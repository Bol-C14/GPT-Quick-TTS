@echo off
REM One-click launcher for GPT-Quick-TTS (Windows Batch)
REM Place this file in the project root and double-click it to run the console UI.

REM Resolve script directory and change to it
SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Optional: uncomment and set your API key here if you don't want to export it globally
REM set OPENAI_API_KEY=your-api-key-here
REM Optional: route requests through an OpenAI-compatible proxy/base URL (example: api.castralhub.com)
REM Note: include the /openai/v1 path so requests map correctly to OpenAI-compatible paths
REM set OPENAI_BASE_URL=https://api.castralhub.com/openai/v1

echo Starting GPT-Quick-TTS in: %SCRIPT_DIR%

REM Prefer the project's venv python when available
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
  "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%tts_console.py"
) else (
  python "%SCRIPT_DIR%tts_console.py"
)

echo.
pause
