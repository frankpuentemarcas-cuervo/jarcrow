# Tareas — CDTalleres
*Crea tareas usando la plantilla [[🤖 CrowBot/plantillas/tarea]]*

| ID | Tarea | Prioridad | Estado | Prompt agente |
|---|---|---|---|---|
| CDT-TASK-DOC-001 | Documentación completa del sistema | Media | ⏳ Pendiente | 017 |
| CDT-TASK-020 | Completar red privada interna (T4-T9 del prompt 019) | 🔴 Crítica | ✅ Completada | 020 ✅ |
| CDT-TASK-021 | Fix Grafana — importar dashboards + Locust target | 🔴 Alta | ✅ Completada | 021 ✅ |
| CDT-TASK-022 | Tuning Gunicorn workers (3→5) + MariaDB parámetros | 🔴 Alta | ✅ Completada | 022 ✅ |
| CDT-TASK-023 | Purgar tabWorkflow Action — 2.79M filas / 480MB | 🟡 Alta | ✅ Completada | 023 ✅ |
| CDT-TASK-024 | Stress test 50u con slow query log activo | 🟡 Media | ⏳ Pendiente | 024 ✅ |
| CDT-TASK-025 | Migrar ACC-GLE y MAT-SLE a MariaDB SEQUENCE | 🟡 Media | ✅ Completada | 025 ✅ |
| CDT-TASK-026 | Investigar Solicitud de Pagos error 417 | 🟢 Baja | ⏳ Pendiente | 026 (crear) |
| CDT-TASK-027 | Stress test final 200u — validar mejoras completas | 🟡 Media | ✅ Completada | 027 ✅ |
| CDT-TASK-028 | Purgar tabVersion 27.7M filas + DocType historial consultable | 🔴 Crítica | ✅ Completada | 028 ✅ |
| CDT-TASK-029 | Validación rendimiento post-purgas — stress test 200u final | 🔴 Crítica | ⏳ Pendiente | 029 ✅ |

## Plan de fases

### Fase 1 — Infraestructura base (ejecutar primero)
CDT-TASK-020 → CDT-TASK-021 → CDT-TASK-022

### Fase 2 — Limpieza y optimización
CDT-TASK-023 → CDT-TASK-024

### Fase 3 — Optimización avanzada (opcional / consultar)
CDT-TASK-025 → CDT-TASK-026

### Fase 4 — Validación final
CDT-TASK-027
