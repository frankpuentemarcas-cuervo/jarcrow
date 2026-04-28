---
fecha: 2026-04-25
agente_id: "003"
descripcion: fix-dockerfile-imagen-apps-websocket
proyecto: ERPNext-v15
ia_destino: antigravity
tipo: debug
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\erpv15\\fix-dockerfile-results.md"
dependencia: "002b (configurator fix completado, stack parcialmente levantado)"
---

# Fix Dockerfile + Imagen + Websocket — ERPNext v15

## Contexto para el agente

Proyecto ERPNext v15 Docker (Overskull para Shalom). El configurator ya corre con exit 0 (prompt 002b completado). El problema ahora está en la imagen `docker-backend:latest` y en el entrypoint del websocket.

### Servidor
| Campo | Valor |
|---|---|
| IP | 178.128.181.196 |
| Usuario SSH | root |
| Llave SSH | `c:\dev\erpv15\id_rsa_deploy` |
| Ruta proyecto en servidor | `/home/erpnext/docker/docker` (verificada en 002b) |
| Dominio activo | erp15docker.shalomcontrol.com |

### Estado actual del stack (post 002b)
```
erpnext-configurator    Exited (0)       ✅
erpnext-database        Up (healthy)     ✅
erpnext-redis-cache     Up (healthy)     ✅
erpnext-redis-queue     Up (healthy)     ✅
erpnext-backend         Up               ✅ (pero sin apps/)
erpnext-websocket       Restarting (1)   ❌ CRASH LOOP
erpnext-frontend        Up               ⚠️ sin websocket
erpnext-nginx-proxy     Restarting       ❌ upstream websocket caído
```

### Bugs identificados (análisis de código local)

#### Bug 1 — Dockerfile backend: brace expansion rota (CAUSA RAÍZ)

En `/home/erpnext/docker/docker/services/backend/Dockerfile` (o ruta equivalente en servidor), línea RUN que crea directorios:

```dockerfile
RUN useradd -m -s /bin/bash frappe \
    && mkdir -p /home/frappe/frappe-bench/{sites,logs,apps,config/pids} \
    && chown -R frappe:frappe /home/frappe
```

**Problema**: `RUN` en Dockerfile usa `/bin/sh` por defecto. La imagen base es `python:3.11-slim-bookworm` donde `/bin/sh` es `dash`, que **no soporta brace expansion `{...}`**. Resultado: se crea el directorio literal `/home/frappe/frappe-bench/{sites,logs,apps,config` en lugar de los 4 directorios separados.

**Fix**: Cambiar a `RUN ["bash", "-c", "..."]` o separar los mkdir:
```dockerfile
RUN useradd -m -s /bin/bash frappe \
    && mkdir -p /home/frappe/frappe-bench/sites \
    && mkdir -p /home/frappe/frappe-bench/logs \
    && mkdir -p /home/frappe/frappe-bench/apps \
    && mkdir -p /home/frappe/frappe-bench/config/pids \
    && chown -R frappe:frappe /home/frappe
```

#### Bug 2 — socketio/entrypoint.sh: espera redis-socket inexistente

En `services/socketio/entrypoint.sh` línea ~20:
```sh
until redis-cli -h "redis-socket" -p 11000 ping >/dev/null 2>&1; do
```

**Problema**: No existe servicio `redis-socket` en docker-compose.yml. Los servicios Redis son `redis-cache` (6379) y `redis-queue` (6379). El websocket queda en loop infinito esperando un host que nunca existe.

**Fix**: Cambiar a `redis-queue` puerto `6379`:
```sh
until redis-cli -h "redis-queue" -p 6379 ping >/dev/null 2>&1; do
```

#### Bug 3 — socketio.js no existe porque apps/ no existe

Como consecuencia del Bug 1, `apps/frappe/socketio.js` nunca se creó en la imagen. Al reconstruir con el fix del Bug 1, este se resuelve **solo si las apps (frappe, erpnext) están instaladas en la imagen**. Verificar durante el proceso.

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

**Generar o actualizar `c:\dev\erpv15\fix-dockerfile-results.md` después de CADA tarea completada o fallida.**

1. Nunca terminar sin el archivo de salida (aunque sea parcial)
2. Si una tarea falla → documentar error exacto → continuar con la siguiente
3. Nunca `docker-compose down -v` — destruiría `vol-db-data`

## 📲 Notificaciones Telegram — obligatorio después de CADA tarea

```bash
TBOT_TOKEN="8610126794:AAFcmZUxmq9swtkOMH7Ez-vbLFOvTelLFOs"
TBOT_CHAT="1412266627"
tg_notify() {
  curl -s -X POST "https://api.telegram.org/bot${TBOT_TOKEN}/sendMessage" \
    -d chat_id="${TBOT_CHAT}" \
    -d parse_mode="Markdown" \
    -d text="$1" > /dev/null
}
```

---

## Tareas a ejecutar

**Primero — conectar al servidor y definir variables:**

```bash
ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no root@178.128.181.196

TBOT_TOKEN="8610126794:AAFcmZUxmq9swtkOMH7Ez-vbLFOvTelLFOs"
TBOT_CHAT="1412266627"
tg_notify() {
  curl -s -X POST "https://api.telegram.org/bot${TBOT_TOKEN}/sendMessage" \
    -d chat_id="${TBOT_CHAT}" \
    -d parse_mode="Markdown" \
    -d text="$1" > /dev/null
}

# Localizar proyecto (debería ser /home/erpnext/docker/docker)
COMPOSE_DIR=$(find / -name "docker-compose.yml" 2>/dev/null | grep -i erp | grep -v node_modules | head -1 | xargs dirname)
echo "COMPOSE_DIR: $COMPOSE_DIR"
tg_notify "✅ *ERPv15 T0* — Conectado\nCOMPOSE_DIR: ${COMPOSE_DIR}"
```

---

### T1 — Verificar estado actual del stack y logs de websocket

```bash
docker ps -a --format "table {{.Names}}\t{{.Status}}"
docker logs erpnext-websocket 2>&1 | tail -30
docker logs erpnext-nginx-proxy 2>&1 | tail -20
```

Documentar: error exacto del websocket crash loop.

```bash
tg_notify "✅ *ERPv15 T1* — Estado capturado\nWebsocket error: [copiar primera línea de error]"
```

---

### T2 — Localizar Dockerfiles en el servidor y hacer backup

```bash
# Buscar Dockerfiles
find $COMPOSE_DIR -name "Dockerfile" 2>/dev/null
ls -la $COMPOSE_DIR/services/backend/
ls -la $COMPOSE_DIR/services/socketio/

# Backup de todos los archivos a modificar
BACKUP_DIR="$COMPOSE_DIR/backup-$(date +%Y%m%d_%H%M)"
mkdir -p $BACKUP_DIR
cp $COMPOSE_DIR/services/backend/Dockerfile $BACKUP_DIR/Dockerfile.backend.bak
cp $COMPOSE_DIR/services/socketio/entrypoint.sh $BACKUP_DIR/entrypoint.socketio.bak
echo "Backups en $BACKUP_DIR"

tg_notify "✅ *ERPv15 T2* — Backups creados en ${BACKUP_DIR}"
```

---

### T3 — Fix Bug 1: Dockerfile backend (brace expansion → mkdir separados)

```bash
# Ver línea actual problemática
grep -n "mkdir\|useradd" $COMPOSE_DIR/services/backend/Dockerfile

# Verificar el directorio malo que se creó (confirmar el bug)
docker run --rm docker-backend:latest bash -c "ls -la /home/frappe/frappe-bench/" 2>&1
```

Editar el Dockerfile. Reemplazar la sección `useradd` + `mkdir`:

```bash
# Reemplazar en el Dockerfile
# DE:
#   && mkdir -p /home/frappe/frappe-bench/{sites,logs,apps,config/pids} \
# A:
#   && mkdir -p /home/frappe/frappe-bench/sites \
#   && mkdir -p /home/frappe/frappe-bench/logs \
#   && mkdir -p /home/frappe/frappe-bench/apps \
#   && mkdir -p /home/frappe/frappe-bench/config/pids \

# Hacer el reemplazo con sed (ajustar si la línea exacta difiere):
sed -i 's|mkdir -p /home/frappe/frappe-bench/{sites,logs,apps,config/pids}|mkdir -p /home/frappe/frappe-bench/sites \&\& mkdir -p /home/frappe/frappe-bench/logs \&\& mkdir -p /home/frappe/frappe-bench/apps \&\& mkdir -p /home/frappe/frappe-bench/config/pids|g' \
    $COMPOSE_DIR/services/backend/Dockerfile
```

Si sed no funciona por escaping complejo, usar `nano` o `python3` para editar:

```bash
python3 -c "
content = open('$COMPOSE_DIR/services/backend/Dockerfile').read()
old = '    && mkdir -p /home/frappe/frappe-bench/{sites,logs,apps,config/pids} \\\\'
new = '''    && mkdir -p /home/frappe/frappe-bench/sites \\\\
    && mkdir -p /home/frappe/frappe-bench/logs \\\\
    && mkdir -p /home/frappe/frappe-bench/apps \\\\
    && mkdir -p /home/frappe/frappe-bench/config/pids \\\\'''
print('OLD encontrado:', old in content)
content = content.replace(old, new)
open('$COMPOSE_DIR/services/backend/Dockerfile', 'w').write(content)
print('Archivo guardado')
"

# Verificar resultado
grep -A5 -B2 "mkdir" $COMPOSE_DIR/services/backend/Dockerfile
```

```bash
tg_notify "✅ *ERPv15 T3* — Dockerfile backend corregido (mkdir separados)"
```

---

### T4 — Fix Bug 2: socketio/entrypoint.sh (redis-socket → redis-queue)

```bash
# Ver línea actual
grep -n "redis" $COMPOSE_DIR/services/socketio/entrypoint.sh

# Fix: cambiar redis-socket:11000 por redis-queue:6379
sed -i 's/redis-socket.*11000/redis-queue" -p 6379/g' $COMPOSE_DIR/services/socketio/entrypoint.sh

# Verificar
grep -n "redis" $COMPOSE_DIR/services/socketio/entrypoint.sh
```

Si sed no funciona exactamente:
```bash
python3 -c "
content = open('$COMPOSE_DIR/services/socketio/entrypoint.sh').read()
old = 'redis-cli -h \"redis-socket\" -p 11000'
new = 'redis-cli -h \"redis-queue\" -p 6379'
print('OLD encontrado:', old in content)
content = content.replace(old, new)
open('$COMPOSE_DIR/services/socketio/entrypoint.sh', 'w').write(content)
print('Archivo guardado')
"

grep -n "redis" $COMPOSE_DIR/services/socketio/entrypoint.sh
tg_notify "✅ *ERPv15 T4* — socketio/entrypoint.sh corregido (redis-queue:6379)"
```

---

### T5 — Reconstruir imágenes docker-backend y docker-socketio

```bash
cd $COMPOSE_DIR

# Reconstruir backend (sin cache para que aplique el fix del Dockerfile)
docker build --no-cache -t docker-backend:latest -f services/backend/Dockerfile services/backend/ 2>&1
BUILD_BACKEND_EXIT=$?

if [ $BUILD_BACKEND_EXIT -eq 0 ]; then
  tg_notify "✅ *ERPv15 T5a* — docker-backend reconstruido OK"
else
  tg_notify "❌ *ERPv15 T5a* — Build docker-backend FALLÓ (exit ${BUILD_BACKEND_EXIT})"
fi

# Verificar que apps/ existe correctamente en la nueva imagen
docker run --rm docker-backend:latest bash -c "ls -la /home/frappe/frappe-bench/" 2>&1
APPS_OK=$(docker run --rm docker-backend:latest bash -c "[ -d /home/frappe/frappe-bench/apps ] && echo SI || echo NO")
echo "apps/ existe: $APPS_OK"

# Reconstruir socketio
docker build --no-cache -t docker-socketio:latest -f services/socketio/Dockerfile services/socketio/ 2>&1
BUILD_SOCKET_EXIT=$?

if [ $BUILD_SOCKET_EXIT -eq 0 ]; then
  tg_notify "✅ *ERPv15 T5b* — docker-socketio reconstruido OK\napps/ en imagen: ${APPS_OK}"
else
  tg_notify "❌ *ERPv15 T5b* — Build docker-socketio FALLÓ (exit ${BUILD_SOCKET_EXIT})"
fi
```

---

### T6 — Verificar que frappe/erpnext están instalados en la imagen

```bash
# Verificar si las apps están en la imagen o si hay que instalarlas
docker run --rm docker-backend:latest bash -c "
ls /home/frappe/frappe-bench/apps/ 2>/dev/null || echo 'apps/ vacío o no existe'
" 2>&1

FRAPPE_OK=$(docker run --rm docker-backend:latest bash -c "[ -d /home/frappe/frappe-bench/apps/frappe ] && echo SI || echo NO")
ERPNEXT_OK=$(docker run --rm docker-backend:latest bash -c "[ -d /home/frappe/frappe-bench/apps/erpnext ] && echo SI || echo NO")
echo "frappe instalado: $FRAPPE_OK"
echo "erpnext instalado: $ERPNEXT_OK"
```

**Si frappe/erpnext NO están instalados** en la imagen → documentar y no continuar con T7. El Dockerfile necesita un `RUN bench get-app frappe` adicional. Notificar a Frank antes de proceder.

**Si frappe/erpnext SÍ están instalados** → continuar a T7.

```bash
tg_notify "✅ *ERPv15 T6* — Apps en imagen\nfrappe: ${FRAPPE_OK}\nerpnext: ${ERPNEXT_OK}"
```

---

### T7 — Levantar stack completo (solo si T5 y T6 exitosos)

```bash
cd $COMPOSE_DIR

# Bajar contenedores sin borrar volúmenes
docker-compose down --remove-orphans

# Levantar todo
docker-compose up -d 2>&1
sleep 20

# Estado
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Logs críticos
docker logs erpnext-websocket 2>&1 | tail -20
docker logs erpnext-nginx-proxy 2>&1 | tail -15
docker logs erpnext-backend 2>&1 | tail -15

UP_COUNT=$(docker ps --filter "name=erpnext" --filter "status=running" | grep -c erpnext)
tg_notify "✅ *ERPv15 T7* — Stack levantado\nContenedores running: ${UP_COUNT}"
```

---

### T8 — Verificar respuesta HTTP

```bash
sleep 30  # Dar tiempo a que nginx inicie

HTTP_LOCAL=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)
HTTPS_DOMAIN=$(curl -sk -o /dev/null -w "%{http_code}" https://erp15docker.shalomcontrol.com 2>/dev/null)

echo "HTTP localhost: $HTTP_LOCAL"
echo "HTTPS dominio: $HTTPS_DOMAIN"

tg_notify "🏁 *ERPv15 003 TERMINÓ*
HTTP local: ${HTTP_LOCAL}
HTTPS dominio: ${HTTPS_DOMAIN}
Ver: c:\\dev\\erpv15\\fix-dockerfile-results.md"
```

Código esperado: `200` o `302` (redirect login). Cualquier 5xx o 000 = bloqueador, documentar.

---

## Archivo de salida

**Crear/actualizar después de CADA tarea:**
```
c:\dev\erpv15\fix-dockerfile-results.md
```

### Estructura obligatoria

```markdown
# Fix Dockerfile ERPNext v15 — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T0. Conectado, COMPOSE_DIR | ✅/❌ | ruta: |
| T1. Logs websocket capturados | ✅/❌ | error: |
| T2. Backups creados | ✅/❌ | ruta backup: |
| T3. Dockerfile backend corregido | ✅/❌ | |
| T4. socketio entrypoint corregido | ✅/❌ | |
| T5. Imágenes reconstruidas | ✅/❌ | backend: OK/FAIL, socketio: OK/FAIL |
| T6. Apps en imagen | ✅/❌ | frappe: sí/no, erpnext: sí/no |
| T7. Stack levantado | ✅/❌ | contenedores Up: |
| T8. Web responde | ✅/❌ | HTTP local: , HTTPS dominio: |

## Logs websocket (antes del fix)
[output completo de docker logs erpnext-websocket]

## Inspección imagen post-build
[output de ls /home/frappe/frappe-bench/ en nueva imagen]
[apps encontradas: frappe, erpnext, otros]

## Estado final contenedores
[docker ps -a output]

## Respuesta HTTP final
- localhost:80: HTTP [code]
- erp15docker.shalomcontrol.com: HTTP [code]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
> - Error exacto: [copiar mensaje]
> - Alternativas intentadas:
> - Qué se necesita para resolver:
```
