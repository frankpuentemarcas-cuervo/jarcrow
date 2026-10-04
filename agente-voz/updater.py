"""Auto-actualización desde GitHub: descarga la carpeta app/ del repo y la reemplaza.

Vive en el .exe (no en app/) a propósito: si una actualización viene rota,
el mecanismo para arreglarla sigue funcionando.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import httpx

REPO = "frankpuentemarcas-cuervo/jarcrow"
BRANCH = "master"
VERSION_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/agente-voz/app/version.txt"
ZIP_URL = f"https://codeload.github.com/{REPO}/zip/refs/heads/{BRANCH}"


def parse(version: str) -> tuple:
    return tuple(int(x) for x in version.strip().split("."))


def local_version(app_dir: Path) -> str:
    return (Path(app_dir) / "version.txt").read_text(encoding="utf-8").strip()


def remote_version() -> str:
    r = httpx.get(VERSION_URL, params={"t": int(time.time())}, timeout=10, follow_redirects=True)
    r.raise_for_status()
    return r.text.strip()


def check(app_dir: Path) -> str | None:
    """Devuelve la versión nueva si hay una, si no None."""
    remote = remote_version()
    return remote if parse(remote) > parse(local_version(app_dir)) else None


def apply(app_dir: Path) -> None:
    app_dir = Path(app_dir)
    r = httpx.get(ZIP_URL, timeout=120, follow_redirects=True)
    r.raise_for_status()

    staging = Path(tempfile.mkdtemp(prefix="jarcrow_upd_"))
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        root = z.namelist()[0].split("/")[0]
        prefix = f"{root}/agente-voz/app/"
        for name in z.namelist():
            if name.startswith(prefix) and not name.endswith("/"):
                dest = staging / name[len(prefix):]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(name))

    if not (staging / "version.txt").exists():
        raise RuntimeError("La descarga no contiene app/version.txt")

    backup = app_dir.with_name("app.bak")
    shutil.rmtree(backup, ignore_errors=True)
    if app_dir.exists():
        app_dir.rename(backup)
    shutil.move(str(staging), str(app_dir))


def rollback(app_dir: Path) -> bool:
    """Vuelve a la versión anterior si la nueva no arranca."""
    app_dir = Path(app_dir)
    backup = app_dir.with_name("app.bak")
    if not backup.exists():
        return False
    shutil.rmtree(app_dir, ignore_errors=True)
    backup.rename(app_dir)
    return True


def restart() -> None:
    args = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, *sys.argv]
    subprocess.Popen(args, close_fds=True)
    os._exit(0)
