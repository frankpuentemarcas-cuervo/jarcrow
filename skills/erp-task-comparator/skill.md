---
name: erp-task-comparator
description: Especialista en sincronización y comparación de tareas entre el ERP y el registro histórico local.
risk: low
source: local
date_added: '2026-03-13'
---

Este skill permite al agente conectarse al ERP, extraer tareas completadas y compararlas con el archivo histórico local para identificar discrepancias.

## Instrucciones

### Instrucción 1: Extracción y Comparación de Tareas
1. **Conexión al ERP**: Utiliza los siguientes parámetros de conexión:
   - **Base URL**: `https://erp-test.shalom.com.pe`
   - **Endpoint**: `/api/resource/Task`
   - **Autenticación**: Token-based (`5867d8ac905cfaa:4de033693c40891`).
2. **Filtros de Búsqueda**:
   - `status`: "Completed"
   - `department`: "Recursos Humanos - SE"
   - `sistema`: En ["ERP", "EMPRESARIAL", "EXPRESS", "APP FAMILIA", "INTERNO"]
   - `completed_on`: Rango amplio (ej. 2022-01-01 hasta 2026-12-31).
3. **Carga Local**: Lee el archivo histórico desde `server/data/historical_tasks.json`.
4. **Comparación**:
   - Compara los IDs de las tareas del ERP con los IDs en el JSON local.
   - Identifica tareas que están en el ERP pero faltan en el JSON.
   - Identifica tareas que están en el JSON pero no están en el ERP.
5. **Registro de Resultados**: Guarda las diferencias en un archivo llamado `erp_comparison_results.json` en la raíz del proyecto agent.

### Instrucción 2: Procesamiento de Diferencias
*Una vez generada la lista de discrepancias en `erp_comparison_results.json`, realiza las siguientes acciones:*
1. **Reporte**: Genera un resumen de cuántas tareas faltan en cada lado.
2. **Acción Posterior**: Si existen tareas faltantes en el JSON local, prepárate para ejecutar el script de sincronización o notificar al usuario para su aprobación.

## Consideraciones de Seguridad
- No compartas las API Keys fuera de las conexiones seguras.
- Asegúrate de que las rutas de los archivos sean absolutas para evitar errores de contexto.
