"""Sistema de memoria para Jarcrow: buffer rotativo + almacenamiento semántico SQLite."""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import config

DB_PATH = config.CONFIG_DIR / "memory.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa las tablas de hechos y buffer si no existen."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recent_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


# Inicializar base de datos al importar
init_db()


def remember_fact(key: str, value: str) -> str:
    """Guarda o actualiza un dato o preferencia duradera sobre Frank o el entorno."""
    key = key.strip().lower()
    value = value.strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        conn.execute("""
            INSERT INTO facts (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (key, value, now))
        conn.commit()
    return f"Recordado: '{key}' = '{value}'"


def forget_fact(key: str) -> str:
    """Elimina un hecho almacenado."""
    key = key.strip().lower()
    with _get_connection() as conn:
        cur = conn.execute("DELETE FROM facts WHERE key = ?", (key,))
        conn.commit()
        if cur.rowcount > 0:
            return f"He olvidado el dato sobre '{key}'."
        return f"No encontré ningún recuerdo registrado sobre '{key}'."


def recall_facts(query: str = "") -> List[Dict[str, str]]:
    """Busca hechos relevantes por palabra clave o devuelve los más recientes si query está vacío."""
    query = query.strip().lower()
    with _get_connection() as conn:
        if query:
            cur = conn.execute("""
                SELECT key, value FROM facts
                WHERE key LIKE ? OR value LIKE ?
                ORDER BY updated_at DESC LIMIT 6
            """, (f"%{query}%", f"%{query}%"))
        else:
            cur = conn.execute("""
                SELECT key, value FROM facts
                ORDER BY updated_at DESC LIMIT 8
            """)
        return [{"key": row["key"], "value": row["value"]} for row in cur.fetchall()]


def get_memory_prompt_snippet(query: str = "") -> str:
    """Genera un fragmento de texto conciso con los hechos conocidos para inyectar en el System Prompt."""
    facts = recall_facts(query)
    if not facts:
        return ""
    lines = [f"- {f['key']}: {f['value']}" for f in facts]
    return "MEMORIA DE FRANK Y PREFERENCIAS:\n" + "\n".join(lines)


def add_turn(role: str, content: str, max_turns: int = 6):
    """Agrega un turno al buffer rotativo y mantiene el límite."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        conn.execute("""
            INSERT INTO recent_turns (role, content, created_at)
            VALUES (?, ?, ?)
        """, (role, content, now))
        
        # Purgar turnos viejos para mantener el límite rotativo
        conn.execute("""
            DELETE FROM recent_turns
            WHERE id NOT IN (
                SELECT id FROM recent_turns ORDER BY id DESC LIMIT ?
            )
        """, (max_turns,))
        conn.commit()


def get_recent_turns(limit: int = 6) -> List[Dict[str, str]]:
    """Obtiene los últimos turnos en orden cronológico."""
    with _get_connection() as conn:
        cur = conn.execute("""
            SELECT role, content FROM recent_turns
            ORDER BY id ASC LIMIT ?
        """, (limit,))
        return [{"role": row["role"], "content": row["content"]} for row in cur.fetchall()]


def clear_recent_turns():
    """Limpia el buffer de turnos recientes (ej: al reiniciar sesión)."""
    with _get_connection() as conn:
        conn.execute("DELETE FROM recent_turns")
        conn.commit()
