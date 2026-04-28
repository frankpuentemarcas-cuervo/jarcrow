---
titulo: "Investigar Solicitud de Pagos — error 417 Expectation Failed"
proyecto: CDTalleres
categoria: trabajo
prioridad: baja
estado: pendiente
automatizable: si
ia_recomendada: crowbot
prompt_preparado: false
fecha_creacion: 2026-04-25
tiempo_estimado: 1h
tags: [debug, solicitud-pagos, frappe, validacion]
---

## Descripción
El DocType "Solicitud de Pagos" retorna 100% de errores 417 (Expectation Failed) en el stress test. No está relacionado con tabSeries — es un error de validación interna de Frappe/ERPNext.

## Contexto
Del stress test (prompt 014): `POST /Solicitud de Pagos` → 100% fail con HTTP 417. El error 417 en Frappe indica que el documento no pasó validación (campos obligatorios, lógica de negocio, etc.). Los datos del test de Locust pueden no ser válidos para este DocType.

## Tareas

1. Revisar el script Locust para Solicitud de Pagos — ver qué datos envía
2. Comparar con campos obligatorios del DocType en Frappe
3. Intentar crear una Solicitud de Pagos manualmente via API con datos correctos
4. Revisar logs del backend al momento del 417 (`frappe.log`)
5. Determinar si es problema del script de test o bug real del DocType

## Datos técnicos
- Backend logs: `/home/erpnext/frappe-bench/logs/`
- Scripts Locust: `/home/erpnext/locust/` en `164.92.94.47`
- Site: `CDTALLERES`

## Criterios de aceptación
- [ ] Causa del 417 identificada (datos inválidos en test vs bug real)
- [ ] Si es datos inválidos: script Locust corregido
- [ ] Si es bug real: documentado y escalado
- [ ] Solicitud de Pagos retorna 200 con datos correctos

## Prompt preparado
Requiere crear prompt 026.
