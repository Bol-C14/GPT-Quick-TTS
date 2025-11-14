#!/usr/bin/env python3
"""
TTS Console - A command-line interface for OpenAI Text-to-Speech API.
Reads user input, sends to TTS, and plays audio immediately.
"""

import os
import sys
import tempfile
from pathlib import Path
from openai import OpenAI
import pygame


class TTSConsole:
    """TTS Console application for converting text to speech."""
    
    def __init__(self):
        """Initialize the TTS Console."""
        self.client = None
        self.status = "Initializing"
        self._init_openai()
        self._init_audio()
        self.status = "Idle"
    
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
    
    def update_status(self, status: str):
        """Update and display the current status."""
        self.status = status
        print(f"\r[{self.status}]", end="", flush=True)
    
    def text_to_speech(self, text: str):
        """Convert text to speech and play it."""
        try:
            # Check if audio is available
            if not getattr(self, '_audio_available', True):
                self.update_status("Error")
                print("\nError: Audio playback not available in this environment.")
                self.update_status("Idle")
                print()
                return
            
            # Update status to Sending
            self.update_status("Sending")
            
            # Create TTS request
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
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
            self.update_status("Playing")
            
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
            self.update_status("Idle")
            print()  # New line after status
            
        except Exception as e:
            self.update_status("Error")
            print(f"\nError: {str(e)}")
            self.update_status("Idle")
            print()
    
    def run(self):
        """Run the main console loop."""
        print("=" * 50)
        print("TTS Console - OpenAI Text-to-Speech")
        print("=" * 50)
        print("Enter text to convert to speech (UTF-8 supported)")
        print("Type ':q' to quit")
        print("=" * 50)
        self.update_status("Idle")
        print()
        
        try:
            while True:
                try:
                    # Read input with UTF-8 encoding
                    user_input = input("\n> ").strip()
                    
                    # Check for quit command
                    if user_input == ":q":
                        print("\nGoodbye!")
                        break
                    
                    # Skip empty input
                    if not user_input:
                        continue
                    
                    # Process the text
                    self.text_to_speech(user_input)
                    
                except KeyboardInterrupt:
                    print("\n\nInterrupted. Type ':q' to quit.")
                    self.update_status("Idle")
                    print()
                    continue
                    
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
        finally:
            if getattr(self, '_audio_available', True):
                pygame.mixer.quit()


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
