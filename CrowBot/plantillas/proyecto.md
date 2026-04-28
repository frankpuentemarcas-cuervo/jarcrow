---
tipo: plantilla
version: 1.0
---

# 🗂️ Template: Proyecto

Copia este template para registrar un nuevo proyecto:

```yaml
---
nombre: ""
cliente: ""                     # shalom | personal | otro
categoria: trabajo              # trabajo | personal
estado: activo                  # activo | pausado | completado | archivado
stack:
  backend: ""                   # laravel | python | erpnext | node
  frontend: ""                  # vue3 | react | html | none
  database: ""                  # mysql | mariadb | postgres | none
  infra: ""                     # docker | k8s | vps | none
repo: ""                        # URL del repositorio
ruta_local: ""                  # c:\dev\nombre-proyecto
servidor: ""                    # IP o nombre del servidor
dominio: ""                     # URL del dominio
skills_asignados: []            # lista de skills aplicables
ia_principal: ""                # IA principal para este proyecto
fecha_inicio: ""
ultima_actividad: {{date}}
---

## Descripción
[Qué es este proyecto, qué problema resuelve]

## Arquitectura
[Resumen de la arquitectura técnica]

## Tareas activas
- Ver carpeta `tareas/` de este proyecto

## Skills asignados
| Skill | Uso | IA |
|---|---|---|
| skill-name | Para qué se usa | claude-code / crowbot |

## Accesos
- Ver `accesos.md` de este proyecto

## Notas importantes
[Restricciones, decisiones clave, cosas a recordar]
```
