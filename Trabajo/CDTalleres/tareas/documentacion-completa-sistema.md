---
id: CDT-TASK-DOC-001
titulo: Generar documentación completa del sistema CDTalleres
proyecto: CDTalleres
estado: pendiente
prioridad: alta
tipo: documentacion
fecha_creacion: 2026-04-25
fecha_limite: ""
asignado_a: agente-antigravity
prompt_agente: "agentes/prompts/2026-04-25_017_documentar-sistema-cdtalleres.md"
archivo_salida: "c:\\dev\\cdtalleres\\docs\\documentacion-cdtalleres.md"
---

# Documentación completa del sistema CDTalleres

## Descripción

Generar documentación técnica y funcional exhaustiva del sistema ERPNext CDTalleres. La documentación debe cubrir:

- **DocTypes custom y personalizaciones** — campos, validaciones, flujos
- **Reglas de negocio** — condicionales, validaciones server-side, cálculos automáticos
- **Flujos de trabajo** — Workflows de Frappe, estados, transiciones, permisos por rol
- **Naming Series** — qué DocTypes las usan, formato, y cuáles son candidatas a migración
- **Scripts y automatizaciones** — Client Scripts, Server Scripts, Scheduled Jobs
- **Print Formats** — formatos de impresión custom
- **Permisos y roles** — roles custom, reglas de permisos por DocType
- **Integraciones** — APIs, webhooks, servicios externos
- **Estructura de datos** — tablas importantes, relaciones entre DocTypes
- **Configuración del sitio** — settings críticos del sistema

## Contexto

Sistema ERPNext v14/v15 para gestión de talleres de Shalom (cliente CDTalleres). Stack de 3 servidores (Backend 164.92.94.47, DB 146.190.42.73, Frontend 209.38.75.235). Investigación de performance reveló `tabSeries` como cuello de botella — la documentación ayudará a identificar todos los DocTypes que necesitan optimización y a comprender el sistema para futuras modificaciones sin romper lógica existente.

## Criterio de completitud

- [ ] Todos los DocTypes custom listados con sus campos y validaciones
- [ ] Todos los Workflows documentados con diagrama de estados
- [ ] Todos los Server Scripts y Client Scripts catalogados
- [ ] Tabla de naming series vs DocType completa
- [ ] Permisos por rol documentados para DocTypes críticos
- [ ] Scheduled Jobs listados con frecuencia y función
- [ ] Documento disponible en `c:\dev\cdtalleres\docs\documentacion-cdtalleres.md`

## Dependencias

Ninguna — puede ejecutarse en paralelo con prompts 015/016.

## Notas

- La documentación se genera por introspección directa del sistema vivo (bench console, frappe.get_meta, queries a DB)
- No requiere acceso al código fuente del repo
- Debe ser suficientemente completa para que un desarrollador nuevo entienda el sistema sin preguntar
