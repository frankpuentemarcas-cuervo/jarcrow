---
fecha: 2026-04-25
agente_id: "005"
descripcion: fix-nginx-puertos-acceso-externo
proyecto: ERPNext-v15
ia_destino: antigravity
tipo: debug
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\erpv15\\fix-nginx-puertos-results.md"
dependencia: "004 (stack restaurado, HTTP 200 en localhost, ERR_CONNECTION_REFUSED desde exterior)"
---

# Fix Nginx — Acceso Externo ERPNext v15

## Contexto para el agente

Proyecto ERPNext v15 Docker (Overskull para Shalom). Stack restaurado exitosamente en el prompt 004. Desde dentro del servidor `curl http://localhost` retorna HTTP 200. Pero desde navegador externo `erp15docker.shalomcontrol.com` da `ERR_CONNECTION_REFUSED`.

**Causas probables a investigar en orden:**
1. `erpnext-nginx` no expone puertos 80/443 al host (falta `ports:` en docker-compose)
2. Firewall del servidor (ufw/iptables) bloquea puerto 80 o 443
3. DNS de `erp15docker.shalomcontrol.com` apunta a IP distinta a `178.128.181.196`

### Servidor

| Campo | Valor |
|---|---|
| IP | 178.128.181.196 |
| Usuario SSH | root |
| Llave SSH | `c:\dev\erpv15\id_rsa_deploy` |
| Compose activo | `/home/erpnext/erpnext-stack/docker/docker-compose.yml` |
| Dominio | erp15docker.shalomcontrol.com |

### Estado post-004

| Contenedor | Estado |
|---|---|
| erpnext-nginx | Up (healthy) ✅ |
| erpnext-backend | Up (healthy) ✅ |
| erpnext-socketio | Restarting (1) ❌ — no crítico para HTTP |
| erpnext-database | Up (healthy) ✅ |

---

## ⚠️ REGLA CRÍTICA — Reporte completo obligatorio

1. Generar o actualizar `c:\dev\erpv15\fix-nginx-puertos-results.md` después de CADA tarea
2. Documentar CADA paso: resultado (✅/❌), output exacto, error completo si falló
3. Nunca terminar sin el archivo de salida
4. Si un paso falla → documentar → continuar con el siguiente

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

**Inicio — conectar al servidor:**

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

COMPOSE_DIR=/home/erpnext/erpnext-stack/docker
tg_notify "✅ *ERPv15 005 T0* — Conectado al servidor"
```

---

### T1 — Verificar qué puertos expone nginx al host

```bash
# Ver puertos mapeados del contenedor nginx
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep nginx

# Ver sección ports en docker-compose.yml
grep -A 10 "nginx:" $COMPOSE_DIR/docker-compose.yml | grep -A5 "ports:"

# Ver si algo escucha en 80/443 en el host
ss -tlnp | grep -E ':80|:443'
netstat -tlnp 2>/dev/null | grep -E ':80|:443' || echo "netstat no disponible"

tg_notify "✅ *ERPv15 005 T1* — Puertos verificados\nNginx ports: $(docker ps --format '{{.Ports}}' --filter name=erpnext-nginx)"
```

**Si nginx NO tiene `0.0.0.0:80->80/tcp` y `0.0.0.0:443->443/tcp`** → el problema es la config del compose. Continuar a T2.

**Si nginx SÍ tiene los puertos mapeados** → el problema es firewall o DNS. Saltar a T3.

---

### T2 — Agregar ports al servicio nginx en docker-compose.yml

```bash
# Ver sección completa del servicio nginx
grep -n "" $COMPOSE_DIR/docker-compose.yml | grep -A 30 "nginx:"

# Verificar si ya tiene ports definidos
grep -c "ports:" $COMPOSE_DIR/docker-compose.yml
```

Si no tiene `ports:` en el servicio nginx, agregar:

```bash
# Backup antes de modificar
cp $COMPOSE_DIR/docker-compose.yml $COMPOSE_DIR/docker-compose.yml.bak-005

# Agregar ports con python3 (más seguro que sed para YAML)
python3 << 'PYEOF'
with open('/home/erpnext/erpnext-stack/docker/docker-compose.yml', 'r') as f:
    content = f.read()

# Buscar el servicio nginx y agregar ports si no existen
# Insertar después de la línea que tiene "image: docker-nginx" o "image: erpnext-nginx"
import re

# Patrón: encontrar servicio nginx sin ports
if '80:80' not in content:
    # Insertar ports después de la definición image del nginx
    # Busca la línea de imagen nginx y agrega ports debajo
    content = re.sub(
        r'(  nginx:\n(?:.*\n)*?    image: [^\n]+\n)',
        r'\1    ports:\n      - "80:80"\n      - "443:443"\n',
        content
    )
    with open('/home/erpnext/erpnext-stack/docker/docker-compose.yml', 'w') as f:
        f.write(content)
    print("ports agregados al servicio nginx")
else:
    print("ports 80:80 ya existe en docker-compose.yml — revisar manualmente")
PYEOF

# Verificar resultado
grep -A 20 "  nginx:" $COMPOSE_DIR/docker-compose.yml | head -25
```

Si el script no detecta correctamente el bloque nginx, editar manualmente con nano:

```bash
nano $COMPOSE_DIR/docker-compose.yml
# Buscar el servicio nginx y agregar bajo él:
#     ports:
#       - "80:80"
#       - "443:443"
```

```bash
tg_notify "✅ *ERPv15 005 T2* — docker-compose.yml modificado con ports 80/443"
```

---

### T3 — Verificar firewall del servidor

```bash
# ufw
ufw status verbose 2>/dev/null || echo "ufw no disponible"

# iptables
iptables -L INPUT -n --line-numbers 2>/dev/null | head -30

# Ver si Digital Ocean / proveedor tiene firewall externo
# (no se puede verificar desde el servidor — Frank debe revisar el panel)
curl -s --max-time 5 http://icanhazip.com || echo "sin acceso a internet desde servidor"

tg_notify "✅ *ERPv15 005 T3* — Firewall verificado\nufw: $(ufw status 2>/dev/null | head -1 || echo 'no ufw')"
```

Si ufw está activo y NO tiene reglas para 80/443:

```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload
ufw status verbose
tg_notify "✅ *ERPv15 005 T3b* — ufw: reglas 80/443 agregadas"
```

---

### T4 — Verificar DNS

```bash
# Desde el servidor, resolver el dominio
dig +short erp15docker.shalomcontrol.com 2>/dev/null || \
  nslookup erp15docker.shalomcontrol.com 2>/dev/null | grep Address || \
  host erp15docker.shalomcontrol.com 2>/dev/null

# IP real del servidor
curl -s http://icanhazip.com 2>/dev/null || ip addr show | grep "inet " | grep -v 127

tg_notify "✅ *ERPv15 005 T4* — DNS verificado\nDNS resuelve: $(dig +short erp15docker.shalomcontrol.com 2>/dev/null || echo 'dig no disponible')\nIP servidor: $(curl -s http://icanhazip.com 2>/dev/null)"
```

**Si DNS resuelve a IP distinta a la del servidor** → problema de DNS, no del stack. Documentar ambas IPs y notificar a Frank.

---

### T5 — Reiniciar nginx y probar acceso externo

```bash
cd $COMPOSE_DIR

# Si se modificó el compose en T2, recrear nginx
docker-compose up -d --force-recreate --no-deps nginx 2>&1
sleep 5

# Verificar puertos ahora
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep nginx
ss -tlnp | grep -E ':80|:443'

# Test desde el propio servidor hacia el dominio
HTTP_LOCAL=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)
HTTPS_LOCAL=$(curl -sk -o /dev/null -w "%{http_code}" https://localhost 2>/dev/null)
HTTP_DOMAIN=$(curl -sk --max-time 10 -o /dev/null -w "%{http_code}" https://erp15docker.shalomcontrol.com 2>/dev/null)

echo "HTTP localhost: $HTTP_LOCAL"
echo "HTTPS localhost: $HTTPS_LOCAL"
echo "HTTPS dominio: $HTTP_DOMAIN"

if [ "$HTTP_LOCAL" = "200" ] || [ "$HTTP_LOCAL" = "301" ] || [ "$HTTP_LOCAL" = "302" ]; then
  tg_notify "✅ *ERPv15 005 T5* — Nginx responde\nHTTP local: ${HTTP_LOCAL}\nHTTPS local: ${HTTPS_LOCAL}\nHTTPS dominio: ${HTTP_DOMAIN}"
else
  tg_notify "❌ *ERPv15 005 T5* — Nginx no responde\nHTTP local: ${HTTP_LOCAL}\nVer logs: docker logs erpnext-nginx"
fi
```

---

### T6 — Si nginx sigue sin responder: capturar logs completos

```bash
docker logs erpnext-nginx 2>&1 | tail -50
docker inspect erpnext-nginx 2>&1 | grep -A5 "Ports\|Status\|Error"

# Ver si el contenedor tiene el puerto interno correcto
docker exec erpnext-nginx sh -c "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null" || \
  docker exec erpnext-nginx curl -s http://localhost 2>/dev/null | head -5

tg_notify "🏁 *ERPv15 005 TERMINÓ*\nVer: c:\\dev\\erpv15\\fix-nginx-puertos-results.md"
```

---

## Archivo de salida

```
c:\dev\erpv15\fix-nginx-puertos-results.md
```

### Estructura obligatoria

```markdown
# Fix Nginx Puertos ERPNext v15 — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T0. Conectado | ✅/❌ | |
| T1. Puertos nginx verificados | ✅/❌ | ports mapeados: sí/no |
| T2. docker-compose ports agregados | ✅/❌/N-A | |
| T3. Firewall verificado | ✅/❌ | ufw status: |
| T4. DNS verificado | ✅/❌ | DNS IP: , Servidor IP: |
| T5. Nginx reiniciado + test | ✅/❌ | HTTP local: , HTTPS dominio: |
| T6. Logs nginx | ✅/❌/N-A | solo si T5 falló |

## Diagnóstico causa raíz

- **Causa identificada**: [ports faltantes / firewall / DNS]
- **Fix aplicado**: [descripción]

## Puertos nginx (docker ps output)
[output]

## Firewall status
[output de ufw status o iptables]

## DNS resolución
- DNS resuelve `erp15docker.shalomcontrol.com` a: [IP]
- IP real del servidor: [IP]
- ¿Coinciden?: sí/no

## Respuesta HTTP final
- localhost:80: HTTP [code]
- localhost:443: HTTP [code]
- erp15docker.shalomcontrol.com: HTTP [code]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo bien]
> - Error exacto:
> - Alternativas intentadas:
> - Qué se necesita:
```
