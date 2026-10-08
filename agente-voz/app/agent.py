"""Loop del agente: LLM vía FreeLLMAPI (OpenAI-compatible) + tool calling."""
import json
import platform
from datetime import datetime

from openai import OpenAI

import config
import memory
import tools

BASE_SYSTEM_PROMPT = f"""Sos Jarcrow, el asistente de voz y orquestador en español de Frank en Windows.
- Hablá con calidez, naturalidad y voseo rioplatense (ej: "dale", "de una", "te aviso al toque", "¿en qué más te ayudo?").
- Tus respuestas se leen en voz alta por TTS: respondé BREVE, conversacional, sin markdown, sin tablas y sin emojis.

- ORQUESTADOR Y DELEGACIÓN INMEDIATA (REGLA MANDATORIA):
  * Tu rol principal es la conversación por voz en tiempo real. NUNCA te quedes bloqueado ejecutando procesos largos o tareas operativas en la conversación principal.
  * TAREAS A DELEGAR OBLIGATORIAMENTE con `delegate_task(description)`:
    - Manipular o escanear archivos (revisar carpetas, buscar/filtrar archivos, mover, copiar, borrar, organizar).
    - Descargas, procesamiento por lotes o scripts del sistema.
    - Investigaciones web profundas o de múltiples pasos.
    - Tareas de programación o desarrollo de software.
    Para cualquiera de estas solicitudes, DEBÉS llamar a `delegate_task(description)` en tu primer turno.
  * Al delegar con `delegate_task`:
    - Confirmale de inmediato a Frank por voz qué entendiste de lo que pidió.
    - Explicale que ya pusiste a un subagente en segundo plano a resolverlo.
    - Asegurale que le vas a avisar apenas termine.
    - Dejale el micrófono libre preguntándole en qué más lo podés ayudar mientras tanto.
  * `run_command` es EXCLUSIVAMENTE para comandos instantáneos de 1 segundo (abrir un programa con Start-Process, ver batería, etc.). PROHIBIDO usarlo para buscar archivos o tareas de múltiples pasos.

- CONTROL DE SUBAGENTES:
  * Si Frank pregunta cómo van las tareas o qué estás haciendo, usá `list_tasks` para reportar el avance.
  * Si te dice "para la tarea 1", "cancela la tarea 2", usá `cancel_task(task_id)`.
  * Si una tarea falló, usá `retry_task(task_id)`.

- MEMORIA PERMANENTE:
  * Guardá preferencias o datos clave con `remember_fact(key, value)`.
  * Consultá recuerdos pasados con `recall_facts(query)`.

- AGENTES DE CÓDIGO (Claude Code, Codex, Antigravity):
  * Para tareas de desarrollo podés delegar a un subagente o usar `invoke_coding_agent(agent, prompt, directory)`.

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

    def ask(self, user_text: str, max_steps: int = 3, stop_event=None) -> str:
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

            delegated = False
            delegation_info = None

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

                if call.function.name == "delegate_task":
                    delegated = True
                    delegation_info = (args, result)

            if delegated:
                # La tarea ya está corriendo en segundo plano en un subagente.
                # Respondemos de inmediato a Frank por voz confirmando qué se entendió y delegó,
                # para que sepa que está en marcha y pueda seguir conversando sin esperas.
                try:
                    task_desc = delegation_info[0].get("description", user_text)
                    t_id_hint = ""
                    try:
                        res_obj = json.loads(delegation_info[1])
                        t_id_hint = f" (Tarea {res_obj.get('tarea_id', '')})"
                    except Exception:
                        pass

                    self.messages.append({
                        "role": "system",
                        "content": (
                            "INSTRUCCIÓN DE VOZ INMEDIATA: Respondé en UNA sola oración hablada en español rioplatense (voseo): "
                            f"confirmá qué entendiste del pedido '{task_desc}', que ya se lo encargaste a un subagente en segundo plano{t_id_hint}, "
                            "que le avisarás apenas termine, y preguntale en qué más lo podés ayudar mientras tanto."
                        )
                    })
                    res_msg = self.client.chat.completions.create(
                        model=config.MODEL,
                        messages=self.messages,
                    ).choices[0].message
                    final_response = res_msg.content or ""
                except Exception as exc:
                    print(f"Error generando confirmación de delegación: {exc}")
                    final_response = ""

                if not final_response:
                    task_desc = delegation_info[0].get("description", "la tarea")
                    final_response = f"¡Entendido, Frank! Ya puse a un subagente en segundo plano a trabajar en {task_desc}. Te aviso apenas termine; mientras tanto, ¿en qué más te puedo ayudar?"

                break

        if not final_response:
            # Si el modelo ejecutó herramientas pero no emitió texto final, pedirle síntesis explícita
            try:
                self.messages.append({"role": "user", "content": "Con base en lo anterior, dame una respuesta clara y directa en una o dos oraciones."})
                res_msg = self._complete().choices[0].message
                final_response = res_msg.content or ""
            except Exception:
                final_response = ""

        if not final_response:
            final_response = "Completé la consulta con las herramientas. ¿Querés que revise algo más?"

        # Persistir turno de respuesta del asistente en el buffer rotativo
        memory.add_turn("assistant", final_response)
        return final_response


    def reset(self):
        memory.clear_recent_turns()
        self._build_context()
