GPT-Quick-TTS 使用说明（中文）

概述
----
这是 GPT-Quick-TTS 的 Windows 使用手册，包含一键启动、API Key 填写（程序会弹出提示）、快捷键操作、发送文本并自动生成播放语音的操作说明，以及日志与打包说明。

启动方式（推荐）
----
1. 可执行文件（一次性运行）：
   - 双击：
     - 打开：D:\Project\GPT-Quick-TTS\dist\GPT-Quick-TTS\GPT-Quick-TTS.exe
     - 程序会打开终端风格的 TUI（全屏控制台）。

2. 使用仓库里的“二进制启动器”（开发/调试）：
   - 双击 `start_tts.bat`（位于项目根目录）将会：
     - 自动使用项目下的 `.venv`（如果存在）里的 Python
     - 否则尝试使用系统的 `python` 命令
   - 或在 PowerShell 中运行（项目根目录）：
     ```powershell
     .\start_tts.bat
     ```

第一次运行 / 依赖安装（开发环境）
----
如果你从源码运行而不是 exe：
1. 创建并激活虚拟环境（PowerShell）：
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. 之后双击 `start_tts.bat` 或运行 `python tts_console.py` 启动。

API Key 填写（会 prompt）
----
程序需要 `OPENAI_API_KEY` 来调用后端 TTS（或你所使用的代理）。有两种常见方式：
1. 运行时通过提示输入（推荐）：
   - 如果没有设置环境变量，程序会在启动时显示：
     "OpenAI API key not set. Enter your OpenAI API key (leave empty to continue without):"
   - 在提示处粘贴你的 API key 然后回车，程序会把它保存在配置中（`tts_config.json`），并用于当前会话。

2. 通过环境变量（永久或会话）：
   - PowerShell（临时当前会话）：
     ```powershell
     $env:OPENAI_API_KEY = 'sk-...'
     .\start_tts.bat
     ```
   - Windows（永久用户变量，需新开终端）：
     ```powershell
     setx OPENAI_API_KEY "sk-..."
     ```

注意：不要在公开场合粘贴或共享你的 API Key。

默认代理/转发 URL
----
本程序默认将 OpenAI 请求发向内置的代理路径：
`https://api.castralhub.com/openai/v1`
如果需要修改（例如指向官方 OpenAI），请设置环境变量：

```powershell
$env:OPENAI_BASE_URL = 'https://api.openai.com/v1'
setx OPENAI_BASE_URL "https://api.openai.com/v1"
```

快捷键（TUI 内）
----
- Ctrl+T：切换 Teaching（教学）风格
- Ctrl+C：切换 Calm（平和）风格
- Ctrl+E：切换 Excited（兴奋）风格
- Ctrl+N：切换 Narration（旁白）风格
- Ctrl+K：切换 Questioning（疑问）风格
- Ctrl+W：切换 Warm（温暖）风格
- Ctrl+F：切换 Formal（正式）风格
- Ctrl+V：切换/循环不同语音（voice）
- Ctrl+S：切换流式播放（Streaming）模式
- Ctrl+Q：退出（按两次确认，如果有正在进行的播放或流式会要求确认）
- Enter：发送当前行文本进行生成并播放

发送文本并自动生成语音
----
1. 在 TTS> 提示符下输入想要转换为语音的文本，然后回车。
2. 程序会根据当前启用的风格（Style）在文本前添加控制 token，并将文本发送至代理（默认 castralhub）。
3. 如果启用了 Streaming（Ctrl+S），程序会尝试低延迟流式播放；失败时会回退到一次性生成再播放。
4. 播放完成后，状态会回到 Idle。

日志与文本保存
----
- UI 中的“日志”显示最近 20 条消息。
- 为了保留完整的文本（不被 UI 截断），程序会把每次你输入的完整文本与日志一并追加保存到磁盘：
  - 默认日志文件：`tts_console.log`（位于项目根目录）
  - 如需改到自定义位置，请设置环境变量 `TTS_LOG_PATH`，例如：
    ```powershell
    setx TTS_LOG_PATH "C:\Users\你\Documents\gpt_tts.log"
    ```

打包说明（已内置默认代理）
----
我们已提供一个 Windows 一键可运行的打包版本（one-folder）：

 - 打包输出目录：`dist\GPT-Quick-TTS\`，主程序：`GPT-Quick-TTS.exe`

如果你想自行打包或更新打包版本（在开发机上）
```powershell
# 在项目根并激活 .venv 后：
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller --name "GPT-Quick-TTS" --onedir --console tts_console.py
```

注意事项：
- exe 默认内置了 `OPENAI_BASE_URL=https://api.castralhub.com/openai/v1`，如果需要改回官方平台请在系统环境中设置 `OPENAI_BASE_URL` 后再运行 exe。
- 建议分发 `dist\GPT-Quick-TTS` 文件夹（one-folder），不要直接使用 single-file（--onefile）除非你能确认所有动态库与音频依赖都正确包含。

虚拟麦克风（VB-Cable）自动安装（仅 Windows）
----
- 需要联网和管理员权限，安装后通常要重启；随后在声音设置里选择 “CABLE Input/CABLE Output”。
- 一次性安装：`python tts_console.py --install-virtual-mic`（或 `./start_tts.bat --install-virtual-mic`）。
- 启动时自动尝试安装：
  ```powershell
  $env:TTS_AUTO_INSTALL_VIRTUAL_MIC=1   # 可选：TTS_FORCE_VIRTUAL_MIC=1 强制重装
  ./start_tts.bat
  ```
- 驱动下载地址可用 `TTS_VIRTUAL_MIC_URL` 覆盖，默认为官方 VB-Cable ZIP。

故障排查
----
- 若程序启动后立刻退出：检查是否使用了非交互式启动方式或在某些环境下 `input()` 被阻塞。建议直接双击 exe 或在终端手动运行 `start_tts.bat` 来观察提示。
- 音频问题：请确认系统音频工作正常，并已安装 pygame 的依赖（打包版本已包含）。
- 网络/API 问题：确保 `OPENAI_API_KEY` 有效且 `OPENAI_BASE_URL` 指向可用的代理或官方 API。

常用命令快速备忘（Windows PowerShell）
----
创建虚拟环境并安装依赖：
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

设置 API Key（永久）：
```powershell
setx OPENAI_API_KEY "sk-..."
```

运行 exe：
```powershell
& 'D:\Project\GPT-Quick-TTS\dist\GPT-Quick-TTS\GPT-Quick-TTS.exe'
```

联系方式
----
如需我继续打包成 single-file、制作安装程序或将日志上报到某处，请告诉我你的偏好。

谢谢使用 GPT-Quick-TTS！
