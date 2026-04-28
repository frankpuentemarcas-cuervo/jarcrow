---
titulo: "Migrar ACC-GLE y MAT-SLE a MariaDB SEQUENCE"
proyecto: CDTalleres
categoria: trabajo
prioridad: media
estado: pendiente
automatizable: si
ia_recomendada: crowbot
prompt_preparado: false
fecha_creacion: 2026-04-25
tiempo_estimado: 2h
tags: [mariadb-sequence, naming-series, gl-entry, stock-ledger-entry]
---

## Descripción
GL Entry (ACC-GLE) y Stock Ledger Entry (MAT-SLE) son DocTypes core de ERPNext con más de 149k y 118k registros respectivamente. Si la carga escala, sus tabSeries locks volverán a ser cuello de botella.

## Contexto
Del audit tabSeries (prompt 015):
- `ACC-GLE-2025-`: 149,252 registros
- `MAT-SLE-2025-`: 118,686 registros

Son DocTypes core de ERPNext (no custom) — no se puede editar el Python controller directamente. La estrategia es Server Script (before_insert) igual que se hizo con Purchase Order y Purchase Invoice en prompt 018.

## ⚠️ Riesgo alto
GL Entry y Stock Ledger Entry son tablas contables críticas. Un naming incorrecto puede romper la trazabilidad contable. Ejecutar solo si:
- Se tiene backup reciente de DB
- Se prueba primero en ambiente de copia (`cdtalleres-copia`)
- Frank aprueba el cambio de formato de ID

## Estrategia
- Crear SEQUENCE `seq_gl_entry` (START con valor actual ACC-GLE-2025- + 1)
- Crear SEQUENCE `seq_stock_ledger` (START con valor actual MAT-SLE-2025- + 1)
- Server Script before_insert en GL Entry → formato `GLE-XXXXXX`
- Server Script before_insert en Stock Ledger Entry → formato `SLE-XXXXXX`
- Congelar series ACC-GLE y MAT-SLE en tabSeries

## Datos técnicos
- Contadores actuales: ACC-GLE-2025-: 149252, MAT-SLE-2025-: 118686
- DB: `146.190.42.73` / `_0646d69b639ad0ff`
- Frontend (Server Scripts): `209.38.75.235`

## Criterios de aceptación
- [ ] SEQUENCE creadas con valor correcto
- [ ] Server Scripts activos y generando IDs legibles
- [ ] tabSeries ACC-GLE y MAT-SLE congelados
- [ ] Crear GL Entry y Stock Ledger Entry de prueba y verificar ID generado
- [ ] tabSeries row_lock_time_avg sigue en 0ms bajo test

## Prompt preparado
Requiere crear prompt 025. **Consultar con Frank antes de ejecutar** — cambio en IDs contables.
