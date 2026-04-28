---
fecha: 2026-04-25
agente_id: "019"
descripcion: configurar-red-privada-interna-ip-privada
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\red-privada-results.md"
dependencia: "ninguna — tarea independiente de optimización de red"
---

# Configurar Red Privada Interna — CDTalleres

## Contexto para el agente

Proyecto CDTalleres: ERPNext distribuido en 3 servidores DigitalOcean en la misma región. Actualmente la comunicación entre servidores usa IPs públicas, lo que agrega latencia innecesaria y costo de ancho de banda. DigitalOcean provee red privada entre droplets de la misma región.

**Objetivo**: Migrar toda la comunicación interna entre servidores a IPs privadas.

### Topología actual

| Rol | IP Pública | IP Privada |
|---|---|---|
| Frontend (Nginx + ERPNext app) | `209.38.75.235` | `10.124.0.10` |
| Backend (Gunicorn/Workers) | `164.92.94.47` | `10.124.0.9` |
| Base de datos (MariaDB) | `165.232.130.222` | `10.124.0.7` |

### Credenciales SSH

Todos los servidores: usuario `root`, password `.Overskull2026.m`

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@[IP]
```

### Bench / Site

- **Bench**: `/home/erpnext/frappe-bench`
- **Site**: `CDTALLERES`
- **DB name**: `_0646d69b639ad0ff`

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Generar o actualizar `c:\dev\cdtalleres\red-privada-results.md` después de CADA tarea
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

### T1 — Verificar conectividad entre servidores por IP privada

Desde el servidor frontend, hacer ping a las IPs privadas de backend y DB:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
echo "=== Ping a backend (10.124.0.9) ==="
ping -c 3 10.124.0.9 2>&1 || echo "FALLO"

echo "=== Ping a DB (10.124.0.7) ==="
ping -c 3 10.124.0.7 2>&1 || echo "FALLO"

echo "=== Interfaces de red ==="
ip addr show | grep "inet " | grep -v "127.0.0.1"
'
```

Desde el servidor backend, hacer ping a DB:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Ping a DB (10.124.0.7) ==="
ping -c 3 10.124.0.7 2>&1 || echo "FALLO"

echo "=== Interfaces de red ==="
ip addr show | grep "inet " | grep -v "127.0.0.1"
'
```

**Si ping falla** → la red privada de DigitalOcean no está habilitada en el droplet. Documentar y notificar a Frank — debe habilitarla desde el panel (Networking → Enable Private Networking en el droplet). No continuar hasta que ping funcione.

```bash
tg_notify "✅ *CDT 019 T1* — Conectividad privada verificada\nFrontend→Backend: OK\nFrontend→DB: OK\nBackend→DB: OK"
```

---

### T2 — Auditar configuraciones actuales con IPs públicas

Identificar todos los archivos que referencian IPs públicas en los 3 servidores.

**En el servidor Frontend:**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

echo "=== common_site_config.json ==="
cat $BENCH/sites/common_site_config.json 2>/dev/null || echo "no existe"

echo "=== site_config.json ==="
cat $BENCH/sites/$SITE/site_config.json 2>/dev/null || echo "no existe"

echo "=== /etc/hosts ==="
cat /etc/hosts

echo "=== supervisord configs ==="
grep -r "146.190\|164.92\|209.38" /etc/supervisor/ 2>/dev/null || echo "sin referencias en supervisor"

echo "=== nginx configs ==="
grep -r "146.190\|164.92\|209.38" /etc/nginx/ 2>/dev/null || echo "sin referencias en nginx"

echo "=== Referencias a IPs públicas en bench ==="
grep -r "146.190\|164.92\|209.38" $BENCH/sites/ 2>/dev/null | grep -v ".pyc" | grep -v "Binary" || echo "ninguna"
'
```

**En el servidor Backend:**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

echo "=== common_site_config.json ==="
cat $BENCH/sites/common_site_config.json 2>/dev/null || echo "no existe"

echo "=== site_config.json ==="
cat $BENCH/sites/$SITE/site_config.json 2>/dev/null || echo "no existe"

echo "=== /etc/hosts ==="
cat /etc/hosts

echo "=== Referencias a IPs públicas ==="
grep -r "146.190\|164.92\|209.38" $BENCH/sites/ 2>/dev/null | grep -v ".pyc" | grep -v "Binary" || echo "ninguna"
'
```

**En el servidor DB:**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== /etc/mysql/mariadb.conf.d/ ==="
grep -r "bind-address\|146.190\|164.92\|209.38" /etc/mysql/ 2>/dev/null || echo "sin referencias"

echo "=== /etc/hosts ==="
cat /etc/hosts

echo "=== MariaDB bind-address actual ==="
mysql -u root -p".Overskull2026.m" -e "SHOW VARIABLES LIKE '"'"'bind_address'"'"';" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 019 T2* — Auditoría de IPs públicas completada"
```

---

### T3 — Actualizar /etc/hosts en los 3 servidores

Agregar resolución de nombres internos por IP privada en cada servidor.

**En Frontend (209.38.75.235):**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
# Backup
cp /etc/hosts /etc/hosts.bak-019

# Agregar aliases internos (solo si no existen ya)
grep -q "cdtalleres-backend" /etc/hosts || echo "10.124.0.9  cdtalleres-backend backend-internal" >> /etc/hosts
grep -q "cdtalleres-db" /etc/hosts || echo "10.124.0.7  cdtalleres-db db-internal" >> /etc/hosts

echo "=== /etc/hosts actualizado ==="
cat /etc/hosts
'
```

**En Backend (164.92.94.47):**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
cp /etc/hosts /etc/hosts.bak-019

grep -q "cdtalleres-db" /etc/hosts || echo "10.124.0.7  cdtalleres-db db-internal" >> /etc/hosts
grep -q "cdtalleres-frontend" /etc/hosts || echo "10.124.0.10  cdtalleres-frontend frontend-internal" >> /etc/hosts

echo "=== /etc/hosts actualizado ==="
cat /etc/hosts
'
```

**En DB (165.232.130.222):**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
cp /etc/hosts /etc/hosts.bak-019

grep -q "cdtalleres-backend" /etc/hosts || echo "10.124.0.9  cdtalleres-backend backend-internal" >> /etc/hosts
grep -q "cdtalleres-frontend" /etc/hosts || echo "10.124.0.10  cdtalleres-frontend frontend-internal" >> /etc/hosts

echo "=== /etc/hosts actualizado ==="
cat /etc/hosts
'
```

```bash
tg_notify "✅ *CDT 019 T3* — /etc/hosts actualizado en 3 servidores"
```

---

### T4 — Actualizar common_site_config.json con IP privada de DB

El archivo `common_site_config.json` contiene `db_host` — cambiar a IP privada del servidor DB.

**En Frontend Y Backend** (ejecutar en ambos):

```bash
for SERVER in 209.38.75.235 164.92.94.47; do
  sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@$SERVER "
BENCH=/home/erpnext/frappe-bench
CONFIG=\$BENCH/sites/common_site_config.json

echo '=== Config actual en $SERVER ==='
cat \$CONFIG 2>/dev/null || echo 'no existe'

# Backup
cp \$CONFIG \${CONFIG}.bak-019 2>/dev/null

# Cambiar db_host a IP privada
python3 -c \"
import json, sys
try:
    with open('\$CONFIG', 'r') as f:
        cfg = json.load(f)
    old_db_host = cfg.get('db_host', 'no definido')
    cfg['db_host'] = '10.124.0.7'
    with open('\$CONFIG', 'w') as f:
        json.dump(cfg, f, indent=2)
    print('db_host cambiado de:', old_db_host, '-> 10.124.0.7')
    print('Config final:', json.dumps(cfg, indent=2))
except Exception as e:
    print('ERROR:', e)
\" 2>&1
  " 2>&1
  echo "---"
done
```

```bash
tg_notify "✅ *CDT 019 T4* — common_site_config.json actualizado con db_host=10.124.0.7"
```

---

### T5 — Verificar que MariaDB acepta conexiones desde red privada

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== bind-address actual ==="
mysql -u root -p".Overskull2026.m" -e "SHOW VARIABLES LIKE '"'"'bind_address'"'"';" 2>/dev/null

echo "=== Archivo de config MariaDB ==="
grep -r "bind.address" /etc/mysql/ 2>/dev/null

# Si bind-address es 127.0.0.1 o solo IP pública, cambiarlo a 0.0.0.0
BIND=$(mysql -u root -p".Overskull2026.m" -se "SELECT @@bind_address;" 2>/dev/null)
echo "bind_address actual: $BIND"

if [ "$BIND" = "127.0.0.1" ]; then
  echo "bind-address = 127.0.0.1 — necesita cambio a 0.0.0.0"
  # Buscar archivo de config
  CONF_FILE=$(grep -rl "bind.address" /etc/mysql/ 2>/dev/null | head -1)
  echo "Archivo: $CONF_FILE"
  sed -i "s/bind-address.*=.*/bind-address = 0.0.0.0/" $CONF_FILE
  grep "bind-address" $CONF_FILE
  systemctl restart mariadb
  sleep 3
  systemctl status mariadb | head -5
else
  echo "bind-address OK: $BIND"
fi

echo "=== Verificar que puerto 3306 escucha en red privada ==="
ss -tlnp | grep 3306
'
```

```bash
tg_notify "✅ *CDT 019 T5* — MariaDB bind-address verificado"
```

---

### T6 — Verificar grant de usuario DB desde IP privada

MariaDB necesita grant explícito para conexiones desde `10.124.0.9` (backend) y `10.124.0.10` (frontend).

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB_NAME="_0646d69b639ad0ff"

echo "=== Grants actuales del usuario DB ==="
mysql -u root -p".Overskull2026.m" -e "SHOW GRANTS FOR '"'"'${DB_NAME}'"'"'@'"'"'%'"'"';" 2>/dev/null || \
mysql -u root -p".Overskull2026.m" -e "SELECT user, host FROM mysql.user WHERE user LIKE '"'"'_0646%'"'"';" 2>/dev/null

# Agregar grants para IPs privadas si no existen
mysql -u root -p".Overskull2026.m" << EOF 2>/dev/null
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '"'"'${DB_NAME}'"'"'@'"'"'10.124.0.9'"'"' IDENTIFIED BY '"'"'$(mysql -u root -p".Overskull2026.m" -se "SELECT authentication_string FROM mysql.user WHERE user='"'"'${DB_NAME}'"'"' LIMIT 1;" 2>/dev/null || echo "password-manual")'"'"';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '"'"'${DB_NAME}'"'"'@'"'"'10.124.0.10'"'"' IDENTIFIED BY '"'"'MISMO_PASSWORD'"'"';
FLUSH PRIVILEGES;
EOF

echo "=== Grants post-actualización ==="
mysql -u root -p".Overskull2026.m" -e "SELECT user, host FROM mysql.user WHERE user LIKE '"'"'_0646%'"'"';" 2>/dev/null
'
```

**NOTA**: Si el script de grants falla por el password (el SELECT de authentication_string no retorna el password legible), obtener el password del `site_config.json`:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 \
  "python3 -c \"import json; cfg=json.load(open('/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json')); print('db_password:', cfg.get('db_password','no encontrado'))\"" 2>/dev/null
```

Usar ese password en los GRANT.

```bash
tg_notify "✅ *CDT 019 T6* — Grants MariaDB para IPs privadas configurados"
```

---

### T7 — Probar conexión DB desde backend por IP privada

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
DB_HOST=10.124.0.7
DB_NAME="_0646d69b639ad0ff"

echo "=== Test conexión MySQL desde backend a DB privada ==="
# Obtener password del site_config
DB_PASS=$(python3 -c "import json; cfg=json.load(open('"'"'/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json'"'"')); print(cfg.get('"'"'db_password'"'"','"'"''"'"'))" 2>/dev/null)
echo "Password obtenido: ${#DB_PASS} chars"

mysql -h $DB_HOST -u $DB_NAME -p"$DB_PASS" $DB_NAME -e "SELECT 1 AS test;" 2>&1

echo "=== Test con nombre interno ==="
mysql -h cdtalleres-db -u $DB_NAME -p"$DB_PASS" $DB_NAME -e "SELECT 1 AS test;" 2>&1
'
```

```bash
tg_notify "✅ *CDT 019 T7* — Conexión DB por red privada verificada"
```

---

### T8 — Reiniciar servicios Frappe y verificar funcionamiento

```bash
# Reiniciar workers en backend
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
supervisorctl restart all 2>/dev/null || \
  (cd /home/erpnext/frappe-bench && sudo -u erpnext bench restart 2>&1) || \
  systemctl restart supervisor 2>/dev/null
sleep 5
supervisorctl status 2>/dev/null | head -20
'

# Reiniciar frontend
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
supervisorctl restart all 2>/dev/null || \
  (cd /home/erpnext/frappe-bench && sudo -u erpnext bench restart 2>&1) || \
  systemctl restart supervisor 2>/dev/null
sleep 5
supervisorctl status 2>/dev/null | head -20

# Test HTTP
HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)
echo "HTTP localhost: $HTTP"
'

tg_notify "✅ *CDT 019 T8* — Servicios reiniciados\nHTTP: $(sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 'curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null' 2>/dev/null)"
```

---

### T9 — Verificar latencia antes/después

```bash
# Latencia DB desde backend — por IP privada vs pública
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Latencia a DB por IP PRIVADA (10.124.0.7) ==="
ping -c 5 10.124.0.7 | tail -2

echo "=== Latencia a DB por IP PÚBLICA (165.232.130.222) ==="
ping -c 5 165.232.130.222 | tail -2
'

tg_notify "🏁 *CDT 019 TERMINÓ* — Red privada configurada\nVer: c:\\dev\\cdtalleres\\red-privada-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\red-privada-results.md
```

### Estructura obligatoria

```markdown
# Configuración Red Privada CDTalleres — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T1. Conectividad privada verificada | ✅/❌ | ping frontend→backend: , frontend→db: , backend→db: |
| T2. Auditoría IPs públicas | ✅/❌ | archivos con IPs públicas encontrados: |
| T3. /etc/hosts actualizado | ✅/❌ | 3 servidores: sí/no |
| T4. common_site_config.json db_host | ✅/❌ | anterior: , nuevo: 10.124.0.7 |
| T5. MariaDB bind-address | ✅/❌ | valor: |
| T6. Grants IP privada | ✅/❌ | grants para 10.124.0.9 y 10.124.0.10: |
| T7. Test conexión DB privada | ✅/❌ | resultado mysql: |
| T8. Servicios reiniciados | ✅/❌ | HTTP: |
| T9. Latencia comparada | ✅/❌ | privada: Xms, pública: Xms |

## Archivos modificados

| Archivo | Servidor | Cambio |
|---|---|---|
| /etc/hosts | frontend | agregado backend/db IPs privadas |
| /etc/hosts | backend | agregado db IP privada |
| /etc/hosts | db | agregado frontend/backend IPs privadas |
| sites/common_site_config.json | frontend | db_host → 10.124.0.7 |
| sites/common_site_config.json | backend | db_host → 10.124.0.7 |
| MariaDB bind-address | db | [valor anterior] → 0.0.0.0 |

## Latencia comparada (T9)
- DB por red privada (10.124.0.7): Xms avg
- DB por IP pública (165.232.130.222): Xms avg
- Mejora: X%

## Bloqueos y errores
[OBLIGATORIO — vacío si todo bien]
```
