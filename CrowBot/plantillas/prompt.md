---
tipo: plantilla
version: 1.0
---

# 💬 Template: Prompt

Copia este template para almacenar un prompt listo para ejecutar:

```yaml
---
titulo: ""
ia_destino: ""                  # claude-code | crowbot | copilot | notebooklm | chatgpt
proyecto: ""                    # proyecto asociado
skill_base: ""                  # skill del que se deriva (si aplica)
tipo: ejecucion                 # ejecucion | investigacion | generacion | debug | review
reutilizable: true              # true | false
variables: []                   # variables que el usuario debe completar
fecha_creacion: {{date}}
---

## Prompt

> [El prompt completo, listo para copiar y pegar]

## Variables a completar
| Variable | Descripción | Ejemplo |
|---|---|---|
| `{{variable}}` | Qué es | Valor ejemplo |

## Resultado esperado
[Qué debería producir este prompt]

## Notas
[Contexto adicional, tips de uso]
```
