---
ultima_actualizacion: 2026-04-25
---

# 🧠 Catálogo de IAs

Guía para seleccionar la IA correcta según el tipo de tarea.

## IAs Disponibles

### 1. Gemini / Antigravity (CrowBot) 🤖
- **Acceso**: IDE integrado (Gemini en VS Code)
- **Fortalezas**:
  - Gestión de proyectos y tareas
  - Orquestación multi-herramienta
  - Acceso a filesystem, terminal, browser
  - Generación de imágenes
  - NotebookLM MCP integrado
- **Usar para**: Tareas de gestión, crear/modificar archivos, ejecutar comandos, investigación con NotebookLM, flujos complejos multi-paso
- **No usar para**: Refactoring masivo de código (mejor Claude Code)

### 2. Claude Code 🟣
- **Acceso**: CLI (`claude`), IDE integrado
- **Fortalezas**:
  - Refactoring profundo de código
  - Debugging complejo
  - Soporte de Skills (prompts especializados)
  - Contexto largo de código
  - Trabajo con repos grandes
- **Usar para**: Desarrollo de features, debugging, refactoring, code review, generación de tests
- **Skills disponibles**: Ver sección "Skills por Proyecto" abajo

### 3. NotebookLM 📓
- **Acceso**: MCP integrado en CrowBot
- **Fortalezas**:
  - Análisis de documentos largos
  - Generación de podcasts/audio
  - Flashcards y quizzes
  - Investigación web (deep research)
- **Usar para**: Analizar documentación técnica, preparar material de estudio, investigar tecnologías nuevas

### 4. GitHub Copilot ✈️
- **Acceso**: VS Code extension
- **Fortalezas**:
  - Autocompletado inline ultra-rápido
  - Sugerencias contextuales en tiempo real
  - Chat integrado en VS Code
- **Usar para**: Escritura de código rutinario, autocompletado, sugerencias rápidas mientras escribes

---

## Matriz de Decisión

| Tarea | IA Recomendada | Razón |
|---|---|---|
| Crear feature nueva (backend) | Claude Code + skill backend-architect | Skills especializados, contexto largo |
| Crear feature nueva (frontend) | Claude Code + skill ui-ux-designer | Design system, componentes Vue |
| Debugging producción | Claude Code | Análisis profundo de stack traces |
| Gestión de tareas/proyectos | CrowBot (Antigravity) | Acceso a filesystem + vault |
| Deploy a servidor | CrowBot (Antigravity) | Acceso a terminal + SSH |
| Investigar tecnología | NotebookLM (vía CrowBot) | Deep research, fuentes web |
| Escribir documentación | CrowBot (Antigravity) | Acceso a archivos + generación |
| Revisar UI/UX | Claude Code + skill ui-visual-validator | Análisis visual riguroso |
| Automatizar pipeline | CrowBot (Antigravity) | GitHub Actions, Docker |
| Control Remoto (Telegram) | Antigravity Telegram Suite | Control remoto de agentes vía móvil |
| Código rutinario | GitHub Copilot | Velocidad, inline |
| Sincronizar ERP | Claude Code + skill erp-task-comparator | Skill específico para ERP |
| Generar tests | Claude Code + skill unit-testing | Cobertura, mocks, fixtures |

---

## Skills por Proyecto

### El Buen Gestor
| Skill | Uso principal |
|---|---|
| backend-architect | Diseño de APIs y servicios Laravel |
| backend-dev-guidelines | Standards de código backend (Node.js/adaptable) |
| backend-feature-development | Workflow completo de features |
| ui-ux-designer | Diseño de interfaces Vue 3 |
| ui-visual-validator | Validación visual de cambios UI |
| unit-testing | Generación de tests |

### Reclutamiento Gamificado
| Skill | Uso principal |
|---|---|
| backend-architect | Arquitectura Laravel + ERPNext API |
| backend-feature-development | Desarrollo de features end-to-end |
| ui-ux-designer | Interfaz gamificada Vue 3 |
| ui-ux-pro-max | Búsqueda de estilos y paletas UI |
| ui-visual-validator | QA visual de componentes |
| unit-testing | Tests de controladores y servicios |

### ERPNext v15
| Skill | Uso principal |
|---|---|
| erp-task-comparator | Sincronización de tareas ERP ↔ local |
| backend-architect | Diseño de integraciones API |

### Correo Mailcow
| Skill | Uso principal |
|---|---|
| ui-ux-designer | Rediseño de login page |
| ui-ux-pro-max | Paletas de color, tipografía |

### ZKTeco Biometría
| Skill | Uso principal |
|---|---|
| backend-architect | Diseño de integración biométrica |
| unit-testing | Tests del script de sincronización |
