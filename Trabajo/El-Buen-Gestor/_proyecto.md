---
nombre: El Buen Gestor
cliente: shalom
categoria: trabajo
estado: activo
stack:
  backend: laravel-11
  frontend: vue3
  database: mysql
  infra: docker
repo: ""
ruta_local: "c:\\dev\\el-buen-gestor"
servidor: ""
dominio: ""
skills_asignados:
  - backend-architect
  - backend-dev-guidelines
  - backend-feature-development
  - ui-ux-designer
  - ui-visual-validator
  - unit-testing
ia_principal: claude-code
fecha_inicio: 2025-01-01
ultima_actividad: 2026-04-25
---

# El Buen Gestor

## Descripción
Sistema de gestión de incidencias y productividad para gestores de Shalom. Monitorea acciones de gestores en ERPNext, genera alertas automáticas, y proporciona dashboard de supervisión.

## Arquitectura
- **Backend**: Laravel 11, API stateless con Bearer tokens (Sanctum)
- **Frontend**: Vue 3 + Vite + Tailwind CSS v4
- **Auth**: Modelo `Gestor` (NO `User`), tabla `gestores`
- **Integración**: `ErpNextService` para comunicación con ERPNext
- **Cron jobs**: Artisan commands que sincronizan datos desde ERPNext
- **URLs**: Frontend → `localhost:4000` | API → `localhost:8000/api`

## Módulos
| Módulo | Estado | Descripción |
|---|---|---|
| M1 - Incidencias | ✅ Activo | Log de acciones por Issue/turno |
| M2 - Detalles | ✅ Activo | Estado de corrección de observaciones |
| M3 - WhatsApp | ⏸️ Diferido | Esperando API modificada del cliente |
| M5 - Pipeline | ✅ Activo | Tracking de aprobación → tarea interna |

## Skills asignados
| Skill | Uso | IA |
|---|---|---|
| backend-architect | Diseño de APIs y servicios Laravel | Claude Code |
| backend-dev-guidelines | Standards de código backend | Claude Code |
| backend-feature-development | Workflow completo de features | Claude Code |
| ui-ux-designer | Diseño de interfaces Vue 3 | Claude Code |
| ui-visual-validator | Validación visual de cambios UI | Claude Code |
| unit-testing | Generación de tests | Claude Code |

## Paleta de colores
| Token | Hex | Uso |
|---|---|---|
| Fog | `#F3EFFF` | Page backgrounds |
| Surface | `#FCFAFF` | Cards, panels, navbar |
| Lavender | `#B19CD9` | Primary buttons, accents |
| Lavender hover | `#9B84C8` | Button hover state |
| Active light | `#EDE7FF` | Active nav links |
| Dark Mauve | `#5E548E` | Headings, main text |
| Muted | `#8878B8` | Secondary text |
| Border | `#E2D9F3` | Dividers, input borders |

## Restricciones importantes
> ⚠️ **No usar `statefulApi()` en `bootstrap/app.php`** — Rompe la auth Bearer token.

> ⚠️ **Auth usa modelo `Gestor`**, NO `User`. Tabla `gestores`.

> ⚠️ **No usar `<style>` scoped** para inputs/buttons — Tailwind v4 Preflight los override. Usar `style` inline o `design-tokens.css`.

> ⚠️ **Google Fonts** deben ir como `<link>` en `index.html`, NO como `@import` en CSS.

> ⚠️ **`departamento` NO válido en Task queries** de ERPNext — Solo en Issue.

> ⚠️ **M3 (WhatsApp)** está diferido hasta que el cliente entregue la API modificada.
