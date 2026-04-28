# Hoja de Ruta: Agente Tareo RRHH

Objetivo: Desarrollar un sistema inteligente que analice marcaciones de asistencia de Shalom usando IA y genere resúmenes de tareo detectando inconsistencias.

## Fase 1: Arquitectura y Setup Inicial
- [ ] **1.1 Inicializar Proyecto**: Setup de Laravel 11 + Vue 3 (Inertia.js) + Tailwind CSS.
- [ ] **1.2 Configuración Docker**: Dockerizar el entorno para desarrollo local y producción.
- [ ] **1.3 Diseño de DB**: Definir tablas para `colaboradores`, `marcaciones`, `turnos` y `asistencias_procesadas`.

## Fase 2: Ingesta y Procesamiento de Datos
- [ ] **2.1 Pipeline de Ingesta**: Crear comandos de consola para importar data desde archivos CSV/JSON o APIs externas (ZKTeco).
- [ ] **2.2 Lógica de Negocio (Legacy)**: Implementar el cálculo básico de horas trabajadas, tardanzas y faltas sin IA.

## Fase 3: Integración de IA
- [ ] **3.1 Service Layer IA**: Conectar con la API de Gemini 1.5 Pro o Claude 3.5 Sonnet.
- [ ] **3.2 Prompt Engineering**: Crear el "System Prompt" que explique las reglas de tareo de Shalom a la IA.
- [ ] **3.3 Agente de Análisis**: Función que envía la data de un colaborador por periodo a la IA para que retorne un JSON con las inconsistencias detectadas.

## Fase 4: Panel de Usuario (Frontend)
- [ ] **4.1 Dashboard Principal**: Resumen visual de inconsistencias detectadas en la última semana/quincena.
- [ ] **4.2 Vista Detalle Colaborador**: Comparativa entre la marcación real y el análisis de la IA.
- [ ] **4.3 Módulo de Corrección**: Interfaz para "Aceptar Sugerencia de IA" o "Corregir Manualmente".

## Fase 5: Reportes y Cierre
- [ ] **5.1 Exportación**: Generar archivos Excel/PDF listos para el área de planillas.
