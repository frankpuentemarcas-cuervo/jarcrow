---
titulo: "Stress test 50u con slow query log — identificar queries lentas"
proyecto: CDTalleres
categoria: trabajo
prioridad: media
estado: pendiente
automatizable: si
ia_recomendada: crowbot
prompt_preparado: false
fecha_creacion: 2026-04-25
tiempo_estimado: 2h
tags: [stress-test, locust, slow-queries, performance]
tags_dependencias: [CDT-TASK-020, CDT-TASK-022]
---

## Descripción
Ejecutar stress test de 50 usuarios con slow_query_log activo para capturar y analizar queries que toman más de 0.5s bajo carga real.

## Contexto
El stress test original (prompt 014, 200 usuarios) colapsó por tabSeries. Después del fix de SEQUENCE (prompt 018) el row_lock_time_avg bajó a 0ms. Ahora hay que identificar qué otras queries pueden ser lentas bajo carga moderada (50 usuarios).

## Dependencias
- CDT-TASK-020 completada (red privada — DB conecta por IP privada)
- CDT-TASK-022 completada (Gunicorn 5 workers, slow_query_log habilitado)

## Tareas para el prompt

1. Limpiar slow query log antes del test
2. Ejecutar Locust 50 usuarios / 3 minutos contra endpoints de escritura (OT-2, PO, PI)
3. Durante el test: capturar `SHOW PROCESSLIST` cada 30s
4. Post-test: leer slow query log completo
5. Ejecutar `EXPLAIN` en las queries más lentas
6. Capturar métricas Grafana durante el test (CPU, RAM, conexiones, row_lock_waits)

## Datos técnicos
- Locust en backend: `164.92.94.47`
- Scripts: `/home/erpnext/locust/` (ver prompt 013)
- Target: `https://cdtalleres-copia.shalom.com.pe`
- Slow query log: `/var/log/mysql/slow.log` o path equivalente

## Criterios de aceptación
- [ ] Test completado 50u/3min sin colapso total
- [ ] Slow query log capturado y analizado
- [ ] Top 5 queries lentas identificadas con EXPLAIN
- [ ] Métricas Grafana durante test documentadas
- [ ] Comparación vs baseline original (96% fail) documentada

## Prompt preparado
Requiere crear prompt 024.
