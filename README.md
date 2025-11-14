# GPT-Quick-TTS

A simple command-line Text-to-Speech (TTS) console using OpenAI's GPT TTS API. Convert text to speech instantly and play it directly from your terminal.

## Features

- 🎯 Interactive command-line interface
- 🌍 UTF-8 support (including Chinese, Japanese, Korean, etc.)
- 🔊 Immediate audio playback (not just file saving)
- 📊 Real-time status display (Idle / Sending / Playing / Error)
- 🚀 Simple and easy to use

## Requirements

- Python 3.7 or higher
- OpenAI API key
- Audio playback capability (pygame)

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Bol-C14/GPT-Quick-TTS.git
   cd GPT-Quick-TTS
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your OpenAI API key**:
   
   You need to set the `OPENAI_API_KEY` environment variable with your OpenAI API key.
   
   - **Linux/MacOS**:
     ```bash
     export OPENAI_API_KEY='your-api-key-here'
     ```
   
   - **Windows (PowerShell)**:
     ```powershell
     $env:OPENAI_API_KEY='your-api-key-here'
     ```
   
   - **Windows (Command Prompt)**:
     ```cmd
     set OPENAI_API_KEY=your-api-key-here
     ```

   > **Note**: For permanent setup, you can add the environment variable to your system's environment variables or shell configuration file (e.g., `.bashrc`, `.zshrc`).

## Usage

1. **Run the TTS Console**:
   ```bash
   python3 tts_console.py
   ```

2. **Enter text to convert to speech**:
   - Type any text and press Enter
   - The text will be sent to OpenAI's TTS API
   - Audio will play automatically
   - You can enter text in any language (UTF-8 supported)

3. **Quit the application**:
   - Type `:q` and press Enter

### Example Session

```
==================================================
TTS Console - OpenAI Text-to-Speech
==================================================
Enter text to convert to speech (UTF-8 supported)
Type ':q' to quit
==================================================
[Idle]

> Hello, world!
[Sending][Playing][Idle]

> 你好，世界！
[Sending][Playing][Idle]

> :q

Goodbye!
```

## Status Indicators

The console displays the current status in square brackets:

- `[Idle]` - Ready to accept input
- `[Sending]` - Sending text to OpenAI TTS API
- `[Playing]` - Playing the generated audio
- `[Error]` - An error occurred (error message will be displayed)

## Troubleshooting

### API Key Issues

If you see an error about the API key:
```
Error: OPENAI_API_KEY environment variable not set.
```
Make sure you've set the environment variable as described in the Setup section.

### Audio Issues

If you experience audio playback problems:
- Ensure your system has audio output capability
- Check that pygame is properly installed: `pip install --upgrade pygame`
- On Linux, you may need to install additional audio libraries:
  ```bash
  sudo apt-get install python3-pygame
  ```

### Network Issues

If requests to the OpenAI API fail:
- Check your internet connection
- Verify your API key is valid and has credit
- Check OpenAI's service status at https://status.openai.com

## License

This project is available for personal use.

## Credits

Built with:
- [OpenAI API](https://openai.com/api/) - Text-to-Speech service
- [pygame](https://www.pygame.org/) - Audio playback
