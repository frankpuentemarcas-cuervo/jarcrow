---
titulo: "Stress test final 200 usuarios — validar mejoras completas"
proyecto: CDTalleres
categoria: trabajo
prioridad: media
estado: pendiente
automatizable: si
ia_recomendada: crowbot
prompt_preparado: false
fecha_creacion: 2026-04-25
tiempo_estimado: 2h
tags: [stress-test, locust, benchmark, validacion-final]
tags_dependencias: [CDT-TASK-020, CDT-TASK-021, CDT-TASK-022, CDT-TASK-023, CDT-TASK-024]
---

## Descripción
Stress test final equivalente al baseline original (200 usuarios, 15 minutos) para validar todas las mejoras implementadas y documentar el nuevo rendimiento del sistema.

## Contexto
El baseline original (prompt 014) colapso con 96%+ de fallos a 50-70 usuarios concurrentes. Después de las optimizaciones (SEQUENCE naming, red privada, tuning) se espera que el sistema soporte 200 usuarios sin colapso.

## Dependencias
Ejecutar después de completar:
- CDT-TASK-020 (red privada completa)
- CDT-TASK-021 (Grafana funcional)
- CDT-TASK-022 (Gunicorn 5 workers + MariaDB tuning)
- CDT-TASK-023 (tabWorkflow purgado)
- CDT-TASK-024 (slow queries identificadas y resueltas)

## Parámetros del test
- Usuarios: 200 (igual que baseline)
- Ramp-up: 10/s
- Duración: 15 minutos
- Endpoints: POST /Orden de Trabajo 2, POST /Purchase Order, POST /Purchase Invoice
- Monitoreo: Grafana activo durante todo el test

## Métricas a comparar

| Métrica | Baseline (014) | Objetivo | Real |
|---|---|---|---|
| Fail% OT-2 | 96.3% | <5% | - |
| Fail% PO | 95.9% | <5% | - |
| row_lock_time_avg | 14,740ms | 0ms | - |
| Latencia p50 | 120s (timeout) | <5s | - |
| Usuarios soportados | 50-70 | 200 | - |

## Criterios de aceptación
- [ ] Test completa sin colapso generalizado
- [ ] Fail% < 5% en OT-2, PO, PI
- [ ] row_lock_time_avg = 0ms durante todo el test
- [ ] Latencia p50 < 10s
- [ ] Grafana captura métricas completas durante el test
- [ ] Informe comparativo baseline vs final generado

## Prompt preparado
Requiere crear prompt 027.
