"""Módulo de subdelegación y gestión de tareas para Jarcrow.

Permite que Jarcrow actúe como cerebro/orquestador principal delegando
trabajo en subagentes en segundo plano sin bloquear la interacción por voz.
Soporta:
- Asignación de ID simple ("tarea 1", "tarea 2")
- Reintentos automáticos si un subagente falla o da timeout
- Cancelación selectiva ("para la tarea 1")
- Consulta y reporte de avance en tiempo real
"""
import threading
import time
from datetime import datetime

from openai import OpenAI

import config
import tools

# Registro global de tareas
_tasks_lock = threading.Lock()
_tasks = {}
_task_counter = 0
_global_notify = None

SUBAGENT_SYSTEM_PROMPT = """Sos un subagente autónomo de Jarcrow ejecutando una tarea en segundo plano para Frank en Windows.
Tu misión es resolver la tarea asignada de principio a fin de manera eficiente, segura y confiable.
- Tenés acceso a herramientas: run_command (PowerShell), web_search, fetch_url e invoke_coding_agent.
- Si la tarea implica manipular o mover archivos:
  * Buscá, filtrá y procesá los archivos usando PowerShell (Get-ChildItem, Move-Item, Copy-Item, etc.).
  * Si la carpeta de destino no existe, creala primero con 'New-Item -ItemType Directory -Force -Path ...'.
- Cuando termines, devolvé un informe CONCISO y CLARO indicando exactamente qué hiciste y cuál fue el resultado (ejemplo: "Se revisó la carpeta X y se movieron 20 archivos a Y.").
- Si encontrás un error, intentá resolverlo de forma alternativa antes de reportar falla."""


class SubTask:
    def __init__(self, task_id: int, description: str, task_type: str = "general"):
        self.task_id = task_id
        self.description = description
        self.task_type = task_type
        self.status = "en_progreso"  # en_progreso | completada | fallida | cancelada
        self.created_at = datetime.now()
        self.finished_at = None
        self.progress_msg = "Iniciando..."
        self.result = ""
        self.error = None
        self.retry_count = 0
        self.max_retries = 2
        self.stop_event = threading.Event()
        self.thread = None

    def cancel(self):
        self.stop_event.set()
        self.status = "cancelada"
        self.progress_msg = "Cancelada por el usuario"
        self.finished_at = datetime.now()

    def as_dict(self):
        return {
            "id": self.task_id,
            "description": self.description,
            "tipo": self.task_type,
            "estado": self.status,
            "avance": self.progress_msg,
            "resultado": self.result[:300] if self.result else "",
            "reintentos": self.retry_count,
        }


def _run_subagent(task: SubTask, on_notify=None):
    client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
    task.status = "en_progreso"
    task.progress_msg = "Ejecutando tarea..."

    messages = [
        {"role": "system", "content": SUBAGENT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Tarea a resolver: {task.description}"},
    ]

    for attempt in range(task.max_retries + 1):
        if task.stop_event.is_set():
            task.status = "cancelada"
            return

        try:
            task.progress_msg = f"Procesando (intento {attempt + 1})..."
            # Loop de resolución del subagente (hasta 6 pasos de herramientas)
            for _ in range(6):
                if task.stop_event.is_set():
                    task.status = "cancelada"
                    return

                res = client.chat.completions.create(
                    model=config.MODEL,
                    messages=messages,
                    tools=getattr(tools, "SUBAGENT_TOOL_SCHEMAS", tools.TOOL_SCHEMAS),
                    timeout=60,
                )
                msg = res.choices[0].message
                calls = msg.tool_calls or []
                messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content or "",
                        **({"tool_calls": [c.model_dump() for c in calls]} if calls else {}),
                    }
                )

                if not calls:
                    task.result = msg.content or "Completada sin texto de salida."
                    break

                for call in calls:
                    if task.stop_event.is_set():
                        task.status = "cancelada"
                        return
                    import json
                    try:
                        args = json.loads(call.function.arguments or "{}")
                    except Exception:
                        args = {}
                    task.progress_msg = f"Ejecutando {call.function.name}..."
                    out = tools.dispatch(call.function.name, args, confirm=None)
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": out})

            if not task.result and not task.stop_event.is_set():
                try:
                    messages.append({
                        "role": "user",
                        "content": "Con base en las herramientas ejecutadas, redactá un resumen claro y directo de lo realizado en una oración."
                    })
                    res_final = client.chat.completions.create(
                        model=config.MODEL,
                        messages=messages,
                        timeout=30,
                    )
                    task.result = res_final.choices[0].message.content or "Completada con éxito."
                except Exception:
                    task.result = "Completada con éxito."

            if not task.stop_event.is_set():
                task.status = "completada"
                task.progress_msg = "Completada con éxito."
                task.finished_at = datetime.now()

                # Guardar resultado en el historial de turnos para que el agente recuerde el resultado
                try:
                    import memory
                    memory.add_turn("system", f"[Subagente Tarea {task.task_id} finalizada]: {task.result}")
                except Exception:
                    pass

                if on_notify:
                    import re
                    summary = task.result.strip()
                    summary_clean = re.sub(r"[*_#`>|]", "", summary).split("\n")[0].strip()
                    if len(summary_clean) > 130:
                        summary_clean = summary_clean[:127] + "..."
                    notify_msg = f"Frank, terminé la tarea {task.task_id}: {summary_clean}"
                    on_notify(notify_msg)
                return

        except Exception as exc:
            task.error = str(exc)
            task.retry_count = attempt + 1
            if attempt < task.max_retries and not task.stop_event.is_set():
                task.progress_msg = f"Reintentando tras error: {exc}"
                time.sleep(2)
                continue
            else:
                task.status = "fallida"
                task.progress_msg = f"Falló tras reintentos: {exc}"
                task.finished_at = datetime.now()
                try:
                    import memory
                    memory.add_turn("system", f"[Subagente Tarea {task.task_id} falló]: {exc}")
                except Exception:
                    pass
                if on_notify:
                    err_clean = str(exc).split("\n")[0][:100]
                    on_notify(f"Frank, la tarea {task.task_id} no pudo completarse: {err_clean}")
                return


def delegate_task(description: str, task_type: str = "general", on_notify=None) -> dict:
    """Crea y arranca un nuevo subagente en segundo plano."""
    global _task_counter
    notify_cb = on_notify or _global_notify
    with _tasks_lock:
        _task_counter += 1
        t_id = _task_counter
        subtask = SubTask(t_id, description, task_type)
        _tasks[t_id] = subtask

    th = threading.Thread(target=_run_subagent, args=(subtask, notify_cb), daemon=True)
    subtask.thread = th
    th.start()
    return {"tarea_id": t_id, "estado": "iniciada", "mensaje": f"Tarea {t_id} asignada a un subagente en segundo plano."}


def list_tasks() -> list[dict]:
    """Lista el estado de todos los subagentes."""
    with _tasks_lock:
        return [t.as_dict() for t in _tasks.values()]


def get_task_status(task_id: int) -> dict:
    """Obtiene el estado detallado de una tarea específica."""
    with _tasks_lock:
        t = _tasks.get(task_id)
        if not t:
            return {"error": f"No se encontró la tarea {task_id}"}
        return t.as_dict()


def cancel_task(task_id: int) -> dict:
    """Cancela una tarea activa."""
    with _tasks_lock:
        t = _tasks.get(task_id)
        if not t:
            return {"error": f"No existe la tarea {task_id}"}
        if t.status != "en_progreso":
            return {"mensaje": f"La tarea {task_id} ya estaba {t.status}."}
        t.cancel()
        return {"mensaje": f"La tarea {task_id} ha sido cancelada."}


def cancel_all_tasks() -> dict:
    """Cancela todas las tareas en progreso."""
    with _tasks_lock:
        cancelled = []
        for t in _tasks.values():
            if t.status == "en_progreso":
                t.cancel()
                cancelled.append(t.task_id)
        return {"mensaje": f"Tareas canceladas: {cancelled}" if cancelled else "No había tareas en progreso."}


def retry_task(task_id: int, on_notify=None) -> dict:
    """Fuerza el reintento de una tarea fallida o cancelada."""
    notify_cb = on_notify or _global_notify
    with _tasks_lock:
        t = _tasks.get(task_id)
        if not t:
            return {"error": f"No existe la tarea {task_id}"}
        subtask = SubTask(t.task_id, t.description, t.task_type)
        _tasks[task_id] = subtask

    th = threading.Thread(target=_run_subagent, args=(subtask, notify_cb), daemon=True)
    subtask.thread = th
    th.start()
    return {"mensaje": f"Reintentando tarea {task_id} con nuevo subagente."}
