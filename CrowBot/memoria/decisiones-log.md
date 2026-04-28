---
tipo: memoria
ultima_actualizacion: 2026-04-25
---

# 📝 Decisiones Log

Registro cronológico de decisiones técnicas, configuraciones elegidas y lecciones aprendidas.

---

## 2026-04-25 — Creación del sistema CrowBot

**Contexto**: Se necesitaba un sistema centralizado para gestionar proyectos, tareas, skills de IA y credenciales.

**Decisión**: Usar Obsidian Vault (Markdown puro) como sistema de gestión, sin depender de la app de Obsidian para funcionar.

**Razones**:
- Markdown es portable y legible sin herramientas especiales
- Git-friendly para versionado
- Extensible con plugins de Obsidian cuando se instale
- Frontmatter YAML permite queries automáticos (Dataview)

**Alternativas descartadas**:
- Notion: Requiere internet, no local-first
- Trello: No soporta prompts ni skills
- Base de datos: Overkill para el uso actual

---

## 2026-04-25 — Stack de IAs definido

**Decisión**: Usar 4 IAs complementarias:
1. **CrowBot (Antigravity/Gemini)** → Orquestación, gestión, infra
2. **Claude Code** → Desarrollo de código con skills
3. **NotebookLM** → Investigación
4. **GitHub Copilot** → Autocompletado inline

**Razón**: Cada IA tiene fortalezas distintas. La matriz de decisión en `catalogo-ias.md` define cuándo usar cada una.

---

## 2026-04-25 — Empresa clarificada

**Hecho**: Overskull es la empresa del usuario. Brinda servicios tecnológicos para Shalom (cliente principal).
- Todos los proyectos actuales son servicios para Shalom
- Dominio principal: `shalom.com.pe`
- Infraestructura en DigitalOcean

---

## 2026-04-25 — Proyecto CDTalleres registrado

**Contexto**: ERPNext de producción con problemas de performance no detectables en logs. Sospecha principal: `tabSeries` (Naming Series) generando locks.

**Decisión**: Crear 3 servidores desde snapshot para separar servicios:
- Backend (164.92.94.47) — Gunicorn workers
- Database (146.190.42.73) — MariaDB
- Frontend (209.38.75.235) — Nginx + assets

**Skills seleccionados** del Frappe Claude Skill Package (61 skills, GitHub: OpenAEC-Foundation):
- `frappe-ops-performance` — Tuning MariaDB, Redis, Gunicorn, profiling
- `frappe-ops-deployment` — Config multi-servidor
- `frappe-agent-debugger` — Debug de errores y logs
- `frappe-core-database` — Operaciones de DB y locks
- `frappe-ops-bench` — Comandos bench
- `frappe-syntax-query-builder` — Análisis de queries

**Razón**: Estos 6 skills cubren el 100% de las necesidades de investigación de performance en Frappe/ERPNext.

**Prompts creados**: 2 prompts en `c:\dev\cdtalleres\`:
1. `prompt-01-verificar-conectividad.md` — Auditoría de los 3 servidores
2. `prompt-02-investigar-frappe-skills.md` — Evaluación y selección de skills del repo

---

## 2026-04-25 — Rediseño de Login Mailcow (Serenity)

**Contexto**: Se requiere actualizar la interfaz de login del servidor de correo corporativo Shalom para mejorar la estética y usar el tema "Serenity" ya diseñado.

**Decisión**: Elaborar un prompt de ejecución para un agente (Claude Code) que realice la implementación técnica directamente en el servidor `167.71.253.104`.

**Prompt creado**: `2026-04-25_001_rediseño-login-serenity.md` en el proyecto Correo Mailcow.

**Razón**: El diseño `login_preview_serenity.html` ya está validado y disponible localmente en `c:\dev\correo-docker\`.

