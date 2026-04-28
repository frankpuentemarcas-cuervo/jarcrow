---
titulo: "Purgar tabWorkflow Action — 2.79M filas / 480MB"
proyecto: CDTalleres
categoria: trabajo
prioridad: alta
estado: pendiente
automatizable: si
ia_recomendada: crowbot
prompt_preparado: false
fecha_creacion: 2026-04-25
tiempo_estimado: 2h
tags: [mariadb, limpieza, performance, workflow]
---

## Descripción
La tabla `tabWorkflow Action` tiene 2,790,159 filas y ocupa ~480MB. Es acumulación histórica de acciones de workflow que nunca se limpia automáticamente. Reduce velocidad de backups y queries relacionadas.

## Contexto
Detectado en auditoría tabSeries (prompt 015). No tiene naming series — no afecta tabSeries lock. Pero su volumen degrada:
- Tiempo de backup (480MB extra en cada dump)
- Queries que hacen JOIN con tabWorkflow Action
- Tamaño general de la DB

## Estrategia de purga segura

1. **Auditar antes de borrar**: verificar qué columnas tiene, cuál es la fecha más antigua, distribución por estado
2. **Borrar por lotes**: DELETE con LIMIT 10000 + SLEEP para no bloquear DB
3. **Conservar**: registros de los últimos 90 días (o el período que Frank defina)
4. **OPTIMIZE TABLE** al finalizar para reclamar espacio

## Datos técnicos
- DB: `146.190.42.73`
- DB name: `_0646d69b639ad0ff`
- Tabla: `tabWorkflow Action`
- Filas estimadas: 2,790,159
- Tamaño: ~480MB

## ⚠️ Precaución
- Hacer backup de la tabla antes de purgar: `CREATE TABLE tabWorkflow_Action_backup_20260425 SELECT * FROM tabWorkflow Action WHERE ...`
- O al menos backup de la DB completa
- Borrar en lotes, no en un solo DELETE masivo

## Criterios de aceptación
- [ ] Backup o snapshot antes de purgar
- [ ] Registros > 90 días eliminados en lotes
- [ ] `SELECT COUNT(*) FROM tabWorkflow Action` muestra reducción significativa
- [ ] `OPTIMIZE TABLE` ejecutado
- [ ] Tamaño DB reducido verificado en `information_schema`

## Prompt preparado
Requiere crear prompt 023.
