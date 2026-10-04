import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv, set_key

FROZEN = getattr(sys, "frozen", False)
APP_DIR = Path(__file__).parent
# Instalado: config del usuario en %APPDATA%\Jarcrow (sobrevive a updates/reinstalaciones)
CONFIG_DIR = Path(os.environ["APPDATA"]) / "Jarcrow" if FROZEN else APP_DIR.parent
ENV_PATH = CONFIG_DIR / ".env"

if not ENV_PATH.exists():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(APP_DIR / ".env.example", ENV_PATH)

load_dotenv(ENV_PATH)


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "si"}


BASE_URL = os.getenv("FREELLM_BASE_URL", "http://127.0.0.1:31415/v1")
API_KEY = os.getenv("FREELLM_API_KEY", "")
MODEL = os.getenv("FREELLM_MODEL", "auto")

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "es")
TTS_VOICE = os.getenv("TTS_VOICE", "es-PE-AlexNeural")
TTS_RATE = os.getenv("TTS_RATE", "+10%")

AUTO_APPROVE_COMMANDS = _bool("AUTO_APPROVE_COMMANDS", False)
COMMAND_TIMEOUT = int(os.getenv("COMMAND_TIMEOUT", "60"))
AUTO_UPDATE = _bool("AUTO_UPDATE", True)

SAMPLE_RATE = 16000


def has_api_key() -> bool:
    return bool(API_KEY) and API_KEY != "pega-tu-key-aqui"


def save(key: str, value: str) -> None:
    """Persiste un valor en el .env y lo aplica en caliente."""
    global API_KEY, AUTO_UPDATE
    set_key(str(ENV_PATH), key, value)
    os.environ[key] = value
    if key == "FREELLM_API_KEY":
        API_KEY = value
    elif key == "AUTO_UPDATE":
        AUTO_UPDATE = _bool(key, True)
