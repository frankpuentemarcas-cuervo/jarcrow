"""Punto de entrada del .exe.

El .exe contiene Python + dependencias + este launcher + updater.
El código de la app (app/) se copia a %LOCALAPPDATA%\\Jarcrow\\app y se carga desde ahí,
así las actualizaciones solo reemplazan esa carpeta sin regenerar el .exe.
"""
import importlib
import os
import shutil
import sys
import traceback
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# Asegurar rutas de Tcl/Tk tanto en entorno virtual como en .exe empaquetado
if not getattr(sys, "frozen", False):
    base_dir = Path(getattr(sys, "base_prefix", sys.prefix))
    tcl_cand = base_dir / "tcl" / "tcl8.6"
    tk_cand = base_dir / "tcl" / "tk8.6"
    if tcl_cand.exists():
        os.environ.setdefault("TCL_LIBRARY", str(tcl_cand))
    if tk_cand.exists():
        os.environ.setdefault("TK_LIBRARY", str(tk_cand))
else:
    int_dir = Path(sys._MEIPASS)
    tcl_cand = int_dir / "_internal" / "tcl" / "tcl8.6"
    tk_cand = int_dir / "_internal" / "tcl" / "tk8.6"
    if not tcl_cand.exists():
        tcl_cand = int_dir / "tcl" / "tcl8.6"
        tk_cand = int_dir / "tcl" / "tk8.6"
    if tcl_cand.exists():
        os.environ.setdefault("TCL_LIBRARY", str(tcl_cand))
    if tk_cand.exists():
        os.environ.setdefault("TK_LIBRARY", str(tk_cand))

FROZEN = getattr(sys, "frozen", False)

if os.environ.get("JARCROW_PACKAGING_ONLY"):  # nunca se ejecuta: le indica a PyInstaller qué empaquetar
    import _deps  # noqa: F401

import updater

if FROZEN:
    DATA_DIR = Path(os.environ["LOCALAPPDATA"]) / "Jarcrow"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Sin consola, stdout/stderr son None y librerías como tqdm explotan: redirigir a log.
    log = open(DATA_DIR / "jarcrow.log", "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = log

    APP_DIR = DATA_DIR / "app"
    bundled = Path(sys._MEIPASS) / "app"
    needs_seed = not (APP_DIR / "version.txt").exists() or updater.parse(
        updater.local_version(bundled)
    ) > updater.parse(updater.local_version(APP_DIR))
    if needs_seed:  # primera instalación o reinstalación con un instalador más nuevo
        shutil.rmtree(APP_DIR, ignore_errors=True)
        shutil.copytree(bundled, APP_DIR)
else:
    APP_DIR = Path(__file__).parent / "app"


def _load_gui():
    sys.path.insert(0, str(APP_DIR))
    return importlib.import_module("gui")


def main():
    try:
        gui = _load_gui()
    except Exception:
        traceback.print_exc()
        # La actualización rompió el arranque: volver a la versión anterior.
        if FROZEN and updater.rollback(APP_DIR):
            updater.restart()
        raise
    gui.main(app_dir=APP_DIR, can_update=FROZEN)


if __name__ == "__main__":
    main()
