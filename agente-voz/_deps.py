"""Solo para PyInstaller: lista las dependencias que usa app/ para que queden dentro del .exe.

Si una actualización de app/ agrega una librería NUEVA, hay que sumarla acá y regenerar el instalador.
"""
import bs4  # noqa: F401
import customtkinter  # noqa: F401
import ddgs  # noqa: F401
import dotenv  # noqa: F401
import edge_tts  # noqa: F401
import faster_whisper  # noqa: F401
import httpx  # noqa: F401
import numpy  # noqa: F401
import openai  # noqa: F401
import pygame  # noqa: F401
import sounddevice  # noqa: F401
import tkinter  # noqa: F401
import _tkinter  # noqa: F401
