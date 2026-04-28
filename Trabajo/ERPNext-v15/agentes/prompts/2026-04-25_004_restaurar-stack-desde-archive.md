---
fecha: 2026-04-25
agente_id: "004"
descripcion: restaurar-stack-completo-desde-archivos-comprimidos
proyecto: ERPNext-v15
ia_destino: antigravity
tipo: deploy
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\erpv15\\restaurar-stack-results.md"
dependencia: "003 (Dockerfile/entrypoint corregidos, imagenes reconstruidas — stack aún caído)"
---

# Restaurar Stack ERPNext v15 desde Archivos Comprimidos

## Contexto para el agente

Proyecto ERPNext v15 Docker (Overskull para Shalom). Los prompts anteriores corrigieron bugs en el Dockerfile pero el stack sigue sin funcionar porque las imágenes no tienen las apps instaladas.

**Solución**: No reconstruir imágenes ni instalar apps. Ya existen archivos exportados del servidor original que contienen todo. El plan es subir esos archivos al servidor y reemplazar el stack completo.

### Servidor
| Campo | Valor |
|---|---|
| IP | 178.128.181.196 |
| Usuario SSH | root |
| Llave SSH | `c:\dev\erpv15\id_rsa_deploy` |
| Ruta proyecto actual en servidor | `/home/erpnext/docker/docker` |
| Dominio | erp15docker.shalomcontrol.com |

### Archivos locales disponibles (en `c:\dev\erpv15\`)
| Archivo | Tamaño | Contenido |
|---|---|---|
| `images-erpnext-custom.tar.gz` | 824MB | Imágenes Docker ya construidas con frappe/erpnext/hrms/payments/overskull instalados |
| `apps.tar.gz` | 74MB | Código fuente de todas las apps Frappe |
| `sites.tar.gz` | 1.3GB | Sites de Frappe (datos, assets, SSL certs) |
| `db-backup.sql.gz` | 8.7MB | Backup DB del 24 abril — **NO restaurar**, conservar DB actual del servidor |
| `docker-project.tar.gz` | 21KB | docker-compose.yml + Dockerfiles + configs + entrypoints + certs SSL |

### Stack del archive (reemplaza al actual)
- **3 Redis** con auth y puertos 11000 (socket), 11001 (queue), 13000 (cache)
- **Volúmenes bind mount** a `/home/erpnext/frappe-bench/{sites,apps,logs}`
- **Sin servicio configurator** — entrypoint.sh escribe `common_site_config.json` directamente
- **Apps montadas** desde `/home/erpnext/frappe-bench/apps` (extraído de `apps.tar.gz`)
- **Un solo nginx** con Dockerfile custom + SSL

### Variables de entorno del archive (`.env`)
```
SITE_NAME=erp15docker.shalomcontrol.com
DB_ROOT_PASSWORD=root_secure_pass_change_me
DB_NAME=_e239a52ab40e9524
DB_USER=_e239a52ab40e9524
DB_PASSWORD=3GpRgvLizMnAePr1
GUNICORN_WORKERS=9
REDIS_SOCKET_PASSWORD=Panz78TK_d7CXxM4wwRZbQDmWkJ26We46DMDay844ug
REDIS_QUEUE_PASSWORD=ixYrBhnPrzxM_wu7YNSztSZv8oc1nvNdhnavtzkexKc
REDIS_CACHE_PASSWORD=l_n-t2Am6fCAJR3I9LF-91E4MFNh7GnPDiHmEIBX4fQ
SHORT_WORKERS=4
DEFAULT_WORKERS=4
LONG_WORKERS=2
```

---

## ⚠️ REGLAS CRÍTICAS

- **NUNCA** `docker-compose down -v` — destruiría `vol-db-data` con la DB actual
- Backup del compose actual antes de reemplazar
- Actualizar `c:\dev\erpv15\restaurar-stack-results.md` después de CADA tarea

## 📲 Notificaciones Telegram

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

**Inicio — conectar y definir variables:**

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

COMPOSE_DIR=$(find / -name "docker-compose.yml" 2>/dev/null | grep -i erp | grep -v node_modules | head -1 | xargs dirname)
echo "COMPOSE_DIR: $COMPOSE_DIR"
tg_notify "✅ *ERPv15 T0* — Conectado\nCOMPOSE_DIR: ${COMPOSE_DIR}"
```

---

### T1 — Snapshot del estado actual y backup

```bash
# Estado actual
docker ps -a --format "table {{.Names}}\t{{.Status}}"

# Espacio disponible (necesitamos ~2.5GB libres)
df -h /

# Backup del compose actual
BACKUP_DIR="/home/erpnext/backup-pre-restore-$(date +%Y%m%d_%H%M)"
mkdir -p $BACKUP_DIR
cp -r $COMPOSE_DIR $BACKUP_DIR/
echo "Backup en $BACKUP_DIR"

# Verificar vol-db-data tiene datos (NO tocar)
docker volume inspect vol-db-data 2>/dev/null || docker volume ls | grep db

tg_notify "✅ *ERPv15 T1* — Backup creado: ${BACKUP_DIR}\nEspacio: $(df -h / | tail -1 | awk '{print $4}') libre"
```

---

### T2 — Bajar stack actual (SIN borrar volúmenes)

```bash
cd $COMPOSE_DIR

# Bajar sin -v para conservar vol-db-data
docker-compose down --remove-orphans 2>&1
docker ps -a | grep erpnext || echo "Stack bajado OK"

tg_notify "✅ *ERPv15 T2* — Stack bajado (vol-db-data conservado)"
```

---

### T3 — Subir archivos comprimidos al servidor

Desde la máquina local, subir los 3 archivos. Ejecutar estos comandos en la terminal LOCAL (no en el servidor):

```bash
# Subir en este orden (de menor a mayor tamaño)
scp -i c:\dev\erpv15\id_rsa_deploy c:\dev\erpv15\docker-project.tar.gz root@178.128.181.196:/home/erpnext/
scp -i c:\dev\erpv15\id_rsa_deploy c:\dev\erpv15\apps.tar.gz root@178.128.181.196:/home/erpnext/
scp -i c:\dev\erpv15\id_rsa_deploy c:\dev\erpv15\sites.tar.gz root@178.128.181.196:/home/erpnext/
scp -i c:\dev\erpv15\id_rsa_deploy c:\dev\erpv15\images-erpnext-custom.tar.gz root@178.128.181.196:/home/erpnext/
```

Verificar que llegaron:
```bash
# De vuelta en el servidor:
ls -lh /home/erpnext/*.tar.gz
```

```bash
tg_notify "✅ *ERPv15 T3* — Archivos subidos al servidor\n$(ls -lh /home/erpnext/*.tar.gz | awk '{print $5, $9}' | tr '\n' ' ')"
```

---

### T4 — Crear estructura de directorios y extraer apps + sites

```bash
# Crear estructura que usará el compose como bind mount
mkdir -p /home/erpnext/frappe-bench/{sites,apps,logs}

# Extraer apps.tar.gz → /home/erpnext/frappe-bench/apps/
echo "Extrayendo apps (~74MB)..."
tar xzf /home/erpnext/apps.tar.gz -C /home/erpnext/frappe-bench/
echo "Apps extraídas:"
ls /home/erpnext/frappe-bench/apps/

# Extraer sites.tar.gz → /home/erpnext/frappe-bench/sites/
echo "Extrayendo sites (~1.3GB, puede tardar 3-5 min)..."
tar xzf /home/erpnext/sites.tar.gz -C /home/erpnext/frappe-bench/
echo "Sites extraídos:"
ls /home/erpnext/frappe-bench/sites/

# Permisos correctos
chown -R 1000:1000 /home/erpnext/frappe-bench/ 2>/dev/null || true

APPS_COUNT=$(ls /home/erpnext/frappe-bench/apps/ | wc -l)
SITE_EXISTS=$([ -d "/home/erpnext/frappe-bench/sites/erp15docker.shalomcontrol.com" ] && echo "SI" || echo "NO")
tg_notify "✅ *ERPv15 T4* — Apps y sites extraídos\nApps: ${APPS_COUNT}\nSite existe: ${SITE_EXISTS}"
```

---

### T5 — Extraer y desplegar docker-compose del archive

```bash
# Extraer docker-project.tar.gz en /home/erpnext/erpnext-stack/
mkdir -p /home/erpnext/erpnext-stack
tar xzf /home/erpnext/docker-project.tar.gz -C /home/erpnext/erpnext-stack/
ls /home/erpnext/erpnext-stack/docker/

# Usar el .env del archive (tiene todos los passwords Redis correctos)
cp /home/erpnext/erpnext-stack/docker/.env /home/erpnext/erpnext-stack/docker/.env.original
# El .env ya tiene los valores correctos — verificar SITE_NAME
grep SITE_NAME /home/erpnext/erpnext-stack/docker/.env

# Verificar que los certs SSL están en el archive (fallback self-signed)
ls /home/erpnext/erpnext-stack/docker/services/nginx/certs/

# Verificar si el servidor tiene Let's Encrypt
ls /etc/letsencrypt/live/erp15docker.shalomcontrol.com/ 2>/dev/null && echo "LetsEncrypt: SI" || echo "LetsEncrypt: NO — usará certs del archive"
```

**Si NO hay Let's Encrypt**, modificar nginx.conf para usar los certs del archive:

```bash
# Verificar qué ruta usa nginx.conf
grep ssl_certificate /home/erpnext/erpnext-stack/docker/services/nginx/nginx.conf

# Si apunta a /etc/letsencrypt y no hay certs, cambiar a certs del archive:
sed -i 's|/etc/letsencrypt/live/erp15docker.shalomcontrol.com/fullchain.pem|/etc/nginx/certs/erp15docker.shalomcontrol.com.crt|g' \
    /home/erpnext/erpnext-stack/docker/services/nginx/nginx.conf
sed -i 's|/etc/letsencrypt/live/erp15docker.shalomcontrol.com/privkey.pem|/etc/nginx/certs/erp15docker.shalomcontrol.com.key|g' \
    /home/erpnext/erpnext-stack/docker/services/nginx/nginx.conf
echo "nginx.conf actualizado para usar certs del archive"
```

```bash
tg_notify "✅ *ERPv15 T5* — docker-compose desplegado en /home/erpnext/erpnext-stack/"
```

---

### T6 — Cargar imágenes Docker del archive

```bash
echo "Cargando imágenes (~824MB, puede tardar 3-5 min)..."
docker load < /home/erpnext/images-erpnext-custom.tar.gz 2>&1
echo "Imágenes cargadas:"
docker images | grep -v "<none>" | head -20

# Verificar que las imágenes esperadas por el compose existen
# El compose usa build: (construye desde Dockerfile) — verificar qué imágenes están disponibles
docker images --format "{{.Repository}}:{{.Tag}}" | sort
```

**Nota importante**: el docker-compose del archive usa `build:` para backend/nginx/socketio. Si las imágenes del archive tienen nombres distintos (ej. `docker-backend:latest`), actualizar el compose para usar `image:` en lugar de `build:`:

```bash
# Ver qué imágenes cargó el tar
LOADED_IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -v "^redis\|^mariadb\|^nginx\|^node\|^python\|^<none>")
echo "Imágenes custom cargadas:"
echo "$LOADED_IMAGES"

# Si hay imágenes tipo docker-backend:latest, docker-socketio:latest, etc.:
# Editar docker-compose.yml para reemplazar build: por image: en backend, nginx, socketio, worker-*, scheduler
# Ejemplo para backend:
# build:
#   context: ./services/backend
# →
# image: docker-backend:latest
```

Si las imágenes tienen nombres correctos, editar el compose en masa:

```bash
cd /home/erpnext/erpnext-stack/docker

# Ver nombres exactos de imágenes cargadas
docker images --format "table {{.Repository}}\t{{.Tag}}" | grep -v "^REPOSITORY\|redis\|mariadb\|^nginx\|node\|python"

# Para cada servicio que tenga build:, reemplazar por la imagen correspondiente
# (ajustar nombres según lo que reporte docker images)
# Ejemplo si las imágenes son docker-backend, docker-nginx, docker-socketio:
python3 << 'PYEOF'
import re

with open('docker-compose.yml', 'r') as f:
    content = f.read()

# Reemplazar build: blocks por image: para servicios conocidos
replacements = [
    # backend y workers: build context ./services/backend → image docker-backend:latest
    (r'    build:\n      context: \./services/backend\n      dockerfile: Dockerfile\n      args:\n        FRAPPE_BRANCH: version-16\n', 
     '    image: docker-backend:latest\n'),
    # nginx: build context ./services/nginx → image docker-nginx:latest
    (r'    build:\n      context: \./services/nginx\n      dockerfile: Dockerfile\n', 
     '    image: docker-nginx:latest\n'),
    # socketio: build context ./services/socketio → image docker-socketio:latest
    (r'    build:\n      context: \./services/socketio\n      dockerfile: Dockerfile\n', 
     '    image: docker-socketio:latest\n'),
]

for pattern, replacement in replacements:
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        print(f"Reemplazado: {pattern[:50]}...")
        content = new_content

with open('docker-compose.yml', 'w') as f:
    f.write(content)

print("docker-compose.yml actualizado")
PYEOF
```

Verificar resultado:
```bash
grep -A2 "image:\|build:" docker-compose.yml | head -40
tg_notify "✅ *ERPv15 T6* — Imágenes cargadas\n$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -v 'redis\|mariadb\|node\|python\|nginx:' | tr '\n' ' ')"
```

---

### T7 — Migrar vol-db-data al nuevo stack

El stack del archive usa un nuevo `vol-db-data` Docker. Hay que mover los datos de la DB actual:

```bash
# Ver cómo se llama el volumen actual con datos
docker volume ls | grep db
OLD_VOL=$(docker volume ls -q | grep db | head -1)
echo "Volumen DB actual: $OLD_VOL"

# Montar ambos volúmenes y copiar datos
# Si el volumen se llama igual (vol-db-data), el nuevo compose lo usará automáticamente
# Verificar:
docker volume inspect $OLD_VOL 2>/dev/null | grep -E "Name|Mountpoint"

# Si el nombre coincide con "vol-db-data", no hay que hacer nada — el compose lo reutiliza
# Si el nombre difiere, copiar con:
# docker run --rm -v $OLD_VOL:/from -v vol-db-data:/to alpine sh -c "cp -av /from/. /to/"
```

```bash
tg_notify "✅ *ERPv15 T7* — DB migrada\nVolumen: ${OLD_VOL}"
```

---

### T8 — Levantar el nuevo stack

```bash
cd /home/erpnext/erpnext-stack/docker

# Descargar imágenes oficiales si no están
docker pull redis:7.0.15-alpine 2>/dev/null || true
docker pull mariadb:10.11.13 2>/dev/null || true

# Levantar
docker-compose up -d 2>&1
sleep 30

# Estado
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

UP_COUNT=$(docker ps --filter "name=erpnext" --filter "status=running" | grep -c erpnext || true)
tg_notify "✅ *ERPv15 T8* — Stack levantado\nContenedores Up: ${UP_COUNT}"
```

---

### T9 — Verificar logs y respuesta HTTP

```bash
cd /home/erpnext/erpnext-stack/docker

# Logs backend (esperar inicialización virtualenv ~2 min en primer arranque)
echo "Esperando inicialización (60s)..."
sleep 60
docker logs erpnext-backend 2>&1 | tail -30
docker logs erpnext-socketio 2>&1 | tail -20
docker logs erpnext-nginx 2>&1 | tail -15

# Test HTTP
HTTP_LOCAL=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)
HTTPS_DOMAIN=$(curl -sk -o /dev/null -w "%{http_code}" https://erp15docker.shalomcontrol.com 2>/dev/null)
echo "HTTP localhost: $HTTP_LOCAL"
echo "HTTPS dominio: $HTTPS_DOMAIN"

tg_notify "🏁 *ERPv15 004 TERMINÓ*
HTTP local: ${HTTP_LOCAL}
HTTPS dominio: ${HTTPS_DOMAIN}
Ver: c:\\dev\\erpv15\\restaurar-stack-results.md"
```

Código esperado: `200` o `302`. Si `000` o `5xx` → documentar logs completos del backend.

---

## Archivo de salida

**Crear/actualizar después de CADA tarea:**
```
c:\dev\erpv15\restaurar-stack-results.md
```

### Estructura obligatoria

```markdown
# Restaurar Stack ERPNext v15 — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T0. Conectado | ✅/❌ | COMPOSE_DIR: |
| T1. Backup + snapshot | ✅/❌ | backup en: |
| T2. Stack bajado | ✅/❌ | vol-db-data conservado: sí/no |
| T3. Archivos subidos | ✅/❌ | tamaños verificados: |
| T4. Apps + sites extraídos | ✅/❌ | apps: N, site existe: sí/no |
| T5. docker-compose desplegado | ✅/❌ | ruta: /home/erpnext/erpnext-stack/ |
| T6. Imágenes cargadas | ✅/❌ | imágenes: [lista] |
| T7. DB migrada | ✅/❌ | volumen: |
| T8. Stack levantado | ✅/❌ | contenedores Up: N |
| T9. Web responde | ✅/❌ | HTTP: , HTTPS: |

## Imágenes Docker cargadas
[output de docker images]

## Estado final contenedores
[docker ps -a output]

## Logs backend (últimas 30 líneas)
[output]

## Respuesta HTTP
- localhost:80: HTTP [code]
- erp15docker.shalomcontrol.com: HTTP [code]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo bien, detallado si hubo problemas]
> - Error exacto:
> - Alternativas intentadas:
> - Qué se necesita:
```
