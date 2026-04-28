---
tipo: plantilla
version: 1.0
---

# 🎯 Template: Skill

Copia este template para registrar un skill reutilizable:

```yaml
---
name: ""
descripcion: ""
ia_target: claude-code          # claude-code | crowbot | copilot
categoria: backend              # backend | frontend | devops | testing | design | erp
riesgo: low                     # low | medium | high | unknown
origen: community               # community | local | custom
proyectos_asignados: []         # lista de proyectos donde aplica
fecha_creacion: {{date}}
---

## Cuándo usar
- [Situaciones donde este skill aplica]

## Cuándo NO usar
- [Situaciones donde este skill NO debe usarse]

## Instrucciones
[Prompt/instrucciones del skill]

## Ejemplo de uso
[Ejemplo de interacción con el skill]
```
