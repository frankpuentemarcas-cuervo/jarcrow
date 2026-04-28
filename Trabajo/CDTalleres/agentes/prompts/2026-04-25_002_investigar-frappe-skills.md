---
fecha: 2026-04-25
agente_id: "002"
descripcion: investigar-frappe-skills
proyecto: CDTalleres
ia_destino: antigravity
tipo: investigacion
estado: completado
archivo_salida: "c:\\dev\\cdtalleres\\frappe-skills-evaluation.md"
---

# Investigar Skills del Frappe Claude Skill Package para CDTalleres

## Contexto para el agente

Soy parte del equipo de Overskull. Estamos investigando problemas de performance en un ERPNext de producción (proyecto CDTalleres). Necesito que investigues el repositorio de skills de Frappe para Claude y determines cuáles son los más relevantes para nuestro caso de uso.

### Proyecto
- **Nombre**: CDTalleres (ERPNext v15 para Shalom)
- **Stack**: Frappe Framework, MariaDB, Redis, Gunicorn, Nginx
- **Infraestructura**: 3 VPS DigitalOcean (Backend: 164.92.94.47, DB: 165.232.130.222, Frontend: 209.38.75.235)

### Repositorio a investigar
**URL**: https://github.com/OpenAEC-Foundation/Frappe_Claude_Skill_Package

61 skills determinísticos para Frappe Framework / ERPNext v14-v16.

### Problema principal
- Demoras en servidor NO perceptibles en logs estándar
- Sospecha: tabla `tabSeries` genera saturación por `SELECT FOR UPDATE` en alta concurrencia
- Cada documento nuevo lockea una fila de `tabSeries` → contención bajo carga

## Tareas a ejecutar

### 1. Clonar el repositorio
```bash
cd c:\dev\cdtalleres
git clone https://github.com/OpenAEC-Foundation/Frappe_Claude_Skill_Package.git
```

### 2. Leer archivos clave
- `INDEX.md` — Catálogo de 61 skills
- `INSTALL.md` — Instalación
- `USAGE.md` — Uso
- `WAY_OF_WORK.md` — Metodología

### 3. Investigar skills relevantes (en `skills/source/`)

#### Prioridad ALTA (leer completo)
- `skills/source/ops/frappe-ops-performance/`
- `skills/source/agents/frappe-agent-debugger/`
- `skills/source/core/frappe-core-database/`
- `skills/source/ops/frappe-ops-deployment/`

#### Prioridad MEDIA
- `skills/source/ops/frappe-ops-bench/`
- `skills/source/syntax/frappe-syntax-query-builder/`
- `skills/source/core/frappe-core-cache/`

### 4. Buscar menciones específicas
Dentro de los skills, buscar: `tabSeries`, `Naming Series`, `autoname`, `SELECT FOR UPDATE`, row locking, concurrent document creation.

## Archivo de salida

**El agente DEBE guardar resultados en:**
```
c:\dev\cdtalleres\frappe-skills-evaluation.md
```

### Estructura esperada

```markdown
# Evaluación de Frappe Claude Skill Package para CDTalleres

## Tabla resumen de skills relevantes
| Skill | Relevancia | Propósito | Caso de uso CDTalleres |

## Análisis de cada skill
### frappe-ops-performance
- Relevancia / Caso de uso / Técnicas clave / Instalar: Sí|No

## Hallazgos sobre tabSeries y Naming Series

## Plan de instalación
(comandos para instalar solo los skills seleccionados)

## Recomendación — orden de uso para diagnóstico
```
