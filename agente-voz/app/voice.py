"""Entrada (micrófono con detección de voz + Whisper local) y salida (edge-tts) de voz."""
import asyncio
import collections
import os
import queue
import re
import tempfile
import threading

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

        # Asignar hilos óptimos para CPU (ej. 4 a 6 hilos según núcleos disponibles)
        cpu_threads = min(6, max(2, (os.cpu_count() or 4) // 2))
        _whisper = WhisperModel(
            config.WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
            cpu_threads=cpu_threads,
            num_workers=1
        )
    return _whisper


def listen_utterance(stop_event, on_level=lambda v: None, silence_s=1.5, max_s=45.0, min_speech_s=0.35, interrupt_event=None):
    """Escucha en continuo y devuelve el audio de UNA frase.
    silence_s=1.5s espera pausas naturales sin cortar prematuramente al usuario.
    Devuelve None si se pidió detener o si llegó una notificación antes de que el usuario hable.
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
            if interrupt_event is not None and interrupt_event.is_set() and not started:
                on_level(0.0)
                return None

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
    # beam_size=1 provee inferencia greedy ultrarrápida manteniendo alta precisión
    segments, _ = load_whisper().transcribe(
        audio,
        language=config.WHISPER_LANGUAGE,
        vad_filter=True,
        beam_size=1
    )
    text = " ".join(s.text.strip() for s in segments).strip()
    if len(text) < 80 and any(h in text.lower() for h in _HALLUCINATIONS):
        return ""
    return text



def _clean_for_speech(text: str) -> str:
    text = re.sub(r"```.*?```", " (te dejé el código en pantalla) ", text, flags=re.S)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[*_#`>|]", "", text)
    return text.strip()


def stop_playback() -> None:
    """Detiene cualquier reproducción de audio en curso de forma inmediata."""
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
    except Exception:
        pass


def is_stop_intent(text: str) -> bool:
    """Determina si un texto representa una orden explícita de detención.
    Distingue rigurosamente la orden imperativa ('¡pará!', 'detente') de la
    preposición 'para' usada en oraciones normales ('para mis archivos', 'para mañana').
    """
    if not text:
        return False
    clean = text.strip().lower()
    clean = re.sub(r"^[¡!¿?,\s]+|[¡!¿?,\s]+$", "", clean)
    clean = re.sub(r"^(hola\s+)?(jar|jarcrow)[\s,.:;!?-]*", "", clean).strip()

    # 1. Órdenes unívocas de detención directa
    explicit_pattern = (
        r"^(detente|deténte|deten|detén|detener|detenerse|cancela todo|cancelar todo|"
        r"detén todo|deten todo|parar todo|para todo|basta|basta ya|alto|silencio|"
        r"cállate|callate|stop)([\s.!?]+(por favor|ya|ahí|ahi))?$"
    )
    if re.match(explicit_pattern, clean, re.I):
        return True

    # 2. Expresiones específicas donde 'para'/'pará' es un verbo imperativo de frenar
    verbal_stops = {
        "para", "pará", "parate", "parate ya", "para ya", "pará ya", "para ahí", "pará ahí",
        "para un poco", "pará un poco", "para de hablar", "pará de hablar",
        "deja de hablar", "dejá de hablar", "corta", "cortá"
    }
    if clean in verbal_stops:
        return True

    # 3. Frases muy cortas (hasta 3 palabras) con una orden imperativa explícita
    words = clean.split()
    if len(words) <= 3:
        if any(w in {"detente", "deténte", "deten", "detén", "basta", "silencio", "stop"} for w in words):
            return True
        if words[0] in {"para", "pará"} and (len(words) == 1 or words[1] in {"ya", "ahí", "ahi", "che", "favor"}):
            return True

    return False


STOP_WORDS_REGEX = re.compile(
    r"\b(detente|deténte|deten|detén|detener|detenerse|pará|parate|alto|silencio|cállate|callate|basta|stop|cancela todo|detén todo)\b",
    re.I
)


def speak(text: str, stop_event=None, on_interrupted=None, enable_barge_in: bool = True) -> bool:
    """Reproduce texto vía edge-tts con soporte de interrupción (Barge-In).
    Si enable_barge_in es True, escucha el micrófono en segundo plano mientras habla.
    Si el usuario dice 'detente', 'para', 'basta', 'stop', etc., corta el audio en el acto.
    Devuelve True si terminó de hablar normalmente, False si fue interrumpido.
    """
    text = _clean_for_speech(text)
    if not text:
        return True
    import edge_tts
    import pygame

    stop_events = stop_event if isinstance(stop_event, (list, tuple)) else ([stop_event] if stop_event else [])

    def is_stopped():
        return any(ev.is_set() for ev in stop_events if ev is not None)

    if is_stopped():
        return False

    path = os.path.join(tempfile.gettempdir(), "jarcrow_tts.mp3")
    try:
        asyncio.run(edge_tts.Communicate(text, config.TTS_VOICE, rate=config.TTS_RATE).save(path))
    except Exception:
        return False

    if is_stopped():
        return False

    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()

    barge_stop = threading.Event()
    was_interrupted = False

    def _barge_in_monitor():
        """Monitorea el micrófono durante la reproducción buscando órdenes de detención."""
        sr = config.SAMPLE_RATE
        q = queue.Queue()

        def _mic_callback(indata, frames, time_info, status):
            q.put(indata[:, 0].copy())

        speech_chunks = []
        started = False
        silent_s = 0.0
        try:
            with sd.InputStream(samplerate=sr, channels=1, dtype="float32", blocksize=int(sr * BLOCK_S), callback=_mic_callback):
                while not barge_stop.is_set() and not is_stopped():
                    try:
                        chunk = q.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    rms = float(np.sqrt(np.mean(chunk**2)))
                    # Umbral para superar el sonido de los parlantes (barge-in intencional)
                    if rms > 0.045:
                        if not started:
                            started = True
                            speech_chunks = [chunk]
                            silent_s = 0.0
                        else:
                            speech_chunks.append(chunk)
                            silent_s = 0.0
                    elif started:
                        speech_chunks.append(chunk)
                        silent_s += BLOCK_S
                        # Si tras hablar hay 0.3s de pausa, transcribir rápido para ver si es 'detente'
                        if silent_s >= 0.3 or len(speech_chunks) * BLOCK_S >= 1.5:
                            audio_arr = np.concatenate(speech_chunks)
                            speech_chunks = []
                            started = False
                            silent_s = 0.0
                            detected = transcribe(audio_arr).strip()
                            if detected and is_stop_intent(detected):
                                barge_stop.set()
                                stop_playback()
                                break
        except Exception:
            pass

    monitor_thread = None
    if enable_barge_in:
        monitor_thread = threading.Thread(target=_barge_in_monitor, daemon=True)
        monitor_thread.start()

    clock = pygame.time.Clock()
    while pygame.mixer.music.get_busy():
        if is_stopped() or barge_stop.is_set():
            pygame.mixer.music.stop()
            was_interrupted = True
            break
        clock.tick(25)

    barge_stop.set()
    if monitor_thread and monitor_thread.is_alive():
        monitor_thread.join(timeout=0.2)

    try:
        pygame.mixer.music.unload()
    except Exception:
        pass

    if was_interrupted and on_interrupted is not None:
        try:
            on_interrupted()
        except Exception:
            pass

    return not was_interrupted



