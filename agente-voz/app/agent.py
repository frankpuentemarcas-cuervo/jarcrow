"""Loop del agente: LLM vía FreeLLMAPI (OpenAI-compatible) + tool calling."""
import json
import platform
from datetime import datetime

from openai import OpenAI

import config
import tools

SYSTEM_PROMPT = f"""Sos Jarcrow, el asistente de voz y orquestador en español de Frank en Windows.
- Respondé BREVE y conversacional: tus respuestas se leen en voz alta. Sin markdown, sin tablas, sin emojis.
- METODOLOGÍA DE SUBDELEGACIÓN:
  * Sos el cerebro central. Cuando Frank te pida tareas que lleven tiempo (investigaciones, búsquedas amplias, procesos en la máquina o tareas múltiples), NO te quedes bloqueado haciéndolas vos solo de principio a fin.
  * Usá `delegate_task(description)` para encargar la tarea a un subagente en segundo plano.
  * Informale de inmediato a Frank por voz: por ejemplo, "Asigné la tarea 1 a un subagente y te aviso al terminar" o "Estoy en eso con un subagente".
  * Si Frank te pregunta cómo van las tareas, usá `list_tasks` para reportarle el avance de cada una.
  * Si Frank te dice "para la tarea uno", "cancela la tarea dos" o similar, usá `cancel_task(task_id)` y confirmáselo.
  * Si una tarea falló, usá `retry_task(task_id)` para reintentarla.
- Tenés acceso libre a internet: para consultas simples e inmediatas usá `web_search` / `fetch_url`. Para investigaciones largas o pesadas, delegá en un subagente.
- Para acciones locales en la PC usá `run_command` (PowerShell).
- Sistema: {platform.platform()}."""


class Agent:
    def __init__(self, confirm_command):
        self.client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
        self.confirm_command = confirm_command
        self.use_tools = True
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _complete(self):
        kwargs = {"model": config.MODEL, "messages": self.messages}
        if self.use_tools:
            kwargs["tools"] = tools.TOOL_SCHEMAS
        try:
            return self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            # Algunos modelos gratuitos no soportan tools: reintentar sin ellas.
            if self.use_tools and "tool" in str(exc).lower():
                print("[!] El modelo no soporta herramientas, sigo sin ellas.")
                self.use_tools = False
                kwargs.pop("tools", None)
                return self.client.chat.completions.create(**kwargs)
            raise

    def ask(self, user_text: str, max_steps: int = 6, stop_event=None) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.messages.append({"role": "user", "content": f"[{now}] {user_text}"})

        for _ in range(max_steps):
            if stop_event is not None and stop_event.is_set():
                return "Ejecución detenida."

            msg = self._complete().choices[0].message
            calls = msg.tool_calls or []
            self.messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    **({"tool_calls": [c.model_dump() for c in calls]} if calls else {}),
                }
            )
            if not calls:
                return msg.content or ""

            for call in calls:
                if stop_event is not None and stop_event.is_set():
                    return "Ejecución detenida."
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                print(f"  -> {call.function.name}({args})")
                result = tools.dispatch(call.function.name, args, confirm=self.confirm_command)
                self.messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

        return "Me trabé usando herramientas, ¿podés reformular la pregunta?"

    def reset(self):
        self.messages = self.messages[:1]
