$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) { uv venv .venv --python 3.13 }
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "Falló la instalación de dependencias." -ForegroundColor Red; exit 1 }

# Pre-descarga el modelo Whisper (crea .env desde la plantilla si no existe)
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'app'); import voice; voice.load_whisper(); print('Whisper OK')"

Write-Host "Entorno de desarrollo listo. Abrí la app con: .\run.ps1" -ForegroundColor Green
