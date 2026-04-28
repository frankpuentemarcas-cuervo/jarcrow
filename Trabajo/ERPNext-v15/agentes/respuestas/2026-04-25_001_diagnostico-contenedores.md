---
fecha: 2026-04-25
agente_id: "001"
descripcion: diagnostico-contenedores-web-no-carga
proyecto: ERPNext-v15
estado: completado
---

# Diagnóstico ERPNext v15 Docker — 2026-04-25 13:30

## Hallazgos clave

- **Todos los contenedores de app en estado `Created`** — nunca arrancaron
- **Configurator falló (exit 2)** — `bench set-config` no reconocido + `apps/` no existe en WORKDIR
- **vol-sites VACÍO** — sitio Frappe nunca inicializado
- **DNS mismatch**: prompt decía `178.128.181.196`, DNS real apunta a `104.248.66.66`
- **nginx.conf**: server_name incorrecto (`erp15docker.shalomcontrol.com`) pero irrelevante hasta que contenedores arranquen
- **MariaDB y Redis**: UP y healthy — base de datos OK

## Estado de contenedores

| Contenedor | Estado |
|---|---|
| erpnext-nginx-proxy | Created (no arrancó) |
| erpnext-frontend | Created (no arrancó) |
| erpnext-backend | Created (no arrancó) |
| erpnext-websocket | Created (no arrancó) |
| erpnext-scheduler | Created (no arrancó) |
| erpnext-queue-short | Created (no arrancó) |
| erpnext-queue-long | Created (no arrancó) |
| erpnext-configurator | Exited (2) — CAUSA RAÍZ |
| erpnext-database | Up 15h (healthy) ✅ |
| erpnext-redis-cache | Up 15h (healthy) ✅ |
| erpnext-redis-queue | Up 15h (healthy) ✅ |

## Error del configurator

```
ls: cannot access 'apps': No such file or directory
WARN: Command not being executed in bench directory
Error: No such command 'set-config'.
```

## Diagnóstico raíz

Dependencia de inicio: todos los contenedores de app esperan que `configurator` complete con éxito antes de arrancar. El configurator falla porque:
1. El WORKDIR del contenedor no contiene la carpeta `apps/`
2. El comando `bench set-config` no existe en la versión de bench instalada

## Próximo paso (prompt 002b)

1. Verificar IP real del servidor (¿`104.248.66.62` o `178.128.181.196`?)
2. Inspeccionar docker-compose.yml del configurator — ver WORKDIR, comando, volúmenes
3. Corregir configurator para que arranque correctamente
4. Una vez vol-sites inicializado → corregir nginx.conf
