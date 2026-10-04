# Jarcrow — asistente de voz

Asistente de voz para Windows: lo **activás con un botón**, te escucha, busca en internet si hace falta y te responde hablando. Usa los modelos gratuitos de [FreeLLMAPI](https://freellmapi.co).

## Uso

1. Tené **FreeLLMAPI** abierto (con al menos un proveedor cargado).
2. Instalá `Jarcrow-Setup-x.y.z.exe` y abrí **Jarcrow** desde el escritorio.
3. La primera vez te pide la *Unified API Key* de FreeLLMAPI.
4. **▶ Activar** → hablá → Jarcrow responde. **■ Apagar** para detenerlo.

| Pieza | Tecnología (gratis) |
|---|---|
| Escucha | Whisper `small` local (faster-whisper, CPU) |
| Voz | edge-tts |
| Cerebro | FreeLLMAPI `model=auto` |
| Internet | Bing / DuckDuckGo + lectura de páginas (sin pedir permiso) |
| PC | PowerShell: lectura sin permiso, cambios con confirmación |

## Arquitectura

```
Jarcrow.exe  (Python + dependencias + launcher.py + updater.py)  ← se regenera solo si cambian dependencias
     │
     └─ carga  %LOCALAPPDATA%\Jarcrow\app\   ← código de app/ — se actualiza solo desde GitHub
config: %APPDATA%\Jarcrow\.env
```

## Publicar una actualización

1. Cambiá el código en `app/`.
2. Subí la versión en `app/version.txt` (ej. `1.0.0` → `1.0.1`).
3. `git push` a `main`.

Las instalaciones la descargan al abrir (si "Auto" está activo) o con **Buscar actualizaciones**. Si la versión nueva no arranca, vuelve sola a la anterior.

> ⚠️ Si la actualización agrega una **librería nueva**, sumala a `requirements.txt` y `_deps.py` y generá un instalador nuevo (`build.ps1`).

## Desarrollo

```powershell
.\install.ps1   # crea .venv y descarga Whisper
.\run.ps1       # abre la GUI desde el código
.\build.ps1     # genera installer\Jarcrow-Setup-x.y.z.exe
```
