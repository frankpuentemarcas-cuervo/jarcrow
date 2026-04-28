---
tipo: plantilla
version: 1.0
---

# 📋 Template: Tarea

Copia este template para crear una nueva tarea:

```yaml
---
titulo: ""
proyecto: ""                    # ERPNext-v15 | El-Buen-Gestor | Reclutamiento-Gamificado | Correo-Mailcow | ZKTeco-Biometria
categoria: trabajo              # trabajo | personal
prioridad: media                # critica | alta | media | baja
estado: pendiente               # pendiente | en-progreso | completada | bloqueada | cancelada
automatizable: evaluar          # si | no | parcial | evaluar
ia_recomendada: ""              # crowbot | claude-code | copilot | notebooklm
skill_requerido: ""             # backend-architect | ui-ux-designer | etc.
prompt_preparado: false         # true | false
fecha_creacion: {{date}}
fecha_limite: ""
tiempo_estimado: ""             # 30min | 1h | 2h | 4h | 1d | 2d | 1w
tags: []
---

## Descripción
[Qué hay que hacer]

## Contexto
[Por qué es necesario, qué problema resuelve]

## Criterios de aceptación
- [ ] Criterio 1
- [ ] Criterio 2

## Prompt preparado
> [Si automatizable=si, incluir el prompt listo para ejecutar en la IA recomendada]

## Notas
[Observaciones adicionales]
```
