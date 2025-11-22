#!/usr/bin/env python3
"""
批量提取文件夹内所有视频中“老师（说话最多的人）”的语音片段，
拼接成一个最多 N 分钟（默认 30 分钟）的音频文件。

依赖：
    - ffmpeg (系统层面，需要 `brew install ffmpeg`)
    - pyannote.audio
    - soundfile
    - numpy

新特性（2025-11）：
    - `--device auto|cpu|mps|cuda`：自动选择可用计算设备。
    - `--ffmpeg-workers N`：并行转码，提升 I/O + CPU 利用率。
    - `--num-threads N`：限制/配置 torch 与 BLAS 线程数。
    - 结构化日志，实时输出处理进度。

用法示例：
    export HUGGINGFACE_TOKEN=你的_hf_token
    python batch_extract_teacher.py ./videos --device auto --ffmpeg-workers 4 \
                 --output teacher_30min.wav --minutes 30 --min-seg 0.8
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from typing import Optional
import logging

import numpy as np
import soundfile as sf
from pyannote.audio import Pipeline
import torch
from scipy.spatial.distance import cdist
from speechbrain.pretrained import EncoderClassifier
import io


VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".m4v"}


def configure_logging(level: str) -> int:
    """Configure structured logging once and return numeric level."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    # Keep noisy libs quieter unless user explicitly requests DEBUG
    if numeric_level > logging.DEBUG:
        logging.getLogger("pyannote").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
    return numeric_level


def configure_threads(num_threads: Optional[int]):
    """Limit PyTorch/BLAS threads when requested to reduce contention."""
    if not num_threads:
        return

    num_threads = max(1, num_threads)
    os.environ["OMP_NUM_THREADS"] = str(num_threads)
    os.environ["MKL_NUM_THREADS"] = str(num_threads)
    torch.set_num_threads(num_threads)
    # heuristic: inter-op threads ~ half intra threads but at least 1
    torch.set_num_interop_threads(max(1, num_threads // 2))
    logging.info("Configured torch threads: intra=%d inter-op=%d", num_threads, max(1, num_threads // 2))


def detect_physical_cores() -> int:
    """Detect physical CPU cores (fallback to os.cpu_count)."""
    try:
        if sys.platform == "darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.physicalcpu"], text=True).strip()
            cores = int(out)
            if cores > 0:
                return cores
    except Exception:
        pass
    return max(1, os.cpu_count() or 1)


def resolve_device(requested: str) -> str:
    """Resolve device string based on availability."""
    requested = (requested or "auto").lower()
    mps_available = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())

    if requested == "auto":
        if torch.cuda.is_available():
            return "cuda"
        if mps_available:
            return "mps"
        return "cpu"

    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("Requested CUDA device but torch.cuda.is_available() is False")
        return "cuda"

    if requested == "mps":
        if not mps_available:
            raise RuntimeError("Requested MPS device but torch.backends.mps.is_available() is False")
        return "mps"

    if requested != "cpu":
        raise ValueError(f"Unknown device option: {requested}")
    return "cpu"


def run_ffmpeg_to_wav(input_path: Path, wav_path: Path):
    """
    用 ffmpeg 把任意视频/音频转成 单声道 16kHz 的 wav。
    """
    cmd = [
        "ffmpeg",
        "-y",            # 覆盖输出
        "-i", str(input_path),
        "-ac", "1",      # 单声道
        "-ar", "16000",  # 16kHz
        str(wav_path),
    ]
    logging.info("[ffmpeg] %s -> %s", input_path.name, wav_path.name)
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


def convert_videos_to_wav(video_files, tmp_dir: Path, workers: int):
    """Convert all videos to wav in parallel; return dict {video_path: wav_path}."""
    tmp_dir.mkdir(exist_ok=True)
    jobs = {}
    start = perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for vf in video_files:
            wav_path = tmp_dir / (vf.stem + ".wav")
            jobs[executor.submit(run_ffmpeg_to_wav, vf, wav_path)] = vf

        converted = {}
        for fut in as_completed(jobs):
            src = jobs[fut]
            try:
                converted[src] = fut.result()
                logging.debug("ffmpeg completed: %s", src.name)
            except Exception as exc:
                logging.error("ffmpeg failed for %s: %s", src, exc)

    elapsed = perf_counter() - start
    logging.info("Converted %d file(s) to wav in %.1fs using %d worker(s)", len(converted), elapsed, workers)
    return converted


def diarize_file(pipeline: Pipeline, wav_path: Path, sr_target=16000):
    """
    对一个 wav 文件做说话人分离，返回：
      audio: np.ndarray (mono)
      sr: 采样率
      diarization: pyannote 对象
      speaker_durations: 每个说话人总时长 dict
    """
    start_t = perf_counter()
    audio, sr = sf.read(str(wav_path))
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    if sr != sr_target:
        # 一般不会发生，因为我们 ffmpeg 已经指定了 16kHz
        raise ValueError(f"Unexpected sample rate {sr}, expected {sr_target}")

    logging.info("[diarization] %s", wav_path.name)
    diarization = pipeline(str(wav_path))

    speaker_durations = defaultdict(float)
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        duration = segment.end - segment.start
        speaker_durations[speaker] += duration

    logging.info("  speaker durations (seconds):")
    for spk, dur in speaker_durations.items():
        logging.info("    %s: %.1fs", spk, dur)

    elapsed = perf_counter() - start_t
    logging.info("[diarization-time] %s processed in %.1fs", wav_path.name, elapsed)

    return audio, sr, diarization, speaker_durations


def collect_teacher_segments(
    audio: np.ndarray,
    sr: int,
    diarization,
    speaker_durations,
    target_samples: int,
    collected_samples: int,
    min_seg_seconds: float,
):
    """
    从当前文件中，取“说话最多的 speaker”的语音片段，
    过滤掉过短的片段（< min_seg_seconds），
    返回：新增的 chunks 列表、更新后的 collected_samples。
    如果 target 已达成，则返回空列表。
    """
    if collected_samples >= target_samples:
        return [], collected_samples

    # 选这个文件中说话时间最长的 speaker 作为“老师”
    teacher_speaker = max(speaker_durations, key=speaker_durations.get)
    logging.info("  -> assume teacher in this file: %s", teacher_speaker)

    chunks = []
    min_seg_samples = int(min_seg_seconds * sr)

    for segment, _, speaker in diarization.itertracks(yield_label=True):
        if speaker != teacher_speaker:
            continue

        start = int(segment.start * sr)
        end = int(segment.end * sr)
        seg_len = end - start

        # 过滤掉太短、太碎的片段
        if seg_len < min_seg_samples:
            continue

        # 如果这一段加上去会超过总长度，就截断到刚好 target
        remaining = target_samples - collected_samples
        if remaining <= 0:
            break

        if seg_len > remaining:
            end = start + remaining
            seg_len = end - start

        chunk = audio[start:end]
        if len(chunk) > 0:
            chunks.append(chunk)
            collected_samples += len(chunk)

        if collected_samples >= target_samples:
            break

    return chunks, collected_samples


def norm_vec(x):
    x = np.asarray(x, dtype=np.float32)
    return x / (np.linalg.norm(x) + 1e-8)


def load_speaker_encoder(device: str = "cpu"):
    """Load speechbrain ECAPA encoder on chosen device."""
    try:
        run_device = device if device in ("cpu", "mps", "cuda") else "cpu"
        return EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            run_opts={"device": run_device},
            savedir=".cache/spkrec_ecapa_voxceleb",
        )
    except Exception as e:
        logging.error("Failed to load speaker encoder: %s", e)
        return None


def embedding_from_file(encoder: EncoderClassifier, path_or_buffer):
    emb = None
    try:
        emb = encoder.encode_file(str(path_or_buffer)).squeeze()
    except Exception:
        # try file-like (BytesIO)
        emb = encoder.encode_file(path_or_buffer).squeeze()

    if hasattr(emb, "cpu"):
        emb = emb.detach().cpu().numpy()
    return norm_vec(emb)


def segment_embedding(encoder: EncoderClassifier, audio: np.ndarray, sr: int, start_s: float, end_s: float):
    start = int(start_s * sr)
    end = int(end_s * sr)
    seg = audio[start:end]
    if seg.size == 0:
        return None
    buf = io.BytesIO()
    sf.write(buf, seg, sr, format="WAV")
    buf.seek(0)
    try:
        return embedding_from_file(encoder, buf)
    except Exception as e:
        logging.debug("segment_embedding failed: %s", e)
        return None


def speaker_cluster_centroid(encoder: EncoderClassifier, audio: np.ndarray, sr: int, segments, max_samples_per_cluster=6):
    if not segments:
        return None
    n = min(len(segments), max_samples_per_cluster)
    indices = np.linspace(0, len(segments) - 1, n, dtype=int)
    embs = []
    for i in indices:
        s, e = segments[i]
        emb = segment_embedding(encoder, audio, sr, s, e)
        if emb is not None:
            embs.append(emb)
    if not embs:
        return None
    centroid = np.mean(embs, axis=0)
    return norm_vec(centroid)


def collect_chunks_for_speakers(
    audio: np.ndarray,
    sr: int,
    segments_by_speaker: dict,
    speakers_to_keep: list,
    target_samples: int,
    collected_samples: int,
    min_seg_seconds: float,
):
    chunks = []
    min_seg_samples = int(min_seg_seconds * sr)
    for spk in speakers_to_keep:
        for (start_s, end_s) in segments_by_speaker.get(spk, []):
            start = int(start_s * sr)
            end = int(end_s * sr)
            seg_len = end - start
            if seg_len < min_seg_samples:
                continue

            remaining = target_samples - collected_samples
            if remaining <= 0:
                return chunks, collected_samples

            if seg_len > remaining:
                end = start + remaining
                seg_len = end - start

            chunk = audio[start:end]
            if len(chunk) > 0:
                chunks.append(chunk)
                collected_samples += len(chunk)

            if collected_samples >= target_samples:
                return chunks, collected_samples

    return chunks, collected_samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_dir",
        help="包含一堆视频文件的文件夹路径",
    )
    parser.add_argument(
        "--hf_token",
        help="HuggingFace access token（也可以用环境变量 HUGGINGFACE_TOKEN）",
        default=os.environ.get("HUGGINGFACE_TOKEN", ""),
    )
    parser.add_argument(
        "--output",
        help="输出的老师音频文件名（.wav）",
        default="teacher_30min.wav",
    )
    parser.add_argument(
        "--minutes",
        type=float,
        help="目标总时长（分钟），超过就截断",
        default=30.0,
    )
    parser.add_argument(
        "--min-seg",
        type=float,
        help="单个语音片段的最短时长（秒），短于此将被丢弃，避免太碎",
        default=0.8,
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "mps", "cuda"],
        default="auto",
        help="推理设备；auto 会优先使用 CUDA/MPS。",
    )
    parser.add_argument(
        "--ffmpeg-workers",
        type=int,
        default=None,
        help="并行 ffmpeg worker 数量（默认：物理核心数与 4 取最小）",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=None,
        help="限制 torch/BLAS 线程数，避免 CPU 争用",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.environ.get("BATCH_TTS_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志等级",
    )
    parser.add_argument(
        "--teacher-sample",
        type=str,
        default=None,
        help="老师的示例音频路径（启用基于 embedding 的筛选）",
    )
    parser.add_argument(
        "--sim-threshold",
        type=float,
        default=0.80,
        help="教师 embedding 与簇质心的相似度阈值（0-1），越高越严格",
    )
    parser.add_argument(
        "--min-cluster-duration",
        type=float,
        default=0.0,
        help="仅考虑累计时长大于该值（秒）的簇作为候选（可用于过滤短簇）",
    )
    args = parser.parse_args()

    configure_logging(args.log_level)

    if not args.hf_token:
        raise RuntimeError(
            "未提供 HuggingFace token。请用 --hf_token 或环境变量 HUGGINGFACE_TOKEN。"
        )

    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        raise RuntimeError(f"输入目录不存在或不是文件夹: {input_dir}")

    # 搜索所有视频文件
    video_files = sorted(
        [p for p in input_dir.iterdir() if p.suffix.lower() in VIDEO_EXTS]
    )

    if not video_files:
        logging.warning("在 %s 中没有找到视频文件（支持扩展名: %s）", input_dir, VIDEO_EXTS)
        return

    logging.info("Found %d video file(s)", len(video_files))
    for vf in video_files:
        logging.debug("  - %s", vf.name)

    # 目标总样本数
    sr_target = 16000
    target_samples = int(args.minutes * 60 * sr_target)

    configure_threads(args.num_threads)
    device = resolve_device(args.device)
    logging.info("Using device: %s", device)

    # 加载 diarization pipeline（加载一次，多文件复用）
    logging.info("Loading pyannote pipeline (first run will download weights)...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization",
        use_auth_token=args.hf_token,
    )
    if hasattr(pipeline, "to"):
        pipeline.to(torch.device(device))
    elif device != "cpu":
        logging.warning("Pipeline object has no .to(); falling back to CPU")

    ffmpeg_workers = args.ffmpeg_workers or min(4, detect_physical_cores())
    ffmpeg_workers = max(1, ffmpeg_workers)

    all_chunks = []
    collected_samples = 0

    # 临时 wav 存放目录
    tmp_dir = input_dir / "_tmp_wav"
    wav_map = convert_videos_to_wav(video_files, tmp_dir, ffmpeg_workers)

    try:
        for vf in video_files:
            if collected_samples >= target_samples:
                logging.info("Already reached target duration, stop processing more files.")
                break

            wav_path = wav_map.get(vf)
            if not wav_path:
                logging.warning("Skipping %s because wav conversion failed", vf.name)
                continue

            audio, sr, diarization, speaker_durations = diarize_file(
                pipeline, wav_path, sr_target=sr_target
            )

            # build segments by speaker from diarization
            segments_by_speaker = defaultdict(list)
            for segment, _, speaker in diarization.itertracks(yield_label=True):
                segments_by_speaker[speaker].append((segment.start, segment.end))

            # If teacher sample provided, compute centroids and pick matching clusters
            if args.teacher_sample:
                encoder = load_speaker_encoder(device if device else "cpu")
                if encoder is None:
                    logging.warning("Speaker encoder not available, falling back to duration-based selection")
                    chunks, collected_samples = collect_teacher_segments(
                        audio,
                        sr,
                        diarization,
                        speaker_durations,
                        target_samples,
                        collected_samples,
                        args.min_seg,
                    )
                else:
                    try:
                        teacher_emb = embedding_from_file(encoder, args.teacher_sample)
                    except Exception as e:
                        logging.error("Failed to encode teacher sample: %s", e)
                        teacher_emb = None

                    if teacher_emb is None:
                        logging.warning("Teacher embedding not available, falling back to duration-based selection")
                        chunks, collected_samples = collect_teacher_segments(
                            audio,
                            sr,
                            diarization,
                            speaker_durations,
                            target_samples,
                            collected_samples,
                            args.min_seg,
                        )
                    else:
                        # compute centroids for clusters that exceed min_cluster_duration
                        speaker_centroids = {}
                        for spk, segs in segments_by_speaker.items():
                            total_dur = sum(e - s for s, e in segs)
                            if total_dur < args.min_cluster_duration:
                                continue
                            cent = speaker_cluster_centroid(encoder, audio, sr, segs)
                            if cent is not None:
                                speaker_centroids[spk] = (cent, total_dur)

                        kept_speakers = []
                        for spk, (cent, tot) in speaker_centroids.items():
                            sim = 1 - cdist([teacher_emb], [cent], metric="cosine")[0][0]
                            logging.info("  sim teacher <-> %s: %.3f (cluster dur %.1fs)", spk, sim, tot)
                            if sim >= args.sim_threshold:
                                kept_speakers.append(spk)

                        if not kept_speakers:
                            logging.info("No clusters passed teacher-similarity threshold; falling back to duration-based selection")
                            chunks, collected_samples = collect_teacher_segments(
                                audio,
                                sr,
                                diarization,
                                speaker_durations,
                                target_samples,
                                collected_samples,
                                args.min_seg,
                            )
                        else:
                            chunks, collected_samples = collect_chunks_for_speakers(
                                audio,
                                sr,
                                segments_by_speaker,
                                kept_speakers,
                                target_samples,
                                collected_samples,
                                args.min_seg,
                            )
            else:
                # fallback: pick speaker by duration as before
                chunks, collected_samples = collect_teacher_segments(
                    audio,
                    sr,
                    diarization,
                    speaker_durations,
                    target_samples,
                    collected_samples,
                    args.min_seg,
                )

            logging.info("  collected so far: %.1fs", collected_samples / sr)
            all_chunks.extend(chunks)

        if not all_chunks:
            logging.warning("没有收集到任何老师语音片段，可能录音太短或分离失败。")
            return

        teacher_audio = np.concatenate(all_chunks)
        duration_sec = len(teacher_audio) / sr_target
        logging.info("Final teacher audio duration: %.1f seconds", duration_sec)

        out_path = Path(args.output)
        sf.write(str(out_path), teacher_audio, sr_target)
        logging.info("Written teacher-only audio to %s", out_path.resolve())

    finally:
        # 可选：不想保留临时 wav 的话可以删掉
        # import shutil
        # shutil.rmtree(tmp_dir, ignore_errors=True)
        pass


if __name__ == "__main__":
    main()
