---
fecha: 2026-04-25
agente_id: "006"
prompt_ref: "prompts/2026-04-25_006_separar-servicios.md"
estado: completado
archivo_fuente: "c:\\dev\\cdtalleres\\separar-servicios-results.md"
---

# Respuesta Agente 006 — Separación de Servicios

## Estado final

| Servidor | IP | Nginx | MariaDB | Supervisor | Redis |
|---|---|---|---|---|---|
| Frontend/App | 209.38.75.235 | ✅ :80/:443 | ❌ apagado | ✅ | ✅ |
| Backend | 164.92.94.47 | ❌ apagado | ❌ apagado | ✅ | ✅ |
| DB | 165.232.130.222 | ❌ apagado | ✅ :3306 | ❌ apagado | ✅ |

## Nota importante

Gunicorn en ambos Frontend y Backend escucha en `127.0.0.1:8000` (loopback, no expuesto externamente). Redis en múltiples puertos (6379, 11000, 12000, 13000) — son las 3 instancias de Frappe (cache, queue, socketio).

Separación completa según arquitectura objetivo. ✅
