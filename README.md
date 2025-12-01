# GPT-Quick-TTS

A feature-rich Text-to-Speech (TTS) console using OpenAI's GPT TTS API with an interactive Terminal User Interface (TUI). Convert text to speech instantly with customizable speaking styles.

## Features

- 🎨 **Beautiful TUI** - Full-screen terminal interface with color-coded elements
- 🎭 **Speaking Styles** - Toggle many speaking styles (Teaching, Calm, Excited, Narration, Questioning, Warm, Formal, and more)
- ⌨️ **Keyboard Controls** - Quick style toggling with Ctrl+<key> plus voice cycling (Ctrl+V) and streaming toggle (Ctrl+S)
- 📊 **Real-time Status** - Live status updates (Idle / Sending / Playing / Error)
- 📝 **Activity Log** - Timestamped log of all actions
- 🌍 **UTF-8 Support** - Full support for international characters
- 🔊 **Immediate Playback** - Audio plays directly in your terminal
- 🎨 **Color Coded** - Green for active styles, red for inactive, gray for logs

## Architecture (modularized)

- Core package lives in `gpt_quick_tts/`:
  - `config_store.py` – JSON-backed persistence for voice, streaming, API key, and styles
  - `styles.py` – style tokens, keyboard shortcuts, and voice catalogue
  - `tts_client.py` – OpenAI client wrapper with optional streaming playback
  - `audio.py` – pygame-based audio playback helper
  - `controller.py` & `state.py` – orchestration + runtime state for the console
  - `ui/console.py` – prompt_toolkit UI built on the controller/state
- Thin entrypoint `tts_console.py` simply runs the console UI, so other apps can import the controller and reuse it.
- Backwards-compatible shims (`config.py`, `styles.py`, `player.py`, `async_runner.py`, `tts_client.py`) forward to the new package to ease extension.

### Extending / embedding

- Build alternate UIs by importing the controller:  
  `from gpt_quick_tts.controller import ConsoleController`
- Swap audio backends by providing your own `AudioPlayer` implementation to the controller.
- Override config location by instantiating `ConfigStore(path=...)`.
- Add new styles by extending `STYLE_TOKENS`/`STYLE_SHORTCUTS` in `gpt_quick_tts/styles.py`; defaults merge safely into existing configs.

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

1. **Run the TTS Console** (choose one):
   ```bash
   # Preferred: modular entrypoint
   python -m gpt_quick_tts

   # Legacy wrapper (still supported)
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
   - Press `Ctrl+N` to toggle **Narration** (warm, paced)
   - Press `Ctrl+K` to toggle **Questioning** (curious, rising intonation)
   - Press `Ctrl+W` to toggle **Warm** (soft, gentle)
   - Press `Ctrl+F` to toggle **Formal** (precise, neutral)
   - Press `Ctrl+V` to cycle available voices (alloy, ash, ballad, ...)
   - Active styles (shown in **green**) are automatically prepended to your text as control tokens

4. **Enter text to convert to speech**:
   - Type any text at the `TTS>` prompt and press Enter
   - Active style tokens like `[Teaching, Excited]` are automatically added
   - The text is sent to OpenAI's TTS API
   - Audio plays automatically
   - You can enter text in any language (UTF-8 supported)

5. **Quit the application**:
   - Press `Ctrl+Q` or type `:q` and press Enter

## Configuration & persistence

- User preferences are stored in `tts_config.json` in the repo root.
- The `ConfigStore` (in `gpt_quick_tts/config_store.py`) manages loading/saving:
  - `voice` – current voice name
  - `streaming` – boolean toggle for low-latency streaming playback
  - `api_key` – optional persisted OpenAI key (env var `OPENAI_API_KEY` still works)
  - `styles` – map of style name -> enabled
- New styles added in the future are merged automatically so older config files remain valid.

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
| `Ctrl+N`    | Toggle Narration style          |
| `Ctrl+K`    | Toggle Questioning style        |
| `Ctrl+W`    | Toggle Warm style               |
| `Ctrl+F`    | Toggle Formal style             |
| `Ctrl+V`    | Cycle voice personas            |
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

## Architecture (refactor overview)

- `gpt_quick_tts/cli.py` – builds the app (config, OpenAI client, audio, state).
- `gpt_quick_tts/styles.py` – style definitions and helpers.
- `gpt_quick_tts/engine.py` – service layer that talks to OpenAI and plays audio.
- `gpt_quick_tts/state.py` – mutable UI state (logs, status, styles, voice).
- `gpt_quick_tts/ui/app.py` – prompt_toolkit UI wired to the engine/state.
- Legacy modules (`tts_console.py`, `config.py`, `styles.py`, etc.) now forward to the package for backwards compatibility.

## License

This project is available for personal use.

## Credits

Built with:
- [OpenAI API](https://openai.com/api/) - Text-to-Speech service
- [pygame](https://www.pygame.org/) - Audio playback
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) - Terminal UI framework
