---
nombre: Reclutamiento Gamificado
cliente: shalom
categoria: trabajo
estado: activo
stack:
  backend: laravel
  frontend: vue3
  database: mysql
  infra: docker, k8s
repo: ""
ruta_local: "c:\\dev\\reclutamiento-gamificado"
servidor: ""
dominio: ""
skills_asignados:
  - backend-architect
  - backend-feature-development
  - ui-ux-designer
  - ui-ux-pro-max
  - ui-visual-validator
  - unit-testing
ia_principal: claude-code
fecha_inicio: 2025-01-01
ultima_actividad: 2026-04-25
---

# Reclutamiento Gamificado

## Descripción
Plataforma interactiva de reclutamiento gamificado que obtiene cursos y exámenes desde ERPNext y los presenta en una interfaz web atractiva para candidatos/estudiantes.

## Arquitectura
- **Backend**: Laravel API con ERPNext como fuente de datos
- **Frontend**: Vue 3 + Vite + componentes interactivos
- **Database**: MySQL 8.0 (caché local de cursos/exámenes de ERPNext)
- **Integración**: `ERPNextClient.php` (API wrapper)
- **Auth**: HMAC + Bearer tokens
- **Deploy**: Docker Compose (dev) / Kubernetes (prod evaluación)
- **CI/CD**: GitHub Actions

## Módulos funcionales
| Módulo | Estado | Descripción |
|---|---|---|
| Cursos | ✅ Activo | Display de cursos desde ERPNext |
| Exámenes | ✅ Activo | Sistema de evaluación con quiz |
| Progreso | ✅ Activo | Tracking de avance por usuario |
| Gamificación | 🔜 Pendiente | Puntos, leaderboards, badges |
| Route Map | ✅ Activo | Mapa visual de ruta de aprendizaje |

## Skills asignados
| Skill | Uso | IA |
|---|---|---|
| backend-architect | Arquitectura Laravel + ERPNext API | Claude Code |
| backend-feature-development | Desarrollo de features end-to-end | Claude Code |
| ui-ux-designer | Interfaz gamificada Vue 3 | Claude Code |
| ui-ux-pro-max | Búsqueda de estilos y paletas UI | Claude Code |
| ui-visual-validator | QA visual de componentes | Claude Code |
| unit-testing | Tests de controladores y servicios | Claude Code |

## Fases del proyecto
| Fase | Estado | Descripción |
|---|---|---|
| 1. Design Implementation | ✅ Completada | UI Vue + mock APIs |
| 2. Backend Integration | ✅ En curso | ERPNext API real |
| 3. Gamification | 🔜 Pendiente | Puntos, leaderboards |
| 4. Production Hardening | 🔜 Pendiente | Performance, security |

## Issues conocidos (del historial)
- Auto-scroll en Course Map mobile necesita ajuste
- Rutas no se marcan completadas automáticamente (requiere clic extra)
- HMAC_SECRET debe estar en GitHub Actions secrets para deploy
