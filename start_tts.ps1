#!/usr/bin/env pwsh
# One-click launcher for GPT-Quick-TTS (Windows PowerShell)
# Place this file in the project root and double-click it (or run in PowerShell) to launch the console UI.

param()

# Resolve script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -Path $ScriptDir

# Optional: uncomment and set your API key here if you don't want to export it globally
# $env:OPENAI_API_KEY = 'your-api-key-here'
# Optional: route requests through an OpenAI-compatible proxy/base URL (example: api.castralhub.com)
# Note: include the /openai/v1 path so requests map correctly to OpenAI-compatible paths
# $env:OPENAI_BASE_URL = 'https://api.castralhub.com/openai/v1'

Write-Host "Starting GPT-Quick-TTS in: $ScriptDir"

# Prefer the project's venv python when available
$venvPython = Join-Path $ScriptDir '.venv\Scripts\python.exe'
if (Test-Path $venvPython) {
    & $venvPython (Join-Path $ScriptDir 'tts_console.py')
} else {
    & python (Join-Path $ScriptDir 'tts_console.py')
}

Write-Host
Read-Host -Prompt 'Press ENTER to close this window...'
