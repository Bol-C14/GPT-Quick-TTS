#!/usr/bin/env python3
"""
TTS Console - A command-line interface for OpenAI Text-to-Speech API.
Reads user input, sends to TTS, and plays audio immediately.
"""

import os
import sys
from datetime import datetime
import pygame
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
import threading
import shutil
import re
from prompt_toolkit.application import get_app
from styles import build_style_prefix, VOICES
from tts_client import TTSClient
from player import AudioPlayer
from config import load_config, save_config

# Styles and voices are defined in `styles.py` and consumed via helpers.


class TTSConsole:
    """TTS Console application for converting text to speech."""
    
    def __init__(self):
        """Initialize the TTS Console."""
        self.tts = None
        self.status = "Initializing"
        self.styles = {
            'Teaching': False,
            'Calm': False,
            'Excited': False,
            'Narration': False,
            'Questioning': False,
            'Warm': False,
            'Formal': False,
        }
        self.log_messages = []
        # Initialize TTS client and audio player
        try:
            self.tts = TTSClient()
        except Exception:
            self.tts = None
        self.player = AudioPlayer()
        self._audio_available = self.player.available()
        self.status = "Idle"
        self.add_log("TTS Console initialized")
        # Load persisted config (voice, streaming, styles)
        cfg = load_config()
        self.voice = cfg.get('voice', 'alloy')
        self.streaming = bool(cfg.get('streaming', False))
        # Merge saved styles into defaults (only for keys that exist)
        saved_styles = cfg.get('styles', {}) or {}
        for k in list(self.styles.keys()):
            if k in saved_styles:
                try:
                    self.styles[k] = bool(saved_styles[k])
                except Exception:
                    pass
    
    def add_log(self, message: str):
        """Add a message to the log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")
        # Keep only last 10 messages
        if len(self.log_messages) > 10:
            self.log_messages.pop(0)
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        # Kept for backward compatibility if needed.
        pass
    
    def _init_audio(self):
        """Initialize pygame mixer for audio playback."""
        try:
            pygame.mixer.init()
        except Exception as e:
            # In headless environments or without audio devices,
            # pygame.mixer.init() may fail. We'll catch this and let
            # the user know when they try to play audio.
            self._audio_available = False
            import warnings
            warnings.warn(f"Audio initialization failed: {e}. Audio playback may not work.")
        else:
            self._audio_available = True
    
    def toggle_style(self, style_name: str):
        """Toggle a style on or off."""
        if style_name in self.styles:
            self.styles[style_name] = not self.styles[style_name]
            state = "ON" if self.styles[style_name] else "OFF"
            self.add_log(f"{style_name} style toggled {state}")
            # persist styles
            try:
                cfg = load_config()
                cfg['styles'] = cfg.get('styles', {})
                cfg['styles'][style_name] = self.styles[style_name]
                save_config(cfg)
            except Exception:
                pass
    
    def get_style_text(self) -> str:
        """Get the style prefix text for TTS input.

        Instead of returning human-readable labels like "[Teaching]",
        return control-style tokens (e.g. <<style:teaching,...>>) which
        are less likely to be spoken by the TTS engine. The UI still
        displays the human-readable state (via `get_header_text`).
        """
        # Build tokens using styles.build_style_prefix
        return build_style_prefix(self.styles)
    
    def text_to_speech(self, text: str, app=None):
        """Convert text to speech and play it."""
        try:
            # Check if audio is available
            if not getattr(self, '_audio_available', True):
                self.status = "Error"
                self.add_log("Error: Audio playback not available")
                self.status = "Idle"
                return
            
            # Prepend style tokens
            full_text = self.get_style_text() + text
            self.add_log(f"Processing: {text[:50]}...")
            if app:
                app.invalidate()

            # Update status to Sending
            self.status = "Sending"
            if app:
                app.invalidate()

            # If streaming mode is enabled, try to use the streaming player
            if self.streaming:
                if not self.tts:
                    raise RuntimeError("TTS client not initialized")
                try:
                    # stream_synthesize_and_play will block until streaming completes,
                    # so this method is expected to be invoked inside a background thread.
                    self.tts.stream_synthesize_and_play(
                        model="gpt-4o-mini-tts",
                        voice=self.voice,
                        input_text=full_text,
                    )
                    # Playback handled inside stream player
                    self.status = "Idle"
                    self.add_log("Streaming playback completed")
                    if app:
                        app.invalidate()
                    return
                except Exception as e:
                    # If streaming fails, fall back to non-streaming synthesis
                    self.add_log(f"Streaming failed, falling back: {e}")
                    if app:
                        app.invalidate()

            # Create TTS request via TTSClient (non-streaming path)
            if not self.tts:
                raise RuntimeError("TTS client not initialized")

            audio_bytes = self.tts.synthesize(
                model="gpt-4o-mini-tts",
                voice=self.voice,
                input_text=full_text,
            )

            # Update status to Playing
            self.status = "Playing"
            self.add_log("Playing audio...")
            if app:
                app.invalidate()

            # Play the audio via AudioPlayer
            if not self.player.available():
                raise RuntimeError("Audio playback not available")

            self.player.play_bytes(audio_bytes)
            
            # Return to Idle
            self.status = "Idle"
            self.add_log("Playback completed")
            if app:
                app.invalidate()
            
        except Exception as e:
            self.status = "Error"
            self.add_log(f"Error: {str(e)}")
            if app:
                app.invalidate()
            self.status = "Idle"
    
    def get_header_text(self):
        """Generate the header text with styles."""
        separator = "=" * 50
        title = "TTS Console - GPT Quick TTS"
        styles_info = "Styles: Ctrl+(Key)"
        voice_info = "Voice: Ctrl+V to cycle"
        
        # Build style toggles with colors (display order)
        style_order = [
            ('Teaching', 'T'), ('Calm', 'C'), ('Excited', 'E'),
            ('Narration', 'N'), ('Questioning', 'Q'), ('Warm', 'W'), ('Formal', 'F'),
        ]
        style_items = []
        for name, key in style_order:
            state = self.styles.get(name, False)
            if state:
                style_items.append(f'<style_on>[{name} ({key}) ON]</style_on>')
            else:
                style_items.append(f'<style_off>[{name} ({key}) OFF]</style_off>')

        # Determine terminal width to wrap style items
        try:
            app = get_app()
            cols = app.output.get_size().columns
        except Exception:
            cols = shutil.get_terminal_size((80, 20)).columns

        # Helper to measure visible length (strip HTML-like tags)
        def visible_len(s: str) -> int:
            return len(re.sub(r'<[^>]+>', '', s))

        # Build lines of style items that don't exceed cols
        lines = []
        cur_line = ''
        cur_len = 0
        sep = ' '
        for item in style_items:
            item_len = visible_len(item)
            add_len = item_len + (1 if cur_line else 0)
            if cur_len + add_len > max(10, cols - 10):
                # push current line
                lines.append(cur_line)
                cur_line = item
                cur_len = item_len
            else:
                if cur_line:
                    cur_line += sep + item
                    cur_len += add_len
                else:
                    cur_line = item
                    cur_len = item_len
        if cur_line:
            lines.append(cur_line)

        styles_block = '\n'.join(lines)
        status_line = f'<status>Status: [{self.status}]</status>'
        voice_line = f'<info>Voice: [{self.voice}] ({len(VOICES)} available) - Ctrl+V to cycle | Streaming: {"ON" if self.streaming else "OFF"} (Ctrl+S)</info>'

        return HTML(
            f'{separator}\n'
            f'<title>{title}</title>\n'
            f'<info>{styles_info}</info>\n'
            f'{styles_block}\n'
            f'{voice_line}\n'
            f'{status_line}\n'
            f'{"-" * 42}\n'
        )
    
    def get_log_text(self):
        """Generate the log text."""
        log_header = "\n<info>Log:</info>"
        if self.log_messages:
            log_lines = '\n'.join([f'<log>{msg}</log>' for msg in self.log_messages])
            return HTML(f'{log_header}\n{log_lines}\n')
        else:
            return HTML(f'{log_header}\n<log>(no messages yet)</log>\n')
    
    def run(self):
        """Run the main console loop with prompt_toolkit TUI."""
        # Define color styles
        style = Style.from_dict({
            'title': '#ffffff bold',
            'info': '#ffffff',
            'style_on': '#00ff00 bold',  # Green for ON
            'style_off': '#ff0000',      # Red for OFF
            'status': '#ffffff',
            'log': '#808080',            # Gray for log
        })
        
        # Create text input area
        text_area = TextArea(
            prompt='TTS> ',
            multiline=False,
            wrap_lines=False,
        )
        
        # Create header window
        header_control = FormattedTextControl(
            text=self.get_header_text,
            focusable=False,
        )
        # Let the header window size itself to the content so lines don't get
        # clipped when wrapping occurs (previously fixed at height=6).
        header_window = Window(
            content=header_control,
            dont_extend_height=True,
        )
        
        # Create log window
        log_control = FormattedTextControl(
            text=self.get_log_text,
            focusable=False,
        )
        log_window = Window(
            content=log_control,
            height=13,
            dont_extend_height=True,
        )
        
        # Create separator window
        separator_control = FormattedTextControl(
            text=HTML('<info>================</info>'),
            focusable=False,
        )
        separator_window = Window(
            content=separator_control,
            height=1,
            dont_extend_height=True,
        )
        
        # Create the layout
        root_container = HSplit([
            header_window,
            log_window,
            separator_window,
            Window(height=1),  # Empty line
            text_area,
        ])
        
        layout = Layout(root_container)
        
        # Create key bindings
        kb = KeyBindings()
        
        @kb.add('c-t')
        def _(event):
            """Toggle Teaching style."""
            self.toggle_style('Teaching')
            event.app.invalidate()
        
        @kb.add('c-c')
        def _(event):
            """Toggle Calm style."""
            self.toggle_style('Calm')
            event.app.invalidate()
        
        @kb.add('c-e')
        def _(event):
            """Toggle Excited style."""
            self.toggle_style('Excited')
            event.app.invalidate()

        @kb.add('c-n')
        def _(event):
            """Toggle Narration style."""
            self.toggle_style('Narration')
            event.app.invalidate()

        @kb.add('c-k')
        def _(event):
            """Toggle Questioning style."""
            self.toggle_style('Questioning')
            event.app.invalidate()

        @kb.add('c-w')
        def _(event):
            """Toggle Warm style."""
            self.toggle_style('Warm')
            event.app.invalidate()

        @kb.add('c-f')
        def _(event):
            """Toggle Formal style."""
            self.toggle_style('Formal')
            event.app.invalidate()
        
        @kb.add('c-q')
        def _(event):
            """Quit the application."""
            event.app.exit()
        
        @kb.add('c-v')
        def _(event):
            """Cycle through available voices."""
            try:
                idx = VOICES.index(self.voice)
                idx = (idx + 1) % len(VOICES)
            except ValueError:
                idx = 0
            self.voice = VOICES[idx]
            self.add_log(f"Voice changed to {self.voice}")
            # persist voice choice
            try:
                cfg = load_config()
                cfg['voice'] = self.voice
                save_config(cfg)
            except Exception:
                pass
            event.app.invalidate()

        @kb.add('c-s')
        def _(event):
            """Toggle streaming (low-latency) mode on/off."""
            self.streaming = not self.streaming
            state = "ON" if self.streaming else "OFF"
            self.add_log(f"Streaming mode toggled {state}")
            # persist streaming mode
            try:
                cfg = load_config()
                cfg['streaming'] = bool(self.streaming)
                save_config(cfg)
            except Exception:
                pass
            event.app.invalidate()
        
        @kb.add('enter')
        def _(event):
            """Process text input."""
            text = text_area.text.strip()
            if text:
                # Clear the input
                text_area.text = ''
                
                # Check for quit command
                if text == ':q':
                    event.app.exit()
                    return
                
                # Process the text in a background thread so the UI
                # (logs/status) can update immediately while TTS runs.
                thread = threading.Thread(
                    target=self.text_to_speech,
                    args=(text, event.app),
                    daemon=True,
                )
                thread.start()
                # Invalidate immediately so the cleared input and any
                # initial log messages are rendered right away.
                event.app.invalidate()
        
        # Create the application
        app = Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=True,
            mouse_support=False,
        )
        
        try:
            # Run the application
            app.run()
        finally:
            # Ensure player is cleaned up
            try:
                self.player.quit()
            except Exception:
                pass
            print("\nGoodbye!")


def main():
    """Main entry point."""
    try:
        console = TTSConsole()
        console.run()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
