---
name: erp-task-comparator
ia_target: claude-code
categoria: erp
riesgo: low
origen: local
proyectos_asignados:
  - ERPNext-v15
fuente_original: "c:\\dev\\correo-docker\\skill\\erp-task-comparator\\skill.md"
---

# 🔄 ERP Task Comparator

Especialista en sincronización y comparación de tareas entre el ERP y el registro histórico local.

## Cuándo usar
- Comparar tareas completadas en ERPNext vs registro local
- Identificar discrepancias de sincronización
- Generar reportes de diferencias

## Configuración
- **Base URL**: `https://erp-test.shalom.com.pe`
- **Endpoint**: `/api/resource/Task`
- **Auth**: Token `5867d8ac905cfaa:4de033693c40891`
- **Filtros**: status=Completed, department="Recursos Humanos - SE"

## Flujo
1. Conectar a ERP y extraer tareas completadas
2. Cargar JSON histórico local
3. Comparar IDs (ERP vs local)
4. Generar `erp_comparison_results.json`
5. Reportar diferencias

## Prompt base
> Ver archivo completo en: `c:\dev\correo-docker\skill\erp-task-comparator\skill.md`
