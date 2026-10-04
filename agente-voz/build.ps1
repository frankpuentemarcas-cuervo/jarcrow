$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = ".venv\Scripts\python.exe"

# 1) PyInstaller en el venv
uv pip install --python $py -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar dependencias" }

# 2) Empaquetar. app/ va como DATOS (no compilado) para poder actualizarlo sin regenerar el .exe.
#    --windowed: sin consola. onedir: arranque rápido.
& $py -m PyInstaller launcher.py --name Jarcrow --onedir --windowed --noconfirm --clean `
    --add-data "app;app" `
    --exclude-module gui --exclude-module agent --exclude-module tools --exclude-module voice --exclude-module config `
    --collect-all customtkinter `
    --collect-all faster_whisper `
    --collect-all ctranslate2 `
    --collect-all onnxruntime `
    --collect-all tokenizers `
    --collect-all sounddevice `
    --collect-all _sounddevice_data `
    --collect-all edge_tts `
    --collect-all ddgs `
    --collect-submodules pygame `
    --hidden-import _deps
if ($LASTEXITCODE -ne 0) { throw "Falló PyInstaller" }

# 3) Inno Setup (se instala con winget si no está)
$candidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    winget install --id JRSoftware.InnoSetup -e --scope user --accept-package-agreements --accept-source-agreements
    $iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $iscc) { throw "No se encontró ISCC.exe tras instalar Inno Setup" }
}

& $iscc installer.iss
if ($LASTEXITCODE -ne 0) { throw "Falló Inno Setup" }

Write-Host "`nInstalador listo en: $PSScriptRoot\installer\" -ForegroundColor Green
