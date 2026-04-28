---
name: ERPNext v15 — Estado actual
description: Estado de producción del ERPNext v15 Docker en 178.128.181.196 — contenedores up, web no carga
type: project
---

ERPNext v15 en Docker corriendo en producción (178.128.181.196). DNS propagado. Web no carga.

**Why:** Dominio en nginx.conf no coincide con el DNS activo → Nginx rechaza requests o no termina SSL correctamente.

**How to apply:** Al trabajar este proyecto, priorizar corrección de nginx.conf y certificado SSL antes de cualquier otra tarea.

## Infraestructura

- **Servidor**: 178.128.181.196 (root, SSH key: `c:\dev\erpv15\id_rsa_deploy`)
- **Dominio activo DNS**: `erpv15-qatest.shalom.com.pe`
- **Dominio en nginx.conf**: `erp15docker.shalomcontrol.com` ← MISMATCH (causa probable del problema)
- **Ruta local**: `c:\dev\erpv15\`
- **Docker compose**: `c:\dev\erpv15\docker\docker-compose.yml`

## Stack Docker (10 contenedores)

| Contenedor | Imagen | Rol |
|---|---|---|
| erpnext-configurator | docker-backend:latest | init (run-once) |
| erpnext-database | mariadb:10.6 | DB |
| erpnext-redis-cache | redis:7-alpine | Cache |
| erpnext-redis-queue | redis:7-alpine | Queue |
| erpnext-backend | docker-backend:latest | Gunicorn :8000 |
| erpnext-websocket | docker-socketio:latest | SocketIO :9000 |
| erpnext-queue-short | docker-worker-short:latest | Workers |
| erpnext-queue-long | docker-worker-long:latest | Workers |
| erpnext-scheduler | docker-scheduler:latest | Scheduler |
| erpnext-frontend | docker-nginx:latest | Frappe frontend :8080 |
| erpnext-nginx-proxy | nginx:alpine | SSL proxy :80/:443 |

## Nginx config

- **Archivo**: `c:\dev\erpv15\docker\services\nginx\nginx.conf`
- **server_name**: `erp15docker.shalomcontrol.com` ← debe cambiarse a `erpv15-qatest.shalom.com.pe`
- **Upstream frontend**: `frontend:8080`
- **SSL certs**: `/etc/nginx/certs/erp15docker.shalomcontrol.com.crt/.key` ← deben reemplazarse
- **Certs locales en**: `c:\dev\erpv15\docker\services\nginx\certs\`

## Problema principal

nginx-proxy tiene `server_name erp15docker.shalomcontrol.com` con certificado SSL para ese dominio. El DNS apunta `erpv15-qatest.shalom.com.pe` → 178.128.181.196. Browser llega, Nginx responde pero con dominio incorrecto → SSL error o no carga.

## Restricción conocida

No usar `departamento` en queries de Task — ERPNext retorna DataError 417. Solo válido en Issue DocType.
