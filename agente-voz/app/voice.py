"""Entrada (micrófono con detección de voz + Whisper local) y salida (edge-tts) de voz."""
import asyncio
import collections
import os
import queue
import re
import tempfile

import numpy as np
import sounddevice as sd

import config

_whisper = None
BLOCK_S = 0.05  # 50 ms por bloque de audio

# Frases que Whisper "alucina" con ruido de fondo
_HALLUCINATIONS = ("subtítulos", "amara.org", "gracias por ver", "suscríbete", "gracias por su atención")


def load_whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel

        _whisper = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    return _whisper


def listen_utterance(stop_event, on_level=lambda v: None, silence_s=0.8, max_s=45.0, min_speech_s=0.35):
    """Escucha en continuo y devuelve el audio de UNA frase.
    silence_s=0.8s corta ágilmente al terminar de hablar para respuesta inmediata.
    Devuelve None si se pidió detener.
    """
    sr = config.SAMPLE_RATE
    q: queue.Queue = queue.Queue()

    def callback(indata, frames, time, status):
        q.put(indata[:, 0].copy())

    preroll = collections.deque(maxlen=int(0.4 / BLOCK_S))  # no cortar la primera sílaba
    speech: list = []
    started, silent, voiced, noise = False, 0.0, 0.0, None

    with sd.InputStream(samplerate=sr, channels=1, dtype="float32", blocksize=int(sr * BLOCK_S), callback=callback):
        while not stop_event.is_set():
            try:
                chunk = q.get(timeout=0.2)
            except queue.Empty:
                continue

            rms = float(np.sqrt(np.mean(chunk**2)))
            on_level(min(1.0, rms * 12))
            noise = rms if noise is None else noise
            threshold = max(0.012, noise * 3.0)

            if not started:
                if rms > threshold:
                    started, speech, silent, voiced = True, list(preroll) + [chunk], 0.0, BLOCK_S
                else:
                    noise = 0.95 * noise + 0.05 * rms  # se adapta al ruido ambiente
                    preroll.append(chunk)
                continue

            speech.append(chunk)
            if rms > threshold:
                silent, voiced = 0.0, voiced + BLOCK_S
            else:
                silent += BLOCK_S

            if silent >= silence_s or len(speech) * BLOCK_S >= max_s:
                if voiced >= min_speech_s:
                    on_level(0.0)
                    return np.concatenate(speech)
                started, speech = False, []  # fue un ruido corto, seguir escuchando
                preroll.clear()
    return None


def transcribe(audio: np.ndarray) -> str:
    if audio is None or audio.size < config.SAMPLE_RATE * 0.3:
        return ""
    segments, _ = load_whisper().transcribe(audio, language=config.WHISPER_LANGUAGE, vad_filter=True)
    text = " ".join(s.text.strip() for s in segments).strip()
    if len(text) < 80 and any(h in text.lower() for h in _HALLUCINATIONS):
        return ""
    return text


def _clean_for_speech(text: str) -> str:
    text = re.sub(r"```.*?```", " (te dejé el código en pantalla) ", text, flags=re.S)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[*_#`>|]", "", text)
    return text.strip()


def speak(text: str, stop_event=None) -> None:
    text = _clean_for_speech(text)
    if not text:
        return
    import edge_tts
    import pygame

    path = os.path.join(tempfile.gettempdir(), "jarcrow_tts.mp3")
    asyncio.run(edge_tts.Communicate(text, config.TTS_VOICE, rate=config.TTS_RATE).save(path))

    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    clock = pygame.time.Clock()
    while pygame.mixer.music.get_busy():
        if stop_event is not None and stop_event.is_set():
            pygame.mixer.music.stop()
            break
        clock.tick(20)
    pygame.mixer.music.unload()
