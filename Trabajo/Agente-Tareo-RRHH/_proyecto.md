---
nombre: Agente Tareo RRHH
cliente: shalom
categoria: trabajo
estado: activo
stack:
  backend: laravel 11
  frontend: vue 3 + tailwind
  database: mariadb
  ai: gemini api / claude api
  infra: docker
repo: ""
ruta_local: "c:\\dev\\agente-tareo-rrhh"
ia_principal: crowbot
fecha_inicio: 2026-04-25
ultima_actividad: 2026-04-25
---

# Agente de Tareo RRHH

## Descripción
Plataforma inteligente para la gestión y resumen de asistencia (tareo) de los colaboradores de Shalom. Utiliza IA para analizar patrones de marcación, detectar inconsistencias y automatizar la corrección de asistencia.

## Objetivos
- Generar un panel con Laravel y Vue conectado a IA.
- Evaluar data de marcaciones y asistencia.
- Detectar marcaciones incompletas e inconsistencias.
- Identificar ausencias seguidas de retorno sin corrección de asistencia.
- Resumir el tareo final para planilla.

## Arquitectura (Propuesta)
- **Backend**: Laravel 11 (API)
- **Frontend**: Vue 3 (Inertia.js o SPA)
- **IA**: Orquestador que envía lotes de marcaciones a un LLM para análisis de patrones.
- **Base de Datos**: Esquema relacional para historial de marcaciones.

## Tareas Principales
1. **Setup**: Inicializar Laravel + Vue y Docker.
2. **Database**: Diseñar esquema de asistencia y empleados.
3. **Ingestion**: Script/API para recibir data de ZKTeco/ERPNext.
4. **AI Logic**: Implementar service class para conexión con LLM y prompt engineering.
5. **Dashboard**: Vista de alertas y resumen de tareo.

## Historial reciente
- 2026-04-25: Inicio del proyecto y definición de hoja de ruta.
