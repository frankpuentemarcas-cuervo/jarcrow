"""Herramientas que el LLM puede invocar: búsqueda web, leer URL y ejecutar comandos."""
import json
import re
import subprocess

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS

import config

# Pre-aprobados: acceso web y consultas de solo lectura.
_SAFE_START = re.compile(
    r"^\s*(Get-|Test-|Resolve-|Measure-|Select-|Invoke-WebRequest|Invoke-RestMethod|iwr\b|irm\b|curl\b|"
    r"Start-Process\s+['\"]?https?://|start\s+['\"]?https?://|ping\b|nslookup\b|ipconfig\b|whoami\b|hostname\b)",
    re.I,
)
# ...salvo que encadenen algo que modifique el sistema.
_DANGEROUS = re.compile(
    r"(Remove-|Set-|Stop-|New-|Move-|Copy-|Rename-|Out-File|Add-Content|Clear-|Format-Volume|Restart-|"
    r"\bdel\b|\brm\b|\brd\b|\bformat\b|\bshutdown\b|>)",
    re.I,
)


def is_auto_approved(command: str) -> bool:
    return config.AUTO_APPROVE_COMMANDS or (bool(_SAFE_START.match(command)) and not _DANGEROUS.search(command))


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Busca en internet (DuckDuckGo). Usala para noticias, datos actuales o cualquier cosa que no sepas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto a buscar"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Descarga una página web y devuelve su texto plano (recortado).",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Ejecuta un comando de PowerShell en la PC Windows del usuario y devuelve stdout/stderr. "
                "Usalo para abrir programas, consultar el sistema, listar archivos, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Comando PowerShell"},
                    "reason": {"type": "string", "description": "Por qué lo vas a ejecutar"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_task",
            "description": (
                "Delega una tarea a un subagente en segundo plano para no hacer esperar al usuario. "
                "Usalo para investigaciones largas, recopilación de información, descargas o tareas múltiples. "
                "Devuelve el ID numérico asignado (ej: 1, 2) para que puedas informar al usuario."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Descripción clara de la tarea que debe realizar el subagente."},
                    "task_type": {"type": "string", "enum": ["investigacion", "sistema", "general"], "default": "general"},
                },
                "required": ["description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Lista todas las tareas delegadas a subagentes con su estado actual (en_progreso, completada, fallida, cancelada).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_task",
            "description": "Cancela un subagente en segundo plano dado su ID numérico (ej: 1, 2).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "El ID numérico de la tarea a cancelar."},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retry_task",
            "description": "Reintenta una tarea delegada que falló o fue interrumpida.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "El ID numérico de la tarea a reintentar."},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": (
                "Guarda un hecho, preferencia o dato clave sobre Frank o sus proyectos en memoria permanente. "
                "Usalo cuando Frank te diga algo que deba ser recordado a futuro (ej: 'recordá que...', 'mi proyecto es...')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Concepto o tema clave (ej: 'lenguaje_favorito', 'ruta_proyecto')."},
                    "value": {"type": "string", "description": "Detalle concreto a recordar."},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_facts",
            "description": "Busca hechos o recuerdos relevantes en la memoria permanente de Frank usando palabras clave.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Palabra o tema para buscar en la memoria. Dejá vacío para ver los recuerdos recientes."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forget_fact",
            "description": "Olvida o elimina un dato específico guardado en la memoria permanente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "La clave o tema del recuerdo a olvidar."},
                },
                "required": ["key"],
            },
        },
    },
]


def _bing_search(query: str, max_results: int) -> list[dict]:
    resp = httpx.get(
        "https://www.bing.com/search",
        params={"q": query, "setlang": "es"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"},
        timeout=15,
        follow_redirects=True,
    )
    soup = BeautifulSoup(resp.text, "html.parser")
    out = []
    for li in soup.select("li.b_algo")[:max_results]:
        a = li.select_one("h2 a")
        p = li.select_one("p") or li.select_one(".b_caption")
        if a:
            out.append({"title": a.get_text(" ", strip=True), "url": _unwrap_bing(a.get("href", "")), "snippet": p.get_text(" ", strip=True) if p else ""})
    return out


def _unwrap_bing(href: str) -> str:
    """bing.com/ck/a?...&u=a1<base64url> -> URL real."""
    import base64
    from urllib.parse import parse_qs, urlparse

    u = parse_qs(urlparse(href).query).get("u", [""])[0]
    if u.startswith("a1"):
        b64 = u[2:] + "=" * (-len(u[2:]) % 4)
        try:
            return base64.urlsafe_b64decode(b64).decode("utf-8")
        except Exception:
            pass
    return href


def web_search(query: str, max_results: int = 5) -> str:
    try:
        results = _bing_search(query, max_results)
    except Exception:
        results = []
    if not results:
        try:
            results = [
                {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
                for r in DDGS(timeout=8).text(query, max_results=max_results)
            ]
        except Exception:
            results = []
    return json.dumps(results or "Sin resultados", ensure_ascii=False)


def fetch_url(url: str) -> str:
    resp = httpx.get(url, timeout=20, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text[:6000]


def run_command(command: str, reason: str = "", confirm=None) -> str:
    if not is_auto_approved(command):
        approved = confirm(command, reason) if confirm else False
        if not approved:
            return "El usuario RECHAZÓ la ejecución del comando."
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=config.COMMAND_TIMEOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    out = (proc.stdout or "")[-4000:]
    err = (proc.stderr or "")[-2000:]
    return json.dumps({"exit_code": proc.returncode, "stdout": out, "stderr": err}, ensure_ascii=False)


def dispatch(name: str, args: dict, confirm=None) -> str:
    try:
        if name == "web_search":
            return web_search(**args)
        if name == "fetch_url":
            return fetch_url(**args)
        if name == "run_command":
            return run_command(confirm=confirm, **args)
        if name in ("delegate_task", "list_tasks", "cancel_task", "retry_task"):
            import subagents
            func = getattr(subagents, name)
            res = func(**args)
            return json.dumps(res, ensure_ascii=False)
        if name in ("remember_fact", "recall_facts", "forget_fact"):
            import memory
            func = getattr(memory, name)
            res = func(**args)
            return json.dumps(res, ensure_ascii=False) if not isinstance(res, str) else res
        return f"Herramienta desconocida: {name}"
    except Exception as exc:  # el error vuelve al LLM para que se recupere
        return f"ERROR ejecutando {name}: {exc}"
