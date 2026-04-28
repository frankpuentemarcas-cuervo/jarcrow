---
fecha: 2026-04-25
agente_id: "002b"
descripcion: fix-configurator-arrancar-stack
proyecto: ERPNext-v15
ia_destino: antigravity
tipo: debug
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\erpv15\\fix-configurator-results.md"
dependencia: "001 (diagnóstico completado)"
---

# Fix Configurator + Arrancar Stack ERPNext v15 — CDTalleres

## Contexto para el agente

Proyecto ERPNext v15 Docker (Overskull para Shalom). Stack con imágenes Docker custom en producción.

**Problema raíz identificado**: El contenedor `erpnext-configurator` falla con exit 2. Esto bloquea el arranque de TODOS los contenedores de aplicación (backend, frontend, nginx-proxy, websocket, scheduler, queues) porque tienen `depends_on: configurator: condition: service_completed_successfully`.

**Errores del configurator:**
```
ls: cannot access 'apps': No such file or directory
WARN: Command not being executed in bench directory
Error: No such command 'set-config'.
```

**Causa probable**: El docker-compose.yml override el entrypoint con `["bash", "-c"]` y el command corre como root sin el contexto correcto de bench. Además, `apps/` puede estar vacío en la imagen o el directorio no existe como se espera.

**Dato adicional crítico**: El prompt anterior usó IP `178.128.181.196` pero el agente reportó que el servidor respondió SSH — verificar cuál IP es la que tiene el stack Docker activo (puede ser `104.248.66.66` si DNS cambió, o `178.128.181.196`).

### Servidor

| Campo | Valor |
|---|---|
| IP reportada en config local | 178.128.181.196 |
| IP alternativa a verificar | 104.248.66.66 |
| **Verificar primero** | cuál IP tiene el stack Docker activo |
| Usuario SSH | root |
| Llave SSH | `c:\dev\erpv15\id_rsa_deploy` (alternativa: password si la llave no funciona) |
| Dominio activo | erp15docker.shalomcontrol.com |

### Ruta del proyecto en servidor
Buscar con: `find / -name docker-compose.yml 2>/dev/null | grep -i erp | grep -v node_modules`

### Imágenes custom en uso

| Contenedor | Imagen |
|---|---|
| configurator, backend, queue-* | `docker-backend:latest` |
| websocket | `docker-socketio:latest` |
| frontend | `docker-nginx:latest` |
| scheduler | `docker-scheduler:latest` |

### Variables de entorno relevantes (`.env` local)

```
SITE_NAME=erp15docker.shalomcontrol.com
DB_NAME=_e239a52ab40e9524
DB_USER=_e239a52ab40e9524
DB_PASSWORD=3GpRgvLizMnAePr1
DB_ROOT_PASSWORD=root_secure_pass_change_me
```

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

**Generar o actualizar el archivo de salida después de CADA tarea completada o fallida.**

Ante cualquier situación — éxito, error, bloqueo o impedimento:
1. **Genera o actualiza el archivo de salida** inmediatamente con lo ejecutado
2. Documenta CADA tarea: resultado (✅/❌), output exacto del comando, error completo si falló
3. **Nunca termines sin el archivo de salida.** Aunque sea parcial.
4. Si una tarea falla, documentarla y **continuar con la siguiente** — no detenerse.

## 📲 Notificaciones Telegram — obligatorio después de CADA tarea

Definir la función al inicio y usarla después de cada tarea:

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

Formato de mensajes:
- Éxito: `tg_notify "✅ *ERPv15 T1* — Proyecto localizado\nRuta: /home/erpnext/docker"`
- Fallo: `tg_notify "❌ *ERPv15 T4* — Configurator fix falló\nError: \`bench: command not found\`"`
- Final: `tg_notify "🏁 *ERPv15 002b terminó*\nVer: c:\\dev\\erpv15\\fix-configurator-results.md"`

---

## ⚠️ REGLA DE SEGURIDAD

- Backup del `.env` y `docker-compose.yml` antes de modificar
- Nunca `docker-compose down -v` — destruiría `vol-db-data` con los datos

---

## Tareas a ejecutar

**Primero — definir función Telegram en el servidor (ejecutar una sola vez al conectar):**

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

### Paso 0. Verificar IP correcta del servidor

```bash
# Intentar las dos IPs — conectar a la que tenga Docker corriendo
ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@104.248.66.66 "docker ps | grep erpnext-database" 2>&1
ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@178.128.181.196 "docker ps | grep erpnext-database" 2>&1
```

Usar la IP que responda. Documentar cuál es la IP real.

**Todo el trabajo siguiente se hace en la IP que tenga el stack.**

Conectar y notificar:
```bash
ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no root@[IP_CORRECTA]
# (redefinir tg_notify en el servidor)
tg_notify "✅ *ERPv15 T0* — Servidor conectado\nIP: [IP_CORRECTA]"
```

---

### 1. Localizar el proyecto y verificar estado actual

```bash
find / -name "docker-compose.yml" 2>/dev/null | grep -i erp | grep -v node_modules
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
docker logs erpnext-configurator 2>&1

COMPOSE_DIR=$(find / -name "docker-compose.yml" 2>/dev/null | grep -i erp | grep -v node_modules | head -1 | xargs dirname)
tg_notify "✅ *ERPv15 T1* — Proyecto localizado\nRuta: ${COMPOSE_DIR}\nConfigurator exit: $(docker inspect erpnext-configurator --format='{{.State.ExitCode}}')"
```

Actualizar archivo de salida.

---

### 2. Inspeccionar la imagen docker-backend:latest

```bash
docker run --rm docker-backend:latest bash -c "
echo '=== WORKDIR ==='; pwd;
echo '=== ls -la ==='; ls -la;
echo '=== apps/ ==='; ls -la apps/ 2>/dev/null || echo 'apps/ NO EXISTE';
echo '=== bench version ==='; bench --version 2>/dev/null || echo 'bench no disponible';
echo '=== which bench ==='; which bench 2>/dev/null || echo 'bench no en PATH';
echo '=== whoami ==='; whoami;
" 2>&1

APPS_EXISTS=$(docker run --rm docker-backend:latest bash -c "ls apps/ 2>/dev/null | wc -l || echo 0")
BENCH_OK=$(docker run --rm docker-backend:latest bash -c "bench --version 2>/dev/null && echo SI || echo NO")
tg_notify "✅ *ERPv15 T2* — Imagen inspeccionada\napps/ items: ${APPS_EXISTS}\nbench disponible: ${BENCH_OK}"
```

Actualizar archivo de salida.

---

### 3. Verificar .env en el servidor

```bash
echo "Directorio: $COMPOSE_DIR"
cat "$COMPOSE_DIR/.env" 2>/dev/null || echo ".env no encontrado"

SITE=$(grep SITE_NAME $COMPOSE_DIR/.env | cut -d= -f2)
tg_notify "✅ *ERPv15 T3* — .env verificado\nSITE_NAME: ${SITE}"
```

Actualizar archivo de salida.

---

### 4. Corregir el configurator

```bash
cd $COMPOSE_DIR

# Backup
cp docker-compose.yml docker-compose.yml.bak.$(date +%Y%m%d_%H%M)
cp .env .env.bak.$(date +%Y%m%d_%H%M) 2>/dev/null
echo "Backup creado"

# Ver command actual
grep -A 20 "configurator:" docker-compose.yml | head -25
```

Editar docker-compose.yml — agregar `gosu frappe` antes de cada `bench` command y usar rutas absolutas para `ls -1 apps`:

```yaml
command:
  - >
    ls -1 /home/frappe/frappe-bench/apps > /home/frappe/frappe-bench/sites/apps.txt 2>/dev/null || echo "" > /home/frappe/frappe-bench/sites/apps.txt;
    gosu frappe bench set-config -g db_host $$DB_HOST;
    gosu frappe bench set-config -gp db_port $$DB_PORT;
    gosu frappe bench set-config -g redis_cache "redis://redis-cache:6379";
    gosu frappe bench set-config -g redis_queue "redis://redis-queue:6379";
    gosu frappe bench set-config -g redis_socketio "redis://redis-queue:6379";
    gosu frappe bench set-config -gp socketio_port $$SOCKETIO_PORT;
```

**IMPORTANTE**: Si `apps/` está vacío (resultado Paso 2), reemplazar `ls -1 ...` por `echo "" > /home/frappe/frappe-bench/sites/apps.txt`.

```bash
tg_notify "✅ *ERPv15 T4* — docker-compose.yml corregido\nBackup: docker-compose.yml.bak.*"
```

Actualizar archivo de salida.

---

### 5. Verificar SITE_NAME en .env (no modificar)

```bash
grep SITE_NAME $COMPOSE_DIR/.env
tg_notify "✅ *ERPv15 T5* — SITE_NAME confirmado: $(grep SITE_NAME $COMPOSE_DIR/.env)"
```

Actualizar archivo de salida.

---

### 6. Recrear solo el configurator y verificar que completa

```bash
cd $COMPOSE_DIR
docker-compose up --force-recreate --no-deps configurator 2>&1
EXIT_CODE=$?
docker ps -a | grep configurator
docker logs erpnext-configurator 2>&1 | tail -20

# Verificar common_site_config.json
docker run --rm -v $(docker volume inspect erpnext_vol-sites --format '{{.Mountpoint}}' 2>/dev/null || echo "/nonexistent"):/sites alpine cat /sites/common_site_config.json 2>/dev/null || echo "No se pudo leer vol-sites"

if [ $EXIT_CODE -eq 0 ]; then
  tg_notify "✅ *ERPv15 T6* — Configurator OK (exit 0)\ncommon_site_config.json generado"
else
  tg_notify "❌ *ERPv15 T6* — Configurator FALLÓ (exit ${EXIT_CODE})\nVer logs para error exacto"
fi
```

Si exit 0 → continuar. Si falla → documentar error exacto, notificar, y detenerse.

Actualizar archivo de salida.

---

### 7. Levantar el stack completo (solo si Paso 6 fue exitoso)

```bash
cd $COMPOSE_DIR
docker-compose up -d 2>&1
sleep 15

docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker logs erpnext-backend --tail 20 2>&1
docker logs erpnext-frontend --tail 10 2>&1
docker logs erpnext-nginx-proxy --tail 20 2>&1

UP_COUNT=$(docker ps --filter "name=erpnext" --filter "status=running" | grep -c erpnext)
tg_notify "✅ *ERPv15 T7* — Stack levantado\nContenedores running: ${UP_COUNT}/10"
```

Actualizar archivo de salida.

---

### 8. Verificar que la web responde (solo si Paso 7 exitoso)

```bash
HTTP_LOCAL=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)
HTTPS_LOCAL=$(curl -sk -o /dev/null -w "%{http_code}" https://localhost 2>/dev/null)
HTTP_DOMAIN=$(curl -sk -o /dev/null -w "%{http_code}" https://erp15docker.shalomcontrol.com 2>/dev/null)

echo "HTTP localhost: $HTTP_LOCAL"
echo "HTTPS localhost: $HTTPS_LOCAL"
echo "HTTPS dominio: $HTTP_DOMAIN"

tg_notify "🏁 *ERPv15 002b TERMINÓ*\nHTTP local: ${HTTP_LOCAL}\nHTTPS local: ${HTTPS_LOCAL}\nHTTPS dominio: ${HTTP_DOMAIN}\nVer: c:\\dev\\erpv15\\fix-configurator-results.md"
```

---

## Archivo de salida

**Crear o actualizar después de CADA tarea:**
```
c:\dev\erpv15\fix-configurator-results.md
```

### Estructura obligatoria

```markdown
# Fix Configurator ERPNext v15 — YYYY-MM-DD HH:MM

## IP real del servidor
- IP confirmada: [104.248.66.66 o 178.128.181.196]
- Cómo se verificó: [respuesta de docker ps]

## Estado tareas

| Tarea | Estado | Notas |
|---|---|---|
| 0. IP verificada | ✅/❌ | |
| 1. Proyecto localizado | ✅/❌ | ruta: |
| 2. Imagen inspeccionada | ✅/❌ | apps/ existe: sí/no |
| 3. .env verificado | ✅/❌ | SITE_NAME valor: |
| 4. Configurator corregido | ✅/❌ | |
| 5. SITE_NAME confirmado | ✅/❌ | valor: erp15docker.shalomcontrol.com |
| 6. Configurator corre exitoso | ✅/❌ | exit code: |
| 7. Stack levantado | ✅/❌ | contenedores Up: |
| 8. Web responde | ✅/❌ | HTTP codes: |

## Inspección de imagen (Tarea 2)
[output completo de docker run --rm docker-backend]

## Configurator logs antes/después
[logs del configurator antes de corrección]
[logs del configurator después de corrección]

## common_site_config.json generado
[contenido si se creó]

## Estado final de contenedores
[docker ps -a output]

## Respuesta HTTP
- localhost:80: HTTP [code]
- localhost:443: HTTP [code]
- erp15docker.shalomcontrol.com: HTTP [code]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
> - Error exacto: [copiar mensaje]
> - Alternativas intentadas:
> - Qué se necesita:
```
