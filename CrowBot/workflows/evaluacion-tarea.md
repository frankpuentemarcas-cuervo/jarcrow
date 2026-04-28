---
tipo: workflow
version: 2.0
---

# 🔄 Evaluación de Tareas — Workflow CrowBot

---

## Paso 1: Clasificar la tarea

```
¿Es de Trabajo o Personal?
├── Trabajo → ¿A qué proyecto pertenece?
│   ├── CDTalleres
│   ├── ERPNext v15
│   ├── El Buen Gestor
│   ├── Reclutamiento Gamificado
│   ├── Correo Mailcow
│   ├── ZKTeco Biometría
│   └── Nuevo proyecto → Crear ficha
└── Personal → Categorizar en Personal
```

## Paso 2: Evaluar automatización

| Pregunta | Respuesta | Acción |
|---|---|---|
| ¿Puede hacerlo un agente solo? | Sí | → Elaborar prompt de agente |
| ¿Puede un agente hacer parte? | Sí | → Elaborar prompt parcial + definir qué queda para Frank |
| ¿Requiere decisión humana? | Sí | → Preparar opciones para Frank |
| ¿Necesita acceso a servidor? | Sí | → Verificar credenciales en Vault / `accesos.md` del proyecto |
| ¿Necesita acceso a API? | Sí | → Verificar tokens en `🔐 Vault/apis.md` |

## Paso 3: Seleccionar IA y agente

```
Tipo de tarea:
├── Código (crear/modificar/debuggear)
│   ├── Feature completa → Claude Code + skill correspondiente
│   ├── Bug fix rápido → Claude Code
│   └── Autocompletado → Copilot
├── Infraestructura (deploy, Docker, SSH, CI/CD)
│   └── Agente Antigravity → acceso a terminal y servidores
├── Investigación
│   └── Agente Antigravity + NotebookLM MCP
├── Diseño UI
│   ├── Diseño nuevo → Claude Code + ui-ux-designer
│   └── Validar visual → Claude Code + ui-visual-validator
├── Gestión (tareas, docs, vault)
│   └── CrowBot directamente
└── ERP (sincronización, comparación)
    └── Claude Code + erp-task-comparator
```

## Paso 4: Elaborar prompt de agente

1. Determinar número secuencial del día (001, 002...)
2. Copiar template: `🤖 CrowBot/plantillas/prompt-agente.md`
3. Completar frontmatter YAML (fecha, agente_id, ia_destino, archivo_salida)
4. Cargar contexto del proyecto desde `_proyecto.md`
5. Incluir accesos necesarios desde `accesos.md`
6. Definir estructura esperada del archivo de salida
7. Guardar en: `🏢 Trabajo/[Proyecto]/agentes/prompts/YYYY-MM-DD_NNN_descripcion.md`

**Regla 1**: El prompt debe ser autocontenido. El agente NO tiene contexto previo.

**Regla 2**: Todo prompt debe instruir al agente a generar/actualizar el archivo de salida después de CADA tarea, no solo al final. Documentar éxitos Y errores. Si una tarea falla, continuar con la siguiente.

## Paso 5: Monitorear respuesta del agente

Cuando Frank dice "el agente terminó":

1. Leer el archivo de salida indicado en el frontmatter del prompt
2. Verificar que contenga todas las secciones esperadas
3. Resumir hallazgos clave (5-10 bullets)
4. Indicar el siguiente paso lógico
5. Copiar respuesta al vault: `🏢 Trabajo/[Proyecto]/agentes/respuestas/YYYY-MM-DD_NNN_descripcion.md`
6. Actualizar `estado` del prompt a `completado` o `fallido`
7. Registrar decisiones relevantes en `🤖 CrowBot/memoria/decisiones-log.md`

---

## Nomenclatura de archivos de agentes

```
YYYY-MM-DD_NNN_descripcion-kebab.md
│           │   └── qué hace el agente (corto, kebab-case)
│           └── número secuencial del día (001, 002, 003...)
└── fecha ISO
```

Ejemplos:
- `2026-04-25_001_verificar-conectividad.md`
- `2026-04-25_002_investigar-frappe-skills.md`
- `2026-04-25_003_instalar-skills-claude.md`

---

## Checklist rápido para cada tarea nueva

- [ ] ¿Proyecto identificado?
- [ ] ¿Prioridad asignada?
- [ ] ¿Evaluación de automatización hecha?
- [ ] ¿IA / agente seleccionado?
- [ ] ¿Skill asignado (si aplica)?
- [ ] ¿Prompt elaborado y guardado en vault?
- [ ] ¿Archivo de salida definido en el prompt?
- [ ] ¿Accesos verificados?
- [ ] ¿Respuesta del agente revisada y guardada?
- [ ] ¿Decisiones relevantes registradas en decisiones-log?
