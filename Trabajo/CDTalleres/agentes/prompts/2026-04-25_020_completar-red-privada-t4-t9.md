---
fecha: 2026-04-25
agente_id: "020"
descripcion: completar-red-privada-interna-t4-t9
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\red-privada-results.md"
dependencia: "prompt 019 T1-T3 completados"
tarea_origen: CDT-TASK-020
---

# Completar Red Privada Interna — T4 a T9

## Contexto para el agente

Proyecto CDTalleres: ERPNext distribuido en 3 servidores DigitalOcean en la misma región. El prompt 019 completó T1-T3:

- T1 ✅ — Ping entre IPs privadas OK
- T2 ✅ — Auditoría de IPs públicas completada
- T3 ✅ — `/etc/hosts` actualizado en los 3 servidores

**Objetivo de este prompt**: Ejecutar T4-T9 — migrar conexión DB de IP pública a IP privada.

### Topología

| Rol | IP Pública | IP Privada |
|---|---|---|
| Frontend (Nginx + ERPNext app) | `209.38.75.235` | `10.124.0.10` |
| Backend (Gunicorn/Workers) | `164.92.94.47` | `10.124.0.9` |
| Base de datos (MariaDB) | `165.232.130.222` | `10.124.0.7` |

### Credenciales SSH

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@[IP]
```

### Bench / Site

- **Bench**: `/home/erpnext/frappe-bench`
- **Site**: `CDTALLERES`
- **DB name**: `_0646d69b639ad0ff`

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Actualizar `c:\dev\cdtalleres\red-privada-results.md` después de CADA tarea
2. Documentar resultado (✅/❌), output exacto, error completo si falló
3. Si un paso falla → documentar → continuar con el siguiente
4. Nunca terminar sin el archivo de salida

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

### T4 — Actualizar common_site_config.json con IP privada de DB

El archivo `common_site_config.json` contiene `db_host` — cambiar a IP privada del servidor DB.

**Ejecutar en Frontend Y Backend:**

```bash
for SERVER in 209.38.75.235 164.92.94.47; do
  sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@$SERVER "
BENCH=/home/erpnext/frappe-bench
CONFIG=\$BENCH/sites/common_site_config.json

echo '=== Config actual en $SERVER ==='
cat \$CONFIG 2>/dev/null || echo 'no existe'

# Backup
cp \$CONFIG \${CONFIG}.bak-020 2>/dev/null

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
tg_notify "✅ *CDT 020 T4* — common_site_config.json actualizado con db_host=10.124.0.7"
```

---

### T5 — Verificar que MariaDB acepta conexiones desde red privada

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== bind-address actual ==="
mysql -u root -p".Overskull2026.m" -e "SHOW VARIABLES LIKE '"'"'bind_address'"'"';" 2>/dev/null

echo "=== Archivo de config MariaDB ==="
grep -r "bind.address" /etc/mysql/ 2>/dev/null

# Si bind-address es 127.0.0.1, cambiar a 0.0.0.0
BIND=$(mysql -u root -p".Overskull2026.m" -se "SELECT @@bind_address;" 2>/dev/null)
echo "bind_address actual: $BIND"

if [ "$BIND" = "127.0.0.1" ]; then
  echo "bind-address = 127.0.0.1 — cambiando a 0.0.0.0"
  CONF_FILE=$(grep -rl "bind.address" /etc/mysql/ 2>/dev/null | head -1)
  echo "Archivo de config: $CONF_FILE"
  sed -i "s/bind-address.*=.*/bind-address = 0.0.0.0/" $CONF_FILE
  grep "bind-address" $CONF_FILE
  systemctl restart mariadb
  sleep 3
  systemctl status mariadb | head -5
else
  echo "bind-address OK: $BIND — no requiere cambio"
fi

echo "=== Puerto 3306 escuchando ==="
ss -tlnp | grep 3306
'
```

```bash
tg_notify "✅ *CDT 020 T5* — MariaDB bind-address verificado"
```

---

### T6 — Agregar grants para IPs privadas

MariaDB necesita grant explícito para conexiones desde `10.124.0.9` (backend) y `10.124.0.10` (frontend).

**Paso 6a — obtener password del DB desde site_config.json:**

```bash
DB_PASS=$(sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 \
  "python3 -c \"import json; cfg=json.load(open('/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json')); print(cfg.get('db_password',''))\"" 2>/dev/null)
echo "Password obtenido: ${#DB_PASS} chars"
```

**Paso 6b — crear grants en MariaDB:**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 "
DB_NAME='_0646d69b639ad0ff'
DB_PASS='$DB_PASS'

echo '=== Grants actuales del usuario ==='
mysql -u root -p'.Overskull2026.m' -e \"SELECT user, host FROM mysql.user WHERE user LIKE '_0646%';\" 2>/dev/null

echo '=== Crear grants para IPs privadas ==='
mysql -u root -p'.Overskull2026.m' << 'SQL'
GRANT ALL PRIVILEGES ON \`_0646d69b639ad0ff\`.* TO '_0646d69b639ad0ff'@'10.124.0.9' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON \`_0646d69b639ad0ff\`.* TO '_0646d69b639ad0ff'@'10.124.0.10' IDENTIFIED BY '$DB_PASS';
FLUSH PRIVILEGES;
SQL

echo '=== Grants post-actualización ==='
mysql -u root -p'.Overskull2026.m' -e \"SELECT user, host FROM mysql.user WHERE user LIKE '_0646%';\" 2>/dev/null
"
```

```bash
tg_notify "✅ *CDT 020 T6* — Grants para 10.124.0.9 y 10.124.0.10 configurados"
```

---

### T7 — Probar conexión DB desde backend por IP privada

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
DB_HOST=10.124.0.7
DB_NAME="_0646d69b639ad0ff"

echo "=== Obtener password del site_config ==="
DB_PASS=$(python3 -c "import json; cfg=json.load(open('"'"'/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json'"'"')); print(cfg.get('"'"'db_password'"'"','"'"''"'"'))" 2>/dev/null)
echo "Password: ${#DB_PASS} chars"

echo "=== Test por IP privada (10.124.0.7) ==="
mysql -h $DB_HOST -u $DB_NAME -p"$DB_PASS" $DB_NAME -e "SELECT 1 AS conexion_privada_ok;" 2>&1

echo "=== Test por nombre interno (cdtalleres-db) ==="
mysql -h cdtalleres-db -u $DB_NAME -p"$DB_PASS" $DB_NAME -e "SELECT 1 AS nombre_interno_ok;" 2>&1
'
```

```bash
tg_notify "✅ *CDT 020 T7* — Conexión DB por red privada verificada"
```

---

### T8 — Reiniciar servicios Frappe y verificar funcionamiento

```bash
# Reiniciar backend
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Reiniciando workers en backend ==="
supervisorctl restart all 2>/dev/null || \
  (cd /home/erpnext/frappe-bench && bench restart 2>&1) || \
  systemctl restart supervisor 2>/dev/null
sleep 5
supervisorctl status 2>/dev/null | head -20
'

# Reiniciar frontend
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
echo "=== Reiniciando frontend ==="
supervisorctl restart all 2>/dev/null || \
  (cd /home/erpnext/frappe-bench && bench restart 2>&1) || \
  systemctl restart supervisor 2>/dev/null
sleep 5
supervisorctl status 2>/dev/null | head -20

echo "=== Test HTTP ==="
HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)
echo "HTTP localhost: $HTTP"

HTTP_DOMAIN=$(curl -s -o /dev/null -w "%{http_code}" https://cdtalleres-copia.shalom.com.pe 2>/dev/null)
echo "HTTP dominio: $HTTP_DOMAIN"
'
```

```bash
tg_notify "✅ *CDT 020 T8* — Servicios reiniciados y HTTP verificado"
```

---

### T9 — Comparar latencia IP privada vs pública

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Latencia DB por IP PRIVADA (10.124.0.7) ==="
ping -c 10 10.124.0.7 | tail -2

echo "=== Latencia DB por IP PÚBLICA (165.232.130.222) ==="
ping -c 10 165.232.130.222 | tail -2

echo "=== Latencia MySQL por IP privada ==="
time mysql -h 10.124.0.7 -u _0646d69b639ad0ff \
  -p"$(python3 -c "import json; cfg=json.load(open('/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json')); print(cfg.get('db_password',''))" 2>/dev/null)" \
  _0646d69b639ad0ff -e "SELECT 1;" 2>&1
'
```

```bash
tg_notify "🏁 *CDT 020 TERMINÓ* — Red privada completada\nVer resultados: c:\\dev\\cdtalleres\\red-privada-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\red-privada-results.md
```

### Estructura obligatoria

Actualizar el archivo existente (que ya tiene T1-T3) con los resultados de T4-T9:

```markdown
## Resultados T4-T9 (prompt 020)

| Tarea | Estado | Notas |
|---|---|---|
| T4. common_site_config db_host | ✅/❌ | anterior: X, nuevo: 10.124.0.7 |
| T5. MariaDB bind-address | ✅/❌ | valor actual: |
| T6. Grants IP privada | ✅/❌ | grants 10.124.0.9 y 10.124.0.10: OK/FAIL |
| T7. Test conexión DB privada | ✅/❌ | SELECT 1: OK/FAIL |
| T8. Servicios reiniciados | ✅/❌ | HTTP: |
| T9. Latencia comparada | ✅/❌ | privada: Xms, pública: Xms, mejora: X% |

## Archivos modificados

| Archivo | Servidor | Cambio |
|---|---|---|
| sites/common_site_config.json | frontend 209.38.75.235 | db_host → 10.124.0.7 |
| sites/common_site_config.json | backend 164.92.94.47 | db_host → 10.124.0.7 |
| MariaDB bind-address | db 165.232.130.222 | [anterior] → 0.0.0.0 |

## Latencia comparada (T9)
- DB por red privada (10.124.0.7): Xms avg
- DB por IP pública (165.232.130.222): Xms avg
- Mejora: X%

## Bloqueos y errores
[vacío si todo OK]
```
