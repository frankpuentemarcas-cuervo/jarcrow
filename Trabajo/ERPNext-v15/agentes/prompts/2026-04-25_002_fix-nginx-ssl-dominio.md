---
fecha: 2026-04-25
agente_id: "002"
descripcion: fix-nginx-ssl-dominio
proyecto: ERPNext-v15
ia_destino: antigravity
tipo: ejecucion
estado: superado-por-002b
falla: ""
archivo_salida: "c:\\dev\\erpv15\\nginx-fix-results.md"
dependencia: "001 (diagnóstico confirmado)"
---

# Fix Nginx + SSL — Cambiar Dominio a erpv15-qatest.shalom.com.pe

## Contexto para el agente

Proyecto ERPNext v15 Docker (Overskull para Shalom). El nginx-proxy tiene `server_name erp15docker.shalomcontrol.com` (dominio viejo) y certificado SSL para ese dominio. El DNS activo es `erpv15-qatest.shalom.com.pe` → 178.128.181.196. Hay que: 1) generar certificado SSL para el nuevo dominio, 2) actualizar nginx.conf, 3) recargar nginx-proxy.

### Servidor

| Campo | Valor |
|---|---|
| IP | 178.128.181.196 |
| Usuario SSH | root |
| Llave SSH | `c:\dev\erpv15\id_rsa_deploy` |
| Dominio nuevo | `erpv15-qatest.shalom.com.pe` |
| Dominio viejo (en config actual) | `erp15docker.shalomcontrol.com` |

### Rutas clave en el servidor

- nginx.conf montado desde: buscar con `docker inspect erpnext-nginx-proxy`
- Certs montados desde: buscar con `docker inspect erpnext-nginx-proxy`
- Ruta proyecto docker-compose: buscar con `find / -name docker-compose.yml 2>/dev/null | grep erpnext`

---

## ⚠️ REGLA CRÍTICA — Reporte de bloqueos

**SIEMPRE, ante cualquier error, bloqueo o impedimento:**

1. Genera el archivo de salida con lo que tengas hasta ese momento
2. Documenta en `## Bloqueos y errores`: qué intentaste, error EXACTO, alternativas, qué se necesita
3. **Nunca termines sin generar el archivo de salida.** Aunque sea parcial.

---

## ⚠️ REGLA DE SEGURIDAD

- Backup de nginx.conf y certs ANTES de modificar
- Si nginx -t falla después del cambio, restaurar backup y NO recargar

---

## Tareas a ejecutar

Conectar:
```bash
ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no root@178.128.181.196
```

### 1. Localizar rutas reales de los archivos montados

```bash
# Encontrar docker-compose
find / -name "docker-compose.yml" 2>/dev/null | grep -i erp

# Inspect para ver bind mounts
docker inspect erpnext-nginx-proxy | grep -A5 '"Mounts"'
```

### 2. Backup de config actual

```bash
# Ajustar RUTA con lo encontrado en paso 1
NGINX_CONF="[RUTA_REAL]/services/nginx/nginx.conf"
CERTS_DIR="[RUTA_REAL]/services/nginx/certs"

cp "$NGINX_CONF" "${NGINX_CONF}.bak.$(date +%Y%m%d_%H%M)"
cp -r "$CERTS_DIR" "${CERTS_DIR}.bak.$(date +%Y%m%d_%H%M)"
echo "Backups OK"
```

### 3. Opción A — Certificado Let's Encrypt (recomendado)

```bash
# Instalar certbot si no existe
which certbot || (apt-get update -qq && apt-get install -y certbot)

# Detener temporalmente nginx-proxy para liberar puerto 80
docker stop erpnext-nginx-proxy

# Obtener certificado
certbot certonly --standalone \
  -d erpv15-qatest.shalom.com.pe \
  --non-interactive \
  --agree-tos \
  --email erickm@overskull.pe 2>&1

echo "Exit code certbot: $?"

# Copiar certs al directorio montado
cp /etc/letsencrypt/live/erpv15-qatest.shalom.com.pe/fullchain.pem "$CERTS_DIR/erpv15-qatest.shalom.com.pe.crt"
cp /etc/letsencrypt/live/erpv15-qatest.shalom.com.pe/privkey.pem "$CERTS_DIR/erpv15-qatest.shalom.com.pe.key"
ls -lh "$CERTS_DIR/"
```

Si certbot falla (DNS no propaga aún, etc.) → usar Opción B.

### Opción B — Certificado autofirmado (temporal)

```bash
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "$CERTS_DIR/erpv15-qatest.shalom.com.pe.key" \
  -out "$CERTS_DIR/erpv15-qatest.shalom.com.pe.crt" \
  -subj "/CN=erpv15-qatest.shalom.com.pe/O=Shalom/C=PE" 2>&1
echo "Cert autofirmado generado: $?"
```

### 4. Actualizar nginx.conf con nuevo dominio y certs

```bash
# Ver contenido actual
cat "$NGINX_CONF"

# Reemplazar dominio y rutas de certs
sed -i 's/erp15docker\.shalomcontrol\.com/erpv15-qatest.shalom.com.pe/g' "$NGINX_CONF"
sed -i 's|erp15docker\.shalomcontrol\.com\.crt|erpv15-qatest.shalom.com.pe.crt|g' "$NGINX_CONF"
sed -i 's|erp15docker\.shalomcontrol\.com\.key|erpv15-qatest.shalom.com.pe.key|g' "$NGINX_CONF"

# Verificar cambios
grep -E "(server_name|ssl_cert)" "$NGINX_CONF"
```

### 5. Recargar nginx-proxy

```bash
# Reiniciar contenedor (levanta con la config nueva)
docker start erpnext-nginx-proxy 2>/dev/null || docker restart erpnext-nginx-proxy
sleep 3

# Verificar nginx dentro del contenedor
docker exec erpnext-nginx-proxy nginx -t 2>&1
docker logs erpnext-nginx-proxy --tail 20 2>&1
```

### 6. Verificación final

```bash
# HTTP → debe redirigir a HTTPS
curl -sv http://erpv15-qatest.shalom.com.pe 2>&1 | grep -E "(HTTP|Location|< )"

# HTTPS → debe responder 200 o redirect a /login
curl -svk https://erpv15-qatest.shalom.com.pe 2>&1 | grep -E "(HTTP|< )" | head -10

# Verificar certificado
echo | openssl s_client -connect erpv15-qatest.shalom.com.pe:443 2>/dev/null | openssl x509 -noout -subject -dates 2>/dev/null
```

---

## Archivo de salida

**Crear al terminar (aunque sea parcial):**
```
c:\dev\erpv15\nginx-fix-results.md
```

### Estructura obligatoria

```markdown
# Fix Nginx SSL ERPNext v15 — YYYY-MM-DD HH:MM

## Rutas encontradas en servidor
- docker-compose.yml: [ruta]
- nginx.conf: [ruta]
- certs dir: [ruta]

## Certificado SSL
- Método usado: Let's Encrypt / Autofirmado
- Estado: ✅/❌
- Válido hasta: [fecha]

## Cambios en nginx.conf
- server_name anterior: erp15docker.shalomcontrol.com
- server_name nuevo: erpv15-qatest.shalom.com.pe
- ssl_certificate nuevo: [ruta]

## Verificación final

| Check | Resultado |
|---|---|
| nginx -t | ✅/❌ |
| HTTP http://erpv15-qatest.shalom.com.pe | HTTP code |
| HTTPS https://erpv15-qatest.shalom.com.pe | HTTP code |
| Certificado SSL válido | ✅/❌ |

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
