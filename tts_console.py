#!/usr/bin/env python3
"""
TTS Console - A command-line interface for OpenAI Text-to-Speech API.
Reads user input, sends to TTS, and plays audio immediately.
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from openai import OpenAI
import pygame
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style


class TTSConsole:
    """TTS Console application for converting text to speech."""
    
    def __init__(self):
        """Initialize the TTS Console."""
        self.client = None
        self.status = "Initializing"
        self.styles = {
            'Teaching': False,
            'Calm': False,
            'Excited': False
        }
        self.log_messages = []
        self._init_openai()
        self._init_audio()
        self.status = "Idle"
        self.add_log("TTS Console initialized")
    
    def add_log(self, message: str):
        """Add a message to the log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")
        # Keep only last 10 messages
        if len(self.log_messages) > 10:
            self.log_messages.pop(0)
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            self.status = "Error"
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please set it with your OpenAI API key."
            )
        self.client = OpenAI(api_key=api_key)
    
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
    
    def get_style_text(self) -> str:
        """Get the style prefix text for TTS input."""
        active_styles = [name for name, active in self.styles.items() if active]
        if active_styles:
            # Prepend style tokens in brackets
            return f"[{', '.join(active_styles)}] "
        return ""
    
    def text_to_speech(self, text: str):
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
            
            # Update status to Sending
            self.status = "Sending"
            
            # Create TTS request
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=full_text
            )
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(
                mode='wb', 
                suffix='.mp3', 
                delete=False
            ) as temp_file:
                temp_filename = temp_file.name
                temp_file.write(response.content)
            
            # Update status to Playing
            self.status = "Playing"
            self.add_log("Playing audio...")
            
            # Play the audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Clean up temporary file
            try:
                Path(temp_filename).unlink()
            except Exception:
                pass  # Ignore cleanup errors
            
            # Return to Idle
            self.status = "Idle"
            self.add_log("Playback completed")
            
        except Exception as e:
            self.status = "Error"
            self.add_log(f"Error: {str(e)}")
            self.status = "Idle"
    
    def get_header_text(self):
        """Generate the header text with styles."""
        separator = "=" * 50
        title = "TTS Console - GPT Quick TTS"
        styles_info = "Styles: Ctrl+(Key)"
        
        # Build style toggles with colors
        style_items = []
        for name, key in [('Teaching', 'T'), ('Calm', 'C'), ('Excited', 'E')]:
            state = self.styles[name]
            if state:
                style_items.append(f'<style_on>[{name} ({key}) ON]</style_on>')
            else:
                style_items.append(f'<style_off>[{name} ({key}) OFF]</style_off>')
        
        styles_line = ' '.join(style_items)
        status_line = f'<status>Status: [{self.status}]</status>'
        
        return HTML(
            f'{separator}\n'
            f'<title>{title}</title>\n'
            f'<info>{styles_info}</info>\n'
            f'{styles_line}\n'
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
        header_window = Window(
            content=header_control,
            height=6,
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
        
        @kb.add('c-q')
        def _(event):
            """Quit the application."""
            event.app.exit()
        
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
                
                # Process the text
                self.text_to_speech(text)
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
            if getattr(self, '_audio_available', True):
                pygame.mixer.quit()
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
