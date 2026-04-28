---
fecha: 2026-04-25
agente_id: "008"
descripcion: configurar-nginx-ssl-dominio
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: completado
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\nginx-ssl-results.md"
dependencia: "007 (Frappe levantando correctamente en :8000)"
---

# Configurar Nginx + SSL para cdtalleres-copia.shalom.com.pe

## Contexto para el agente

Proyecto CDTalleres (ERPNext v13.9.2 / Frappe 13.9.1 para Shalom / Overskull). Frappe ya está corriendo en el servidor Frontend/App (209.38.75.235). Hay que configurar Nginx como reverse proxy para el dominio `cdtalleres-copia.shalom.com.pe` con SSL (Let's Encrypt).

### Infraestructura

| Servidor | IP | Rol |
|---|---|---|
| Frontend/App | 209.38.75.235 | **Aquí se trabaja** — Nginx + Frappe/Gunicorn |

- **Dominio**: `cdtalleres-copia.shalom.com.pe` → ya apunta a 209.38.75.235 (DNS configurado)
- **Bench path**: `/home/erpnext/frappe-bench`
- **Site Frappe**: `CDTALLERES`
- **Usuario bench**: `erpnext`
- **Gunicorn escucha en**: `localhost:8000` (o socket unix — verificar)
- **OS**: Ubuntu 20.04

### Servidores

| Rol | IP | Usuario | Password |
|---|---|---|---|
| Frontend/App | 209.38.75.235 | root | .Overskull2026.m |

---

## ⚠️ REGLA CRÍTICA — Reporte de bloqueos

**SIEMPRE, ante cualquier error, bloqueo o impedimento:**

1. Genera el archivo de salida con lo que tengas hasta ese momento
2. Documenta en `## Bloqueos y errores`: qué intentaste, error EXACTO, alternativas, qué se necesita
3. **Nunca termines sin generar el archivo de salida.** Aunque sea parcial.

---

## Tareas a ejecutar (en servidor 209.38.75.235)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235
```

### 1. Verificar estado actual de Nginx y cómo escucha Frappe

```bash
echo "=== CONFIG NGINX ACTUAL ==="
ls -la /etc/nginx/conf.d/ 2>/dev/null
ls -la /etc/nginx/sites-enabled/ 2>/dev/null
cat /etc/nginx/sites-enabled/frappe 2>/dev/null || cat /etc/nginx/conf.d/frappe.conf 2>/dev/null

echo "=== GUNICORN SOCKET/PORT ==="
ss -tlnp | grep -E "(8000|gunicorn)"
ls /home/erpnext/frappe-bench/config/*.conf 2>/dev/null
cat /home/erpnext/frappe-bench/config/supervisor.conf 2>/dev/null | grep -A 10 gunicorn

echo "=== NGINX STATUS ==="
nginx -t 2>&1
systemctl status nginx | head -10
```

### 2. Verificar que DNS resuelve correctamente

```bash
# Desde el servidor, verificar que el dominio apunta a él mismo
dig cdtalleres-copia.shalom.com.pe +short 2>/dev/null || nslookup cdtalleres-copia.shalom.com.pe 2>/dev/null
# Debe mostrar: 209.38.75.235

# Puerto 80 accesible desde afuera (UFW)
ufw status | grep -E "(80|443|Nginx)"
```

Si UFW está activo y no permite 80/443:
```bash
ufw allow 'Nginx Full'
ufw status
```

### 3. Regenerar config Nginx de Frappe con el dominio correcto

Frappe v13 usa `bench setup nginx` para generar la config:

```bash
cd /home/erpnext/frappe-bench

# Primero: agregar dominio al site
sudo -u erpnext bench --site CDTALLERES set-config host_name "cdtalleres-copia.shalom.com.pe"

# Regenerar config de nginx
sudo -u erpnext bench setup nginx 2>&1

# Ver qué generó
cat /home/erpnext/frappe-bench/config/nginx.conf 2>/dev/null | head -60
```

Si `bench setup nginx` genera el archivo en `config/nginx.conf`, linkearlo:

```bash
# Backup del config actual
cp /etc/nginx/conf.d/frappe.conf /etc/nginx/conf.d/frappe.conf.bak.$(date +%Y%m%d) 2>/dev/null
cp /etc/nginx/sites-enabled/frappe /etc/nginx/sites-enabled/frappe.bak.$(date +%Y%m%d) 2>/dev/null

# Linkear la nueva config generada por bench
ln -sf /home/erpnext/frappe-bench/config/nginx.conf /etc/nginx/conf.d/frappe-cdtalleres.conf 2>/dev/null

# Verificar sintaxis
nginx -t 2>&1
```

Si hay errores de sintaxis, documentarlos y NO recargar nginx.

### 4. Recargar Nginx (solo si nginx -t pasó)

```bash
systemctl reload nginx
systemctl status nginx | head -10

# Verificar respuesta HTTP (sin SSL aún)
curl -s -o /dev/null -w "HTTP %{http_code} - %{redirect_url}\n" http://cdtalleres-copia.shalom.com.pe
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://209.38.75.235
```

### 5. Instalar certbot y obtener certificado SSL

```bash
# Instalar certbot si no existe
which certbot 2>/dev/null || (apt-get update -qq && apt-get install -y certbot python3-certbot-nginx)

# Obtener certificado (modo no interactivo)
certbot --nginx \
  -d cdtalleres-copia.shalom.com.pe \
  --non-interactive \
  --agree-tos \
  --email erickm@overskull.pe \
  --redirect 2>&1

echo "Exit code: $?"
```

Si certbot falla, intentar modo standalone:
```bash
systemctl stop nginx
certbot certonly --standalone \
  -d cdtalleres-copia.shalom.com.pe \
  --non-interactive \
  --agree-tos \
  --email erickm@overskull.pe 2>&1
systemctl start nginx
```

### 6. Verificación final completa

```bash
echo "=== NGINX CONFIG TEST ==="
nginx -t 2>&1

echo "=== HTTP (debe redirigir a HTTPS) ==="
curl -s -o /dev/null -w "HTTP %{http_code} → %{redirect_url}\n" http://cdtalleres-copia.shalom.com.pe

echo "=== HTTPS ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://cdtalleres-copia.shalom.com.pe

echo "=== CERTIFICADO SSL ==="
echo | openssl s_client -connect cdtalleres-copia.shalom.com.pe:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null

echo "=== LOGS NGINX (últimas 20 líneas) ==="
tail -20 /var/log/nginx/error.log 2>/dev/null
```

---

## Archivo de salida

**Crear al terminar (aunque sea parcial):**
```
c:\dev\cdtalleres\nginx-ssl-results.md
```

### Estructura obligatoria

```markdown
# Nginx + SSL CDTalleres — YYYY-MM-DD HH:MM

## Verificación DNS
- cdtalleres-copia.shalom.com.pe resuelve a: [IP]
- DNS correcto: ✅/❌

## Cambios realizados

| Paso | Estado | Detalle |
|---|---|---|
| Config Nginx generada | ✅/❌ | ruta del archivo |
| Nginx recargado | ✅/❌ | |
| HTTP responde | ✅/❌ | HTTP code: |
| Certbot instalado | ✅/❌ | |
| Certificado SSL obtenido | ✅/❌ | válido hasta: |
| HTTPS responde | ✅/❌ | HTTP code: |
| HTTP redirige a HTTPS | ✅/❌ | |

## URL final
- http://cdtalleres-copia.shalom.com.pe → [resultado]
- https://cdtalleres-copia.shalom.com.pe → [resultado]

## Errores en logs Nginx
[tail de error.log]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
> - Error exacto:
> - Alternativas intentadas:
> - Qué se necesita:
```
