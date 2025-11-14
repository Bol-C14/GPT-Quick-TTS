# GPT-Quick-TTS

A feature-rich Text-to-Speech (TTS) console using OpenAI's GPT TTS API with an interactive Terminal User Interface (TUI). Convert text to speech instantly with customizable speaking styles.

## Features

- 🎨 **Beautiful TUI** - Full-screen terminal interface with color-coded elements
- 🎭 **Speaking Styles** - Toggle Teaching, Calm, and Excited styles with keyboard shortcuts
- ⌨️ **Keyboard Controls** - Quick style toggling with Ctrl+T/C/E
- 📊 **Real-time Status** - Live status updates (Idle / Sending / Playing / Error)
- 📝 **Activity Log** - Timestamped log of all actions
- 🌍 **UTF-8 Support** - Full support for international characters
- 🔊 **Immediate Playback** - Audio plays directly in your terminal
- 🎨 **Color Coded** - Green for active styles, red for inactive, gray for logs

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

2. **Using the TUI**:
   
   The interface shows:
   ```
   ==================================================
   TTS Console - GPT Quick TTS
   Styles: Ctrl+(Key)
   [Teaching (T) ON] [Calm (C) OFF] [Excited (E) ON]
   Status: [Idle]
   ------------------------------------------
   
   Log:
   [21:09:15] TTS Console initialized
   [21:09:18] Teaching style toggled ON
   ...
   ================
   
   TTS> _
   ```

3. **Toggle Speaking Styles**:
   - Press `Ctrl+T` to toggle **Teaching** style (explanatory, educational tone)
   - Press `Ctrl+C` to toggle **Calm** style (relaxed, soothing tone)
   - Press `Ctrl+E` to toggle **Excited** style (enthusiastic, energetic tone)
   - Active styles (shown in **green**) are automatically prepended to your text

4. **Enter text to convert to speech**:
   - Type any text at the `TTS>` prompt and press Enter
   - Active style tokens like `[Teaching, Excited]` are automatically added
   - The text is sent to OpenAI's TTS API
   - Audio plays automatically
   - You can enter text in any language (UTF-8 supported)

5. **Quit the application**:
   - Press `Ctrl+Q` or type `:q` and press Enter

### Example Session

```
==================================================
TTS Console - GPT Quick TTS
Styles: Ctrl+(Key)
[Teaching (T) OFF] [Calm (C) OFF] [Excited (E) OFF]
Status: [Idle]
------------------------------------------

Log:
[21:09:15] TTS Console initialized

================

TTS> Hello, world!
[Sending][Playing][Idle]

TTS> (Press Ctrl+T to enable Teaching style)
[21:09:20] Teaching style toggled ON

TTS> Python is a great programming language
[Sending - with style: "[Teaching] Python is a great programming language"]
[Playing][Idle]

TTS> :q

Goodbye!
```

## Keyboard Controls

| Key         | Action                          |
|-------------|---------------------------------|
| `Ctrl+T`    | Toggle Teaching style           |
| `Ctrl+C`    | Toggle Calm style               |
| `Ctrl+E`    | Toggle Excited style            |
| `Ctrl+Q`    | Quit the application            |
| `Enter`     | Send text to TTS                |
| `:q`        | Alternative quit command        |

## Color Scheme

The TUI uses colors to provide visual feedback:
- **Green (Bold)** - Active styles (ON)
- **Red** - Inactive styles (OFF)
- **White** - Status information and titles
- **Gray** - Log messages with timestamps

## Status Indicators

The console displays the current status at the top of the interface:

- `[Idle]` - Ready to accept input
- `[Sending]` - Sending text to OpenAI TTS API
- `[Playing]` - Playing the generated audio
- `[Error]` - An error occurred (details shown in log)

## Activity Log

The log section shows timestamped messages about:
- Style toggle events
- Text processing status
- Playback status
- Error messages

The log automatically keeps the last 10 messages to maintain a clean interface.

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
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) - Terminal UI framework
