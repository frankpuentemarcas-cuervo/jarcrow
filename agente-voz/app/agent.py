"""Loop del agente: LLM vía FreeLLMAPI (OpenAI-compatible) + tool calling."""
import json
import platform
from datetime import datetime

from openai import OpenAI

import config
import memory
import tools

BASE_SYSTEM_PROMPT = f"""Sos Jarcrow, el asistente de voz y orquestador en español de Frank en Windows.
- Respondé BREVE y conversacional: tus respuestas se leen en voz alta. Sin markdown, sin tablas, sin emojis.
- METODOLOGÍA DE SUBDELEGACIÓN:
  * Sos el cerebro central. Cuando Frank te pida tareas que lleven tiempo (investigaciones, búsquedas amplias, procesos en la máquina o tareas múltiples), NO te quedes bloqueado haciéndolas vos solo de principio a fin.
  * Usá `delegate_task(description)` para encargar la tarea a un subagente en segundo plano.
  * Informale de inmediato a Frank por voz: por ejemplo, "Asigné la tarea 1 a un subagente y te aviso al terminar" o "Estoy en eso con un subagente".
  * Si Frank te pregunta cómo van las tareas, usá `list_tasks` para reportarle el avance de cada una.
  * Si Frank te dice "para la tarea uno", "cancela la tarea dos" o similar, usá `cancel_task(task_id)` y confirmáselo.
  * Si una tarea falló, usá `retry_task(task_id)` para reintentarla.
- MEMORIA Y PREFERENCIAS:
  * Tenés memoria permanente: si Frank te dice que recuerdes un dato clave, una preferencia o una ruta, usá `remember_fact(key, value)`.
  * Si te pregunta qué recordás o sobre algún tema del pasado, usá `recall_facts(query)`.
- Tenés acceso libre a internet: para consultas simples e inmediatas usá `web_search` / `fetch_url`. Para investigaciones largas o pesadas, delegá en un subagente.
- Para acciones locales en la PC usá `run_command` (PowerShell).
- Sistema: {platform.platform()}."""


class Agent:
    def __init__(self, confirm_command):
        self.client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
        self.confirm_command = confirm_command
        self.use_tools = True
        self.messages = []
        self._build_context()

    def _build_context(self, user_query: str = ""):
        """Construye el contexto del modelo: System Prompt + Hechos relevantes + Buffer rotativo (máx 6 turnos)."""
        sys_prompt = BASE_SYSTEM_PROMPT
        memory_snippet = memory.get_memory_prompt_snippet(user_query)
        if memory_snippet:
            sys_prompt += f"\n\n{memory_snippet}"

        new_messages = [{"role": "system", "content": sys_prompt}]
        # Inyectar buffer rotativo de turnos previos guardados en SQLite
        for turn in memory.get_recent_turns(limit=6):
            new_messages.append({"role": turn["role"], "content": turn["content"]})
        self.messages = new_messages

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
        formatted_user = f"[{now}] {user_text}"
        
        # Reconstruir contexto inyectando hechos relevantes según la consulta
        self._build_context(user_query=user_text)
        self.messages.append({"role": "user", "content": formatted_user})
        # Persistir turno de usuario en el buffer rotativo
        memory.add_turn("user", formatted_user)

        final_response = ""
        for _ in range(max_steps):
            if stop_event is not None and stop_event.is_set():
                final_response = "Ejecución detenida."
                break

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
                final_response = msg.content or ""
                break

            for call in calls:
                if stop_event is not None and stop_event.is_set():
                    final_response = "Ejecución detenida."
                    break
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                print(f"  -> {call.function.name}({args})")
                result = tools.dispatch(call.function.name, args, confirm=self.confirm_command)
                self.messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

        if not final_response:
            final_response = "Me trabé usando herramientas, ¿podés reformular la pregunta?"

        # Persistir turno de respuesta del asistente en el buffer rotativo
        memory.add_turn("assistant", final_response)
        return final_response

    def reset(self):
        memory.clear_recent_turns()
        self._build_context()
