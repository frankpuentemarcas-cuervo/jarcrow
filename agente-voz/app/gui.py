"""Interfaz de Jarcrow: un botón para activar/apagar el agente de voz."""
import math
import queue
import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

import config
import updater
import voice
from agent import Agent

BG = "#0F1117"
CARD = "#171A23"
MUTED = "#8B93A7"
TEXT = "#E8EAF0"

STATES = {
    # estado: (color, texto)
    "off": ("#3A3F4B", "Apagado"),
    "loading": ("#F5A524", "Preparando..."),
    "listening": ("#22C55E", "Te escucho..."),
    "thinking": ("#7C5CFF", "Pensando..."),
    "speaking": ("#38BDF8", "Hablando..."),
}


class JarcrowApp(ctk.CTk):
    def __init__(self, app_dir, can_update: bool):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("Jarcrow")
        self.geometry("400x620")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        self.app_dir = app_dir
        self.can_update = can_update
        self.events: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.agent: Agent | None = None
        self.agent_state = "off"
        self.level = 0.0  # nivel de micrófono 0..1 (lo escribe el hilo de audio)
        self.shown_level = 0.0
        self.phase = 0.0

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(33, self._animate)
        self.after(50, self._drain_events)
        if self.can_update and config.AUTO_UPDATE:
            self.after(1500, lambda: self.check_updates(silent=True))

    # ---------- UI ----------
    def _build(self):
        ctk.CTkLabel(self, text="Jarcrow", font=ctk.CTkFont(size=30, weight="bold"), text_color=TEXT).pack(pady=(28, 0))
        ctk.CTkLabel(self, text="Tu asistente de voz", font=ctk.CTkFont(size=14), text_color=MUTED).pack()

        self.canvas = tk.Canvas(self, width=240, height=240, bg=BG, highlightthickness=0)
        self.canvas.pack(pady=(18, 4))

        self.status = ctk.CTkLabel(self, text="Apagado", font=ctk.CTkFont(size=16), text_color=MUTED)
        self.status.pack()

        self.button = ctk.CTkButton(
            self,
            text="▶  Activar",
            width=230,
            height=58,
            corner_radius=29,
            font=ctk.CTkFont(size=19, weight="bold"),
            fg_color="#22C55E",
            hover_color="#16A34A",
            command=self.toggle,
        )
        self.button.pack(pady=(18, 16))

        self.transcript = ctk.CTkTextbox(
            self, width=350, height=110, fg_color=CARD, text_color=TEXT, corner_radius=14, wrap="word",
            font=ctk.CTkFont(size=13),
        )
        self.transcript.pack()
        self.transcript.configure(state="disabled")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=14)
        version = updater.local_version(self.app_dir)
        ctk.CTkLabel(footer, text=f"v{version}", text_color=MUTED, font=ctk.CTkFont(size=12)).pack(side="left")
        self.update_btn = ctk.CTkButton(
            footer, text="Buscar actualizaciones", width=160, height=28, corner_radius=14,
            fg_color=CARD, hover_color="#232838", text_color=TEXT, font=ctk.CTkFont(size=12),
            command=self.check_updates,
        )
        self.update_btn.pack(side="right")
        self.auto_var = ctk.BooleanVar(value=config.AUTO_UPDATE)
        ctk.CTkSwitch(
            footer, text="Auto", variable=self.auto_var, width=40, font=ctk.CTkFont(size=12), text_color=MUTED,
            command=lambda: config.save("AUTO_UPDATE", "true" if self.auto_var.get() else "false"),
        ).pack(side="right", padx=8)

    def _animate(self):
        self.phase += 0.08
        target = self.level if self.agent_state == "listening" else 0.0
        if self.agent_state == "speaking":
            target = 0.35 + 0.25 * abs(math.sin(self.phase * 2.3))
        self.shown_level += (target - self.shown_level) * 0.25

        color = STATES[self.agent_state][0]
        breathe = 0.0 if self.agent_state == "off" else 4 * math.sin(self.phase)
        c, base = 120, 62
        self.canvas.delete("all")
        for i, alpha in enumerate((0.10, 0.18, 0.30)):  # halos
            r = base + 34 - i * 10 + self.shown_level * 40 + breathe
            self.canvas.create_oval(c - r, c - r, c + r, c + r, fill=_blend(color, BG, alpha), outline="")
        r = base + self.shown_level * 14
        self.canvas.create_oval(c - r, c - r, c + r, c + r, fill=color, outline="")
        if self.agent_state == "thinking":  # arco giratorio
            start = (self.phase * 180) % 360
            self.canvas.create_arc(c - 80, c - 80, c + 80, c + 80, start=start, extent=90, style="arc",
                                   outline="#C4B5FD", width=4)
        self.after(33, self._animate)

    def _set_state(self, state: str, text: str | None = None):
        self.agent_state = state
        self.status.configure(text=text or STATES[state][1], text_color=TEXT if state != "off" else MUTED)

    def _log(self, who: str, text: str):
        self.transcript.configure(state="normal")
        self.transcript.insert("end", f"{who}: {text}\n\n")
        self.transcript.see("end")
        self.transcript.configure(state="disabled")

    # ---------- Comunicación con el hilo del agente ----------
    def post(self, kind: str, *payload):
        self.events.put((kind, payload))

    def _drain_events(self):
        while not self.events.empty():
            kind, payload = self.events.get()
            if kind == "state":
                self._set_state(*payload)
            elif kind == "log":
                self._log(*payload)
            elif kind == "error":
                self._log("⚠️", payload[0])
            elif kind == "stopped":
                self._on_stopped()
            elif kind == "confirm":
                command, reason, holder, done = payload
                msg = f"Jarcrow quiere ejecutar en tu PC:\n\n{command}"
                if reason:
                    msg += f"\n\nMotivo: {reason}"
                holder.append(messagebox.askyesno("Confirmar comando", msg, parent=self))
                done.set()
            elif kind == "update":
                self._on_update_result(*payload)
        self.after(50, self._drain_events)

    def confirm_command(self, command: str, reason: str) -> bool:
        """Lo llama el hilo del agente; la ventana de diálogo se muestra en el hilo de la UI."""
        holder, done = [], threading.Event()
        self.post("confirm", command, reason, holder, done)
        done.wait()
        return holder[0]

    # ---------- Activar / apagar ----------
    def toggle(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.button.configure(state="disabled", text="Apagando...")
            return
        if not config.has_api_key() and not self._ask_api_key():
            return
        self.stop_event.clear()
        self.button.configure(text="■  Apagar", fg_color="#EF4444", hover_color="#DC2626")
        self.worker = threading.Thread(target=self._run_agent, daemon=True)
        self.worker.start()

    def _on_stopped(self):
        self._set_state("off")
        self.level = 0.0
        self.button.configure(state="normal", text="▶  Activar", fg_color="#22C55E", hover_color="#16A34A")

    def _ask_api_key(self) -> bool:
        dialog = ctk.CTkInputDialog(
            title="Configurar Jarcrow",
            text="Pegá la 'Unified API Key' del dashboard de FreeLLMAPI:",
        )
        key = (dialog.get_input() or "").strip()
        if not key:
            return False
        config.save("FREELLM_API_KEY", key)
        return True

    def _set_level(self, value: float):
        self.level = value

    def _run_agent(self):
        try:
            self.post("state", "loading", "Cargando modelo de voz...\n(la primera vez tarda unos minutos)")
            voice.load_whisper()
            if self.agent is None:
                self.agent = Agent(self.confirm_command)

            while not self.stop_event.is_set():
                self.post("state", "listening")
                audio = voice.listen_utterance(self.stop_event, self._set_level)
                if audio is None:
                    break
                self.post("state", "thinking", "Entendiendo...")
                text = voice.transcribe(audio)
                if not text:
                    continue
                self.post("log", "Vos", text)
                self.post("state", "thinking")
                try:
                    answer = self.agent.ask(text)
                except Exception as exc:
                    self.post("error", f"No pude conectar con FreeLLMAPI: {exc}")
                    continue
                if self.stop_event.is_set():
                    break
                self.post("log", "Jarcrow", answer)
                self.post("state", "speaking")
                try:
                    voice.speak(answer, self.stop_event)
                except Exception as exc:
                    self.post("error", f"No pude hablar: {exc}")
        except Exception as exc:
            self.post("error", str(exc))
        finally:
            self.post("stopped")

    # ---------- Actualizaciones ----------
    def check_updates(self, silent: bool = False):
        if not self.can_update:
            if not silent:
                messagebox.showinfo("Actualizaciones", "Modo desarrollo: actualizá con 'git pull'.", parent=self)
            return
        self.update_btn.configure(state="disabled", text="Buscando...")

        def work():
            try:
                self.post("update", updater.check(self.app_dir), None, silent)
            except Exception as exc:
                self.post("update", None, str(exc), silent)

        threading.Thread(target=work, daemon=True).start()

    def _on_update_result(self, new_version, error, silent):
        self.update_btn.configure(state="normal", text="Buscar actualizaciones")
        if error:
            if not silent:
                messagebox.showerror("Actualizaciones", f"No pude buscar actualizaciones:\n{error}", parent=self)
            return
        if not new_version:
            if not silent:
                messagebox.showinfo("Actualizaciones", "Ya tenés la última versión. ✅", parent=self)
            return
        busy = self.worker and self.worker.is_alive()
        auto = silent and config.AUTO_UPDATE and not busy
        if auto or messagebox.askyesno(
            "Actualización disponible", f"Hay una versión nueva ({new_version}).\n¿Actualizar ahora?", parent=self
        ):
            self._apply_update()

    def _apply_update(self):
        self.stop_event.set()
        self.update_btn.configure(state="disabled", text="Actualizando...")
        self.button.configure(state="disabled")

        def work():
            try:
                updater.apply(self.app_dir)
                updater.restart()
            except Exception as exc:
                self.post("update", None, f"Falló la actualización: {exc}", False)

        threading.Thread(target=work, daemon=True).start()

    def _on_close(self):
        self.stop_event.set()
        self.destroy()


def _blend(hex_a: str, hex_b: str, t: float) -> str:
    """Mezcla dos colores: t=1 -> a, t=0 -> b (tkinter no soporta transparencia)."""
    a = [int(hex_a[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * t + y * (1 - t)):02x}" for x, y in zip(a, b))


def main(app_dir, can_update: bool = False):
    JarcrowApp(app_dir, can_update).mainloop()
