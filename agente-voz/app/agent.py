"""Loop del agente: LLM vía FreeLLMAPI (OpenAI-compatible) + tool calling."""
import json
import platform
from datetime import datetime

from openai import OpenAI

import config
import tools

SYSTEM_PROMPT = f"""Sos Jarcrow, un asistente de voz en español que corre en la PC Windows de Frank.
- Respondé BREVE y conversacional: tus respuestas se leen en voz alta. Sin markdown, sin tablas, sin emojis.
- Tenés acceso libre a internet: para CUALQUIER dato actual usá web_search y, si hace falta, fetch_url. NO pidas permiso para buscar.
- Para internet NUNCA uses run_command; usá siempre web_search / fetch_url.
- Usá run_command (PowerShell) solo para acciones en la PC. Nunca ejecutes comandos destructivos sin que te lo pidan explícitamente.
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

    def ask(self, user_text: str, max_steps: int = 6) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.messages.append({"role": "user", "content": f"[{now}] {user_text}"})

        for _ in range(max_steps):
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
