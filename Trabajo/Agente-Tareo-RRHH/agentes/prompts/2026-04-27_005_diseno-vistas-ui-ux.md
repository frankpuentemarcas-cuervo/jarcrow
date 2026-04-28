---
fecha: 2026-04-27
agente_id: "005"
descripcion: "diseno-implementacion-vistas-ia-tareo"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-27_005_diseno-vistas-ui-ux.md"
---

# Fase 4: Diseño e Implementación de Vistas con IA

## 🚀 OBLIGATORIO: Carga de Skills de Ingeniería
Antes de empezar, debes copiar el contenido de `C:\jarcrow\skills\` a tu directorio de configuración de agente (ej. `.claude/skills/` o la carpeta equivalente de tu entorno) para actuar como Experto UI/UX Pro Max.

## Tareas

### 1. Generación del Design System
- Utiliza la skill `ui-ux-pro-max` para generar un `MASTER.md` de diseño en el proyecto.
- Estilo recomendado: **Bento Grid** + **Soft UI**.
- Colores: Paleta corporativa de Shalom (Azul/Rojo) pero suavizada para dashboards de datos densos.

### 2. Creación de Componentes Base
- Implementar Layout principal con Sidebar colapsable.
- Componente `StatusBadge` para estados de asistencia.
- Componente `InconsistencyCard` para mostrar los hallazgos de la IA.

### 3. Implementación de Vistas (Inertia/Vue)
- **Dashboard.vue**: Layout tipo Bento con los KPIs de asistencia.
- **AnalisisDetalle.vue**: Vista de timeline de marcaciones con el sidebar de análisis de Gemini.
- **Alertas.vue**: Listado filtrable de inconsistencias pendientes de resolución.

### 4. Conexión de Datos
- Asegura que las vistas consuman los datos procesados por `AIAnalyzerService`.
- Implementar estados de "Loading" con esqueletos (Skeleton Screens) mientras la IA procesa el análisis.

---

## Archivo de salida
`c:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-27_005_diseno-vistas-ui-ux.md`
