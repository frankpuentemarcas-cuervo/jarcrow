---
fecha: 2026-04-25
agente_id: "022"
descripcion: tuning-gunicorn-workers-mariadb-parametros
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\tuning-results.md"
dependencia: "CDT-TASK-020 completada (red privada)"
tarea_origen: CDT-TASK-022
---

# Tuning Gunicorn Workers + MariaDB Parámetros

## Contexto para el agente

Proyecto CDTalleres: ERPNext distribuido en 3 servidores. El backend (`164.92.94.47`) tiene 2 CPU cores y Gunicorn corriendo con solo 3 workers — debería tener 5 según la fórmula `(2*CPU)+1`. MariaDB (`165.232.130.222`) tiene parámetros por defecto sin optimizar.

**Objetivo**: Maximizar paralelismo en Gunicorn y ajustar MariaDB para carga ERPNext.

### Credenciales SSH

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@[IP]
```

| Rol | IP |
|---|---|
| Backend (Gunicorn) | `164.92.94.47` |
| DB (MariaDB) | `165.232.130.222` |

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear `c:\dev\cdtalleres\tuning-results.md` y actualizar después de CADA tarea
2. Documentar resultado (✅/❌), output exacto, valores anteriores y nuevos
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

### T1 — Auditar configuración actual Gunicorn

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== CPU cores ==="
nproc
grep -c ^processor /proc/cpuinfo

echo "=== Workers actuales (procesos gunicorn) ==="
ps aux | grep gunicorn | grep -v grep | wc -l
ps aux | grep gunicorn | grep -v grep

echo "=== Config supervisor — archivos ==="
ls /etc/supervisor/conf.d/

echo "=== Contenido supervisor configs ==="
grep -r "workers\|gunicorn\|timeout\|processes" /etc/supervisor/conf.d/ 2>/dev/null

echo "=== Bench gunicorn config ==="
find /home/erpnext/frappe-bench -name "*.conf" -o -name "gunicorn*" 2>/dev/null | grep -v ".pyc" | head -20
cat /home/erpnext/frappe-bench/config/supervisor.conf 2>/dev/null | grep -A3 -i "gunicorn\|worker"
'
```

```bash
tg_notify "✅ *CDT 022 T1* — Auditoría Gunicorn completada"
```

---

### T2 — Cambiar Gunicorn de 3 a 5 workers

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
BENCH=/home/erpnext/frappe-bench

echo "=== Ubicar archivo de configuración supervisor de Gunicorn ==="
# Frappe bench genera config en bench/config/supervisor.conf
# y puede estar copiado en /etc/supervisor/conf.d/
SUPERVISOR_CONF=""
for F in /etc/supervisor/conf.d/*.conf /etc/supervisor/supervisord.conf; do
  if grep -q "gunicorn" "$F" 2>/dev/null; then
    SUPERVISOR_CONF="$F"
    echo "Config encontrada: $F"
    break
  fi
done

if [ -z "$SUPERVISOR_CONF" ]; then
  echo "Config en bench:"
  SUPERVISOR_CONF="$BENCH/config/supervisor.conf"
  cat "$SUPERVISOR_CONF" | grep -A10 gunicorn
fi

echo "=== Backup config ==="
cp "$SUPERVISOR_CONF" "${SUPERVISOR_CONF}.bak-022"

echo "=== Config actual gunicorn ==="
grep -n "workers\|worker\|timeout\|gunicorn" "$SUPERVISOR_CONF" | head -20

echo "=== Aplicar cambio: 3 -> 5 workers, timeout 120s ==="
# Cambiar numero de workers
sed -i "s/--workers [0-9]*/--workers 5/g" "$SUPERVISOR_CONF"
sed -i "s/workers=[0-9]*/workers=5/g" "$SUPERVISOR_CONF"

# Ajustar timeout
sed -i "s/--timeout [0-9]*/--timeout 120/g" "$SUPERVISOR_CONF"

echo "=== Config post-cambio ==="
grep -n "workers\|timeout\|gunicorn" "$SUPERVISOR_CONF" | head -20
'
```

```bash
tg_notify "✅ *CDT 022 T2* — Config Gunicorn actualizada: 3→5 workers"
```

---

### T3 — Regenerar config con bench y reiniciar supervisor

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
BENCH=/home/erpnext/frappe-bench

echo "=== Opción A: bench set-config (si bench soporta workers) ==="
cd $BENCH
sudo -u erpnext bench config set gunicorn_workers 5 2>/dev/null && echo "OK" || echo "no soportado"

echo "=== Recargar supervisor ==="
supervisorctl reread 2>&1
supervisorctl update 2>&1
supervisorctl restart all 2>&1 | head -20
sleep 5

echo "=== Verificar workers activos ==="
ps aux | grep gunicorn | grep -v grep
echo "Total workers: $(ps aux | grep gunicorn | grep -v grep | wc -l)"

echo "=== Estado supervisor ==="
supervisorctl status 2>/dev/null | head -20
'
```

```bash
tg_notify "✅ *CDT 022 T3* — Supervisor reiniciado con 5 workers"
```

---

### T4 — Auditar parámetros actuales MariaDB

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== Variables clave MariaDB ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT variable_name, variable_value
FROM information_schema.global_variables
WHERE variable_name IN (
  '"'"'innodb_buffer_pool_size'"'"',
  '"'"'innodb_lock_wait_timeout'"'"',
  '"'"'max_connections'"'"',
  '"'"'slow_query_log'"'"',
  '"'"'slow_query_log_file'"'"',
  '"'"'long_query_time'"'"',
  '"'"'query_cache_type'"'"',
  '"'"'query_cache_size'"'"',
  '"'"'innodb_flush_log_at_trx_commit'"'"',
  '"'"'innodb_log_buffer_size'"'"',
  '"'"'thread_cache_size'"'"',
  '"'"'tmp_table_size'"'"',
  '"'"'max_heap_table_size'"'"'
)
ORDER BY variable_name;" 2>/dev/null

echo "=== RAM total del servidor ==="
free -h | head -3

echo "=== RAM usada por MariaDB ==="
ps aux | grep mysqld | grep -v grep | awk '"'"'{print "RSS:", $6/1024, "MB"}'"'"'

echo "=== Conexiones actuales ==="
mysql -u root -p".Overskull2026.m" -e "SHOW STATUS LIKE '"'"'Threads_connected'"'"';" 2>/dev/null

echo "=== Archivo de configuración MariaDB ==="
ls /etc/mysql/mariadb.conf.d/ 2>/dev/null
cat /etc/mysql/mariadb.conf.d/50-server.cnf 2>/dev/null | grep -v "^#" | grep -v "^$" | head -40
'
```

```bash
tg_notify "✅ *CDT 022 T4* — Auditoría MariaDB completada"
```

---

### T5 — Aplicar tuning MariaDB

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== Obtener RAM total para calcular buffer pool ==="
TOTAL_RAM_MB=$(free -m | awk '"'"'/^Mem:/{print $2}'"'"')
echo "RAM total: ${TOTAL_RAM_MB}MB"

# buffer_pool = 70% de RAM (si > 4GB usar 70%, si < 4GB usar 50%)
if [ $TOTAL_RAM_MB -gt 4096 ]; then
  BUFFER_POOL_MB=$((TOTAL_RAM_MB * 70 / 100))
else
  BUFFER_POOL_MB=$((TOTAL_RAM_MB * 50 / 100))
fi
echo "Buffer pool recomendado: ${BUFFER_POOL_MB}MB"

CONF_FILE="/etc/mysql/mariadb.conf.d/50-server.cnf"
cp $CONF_FILE ${CONF_FILE}.bak-022

echo "=== Aplicando tuning en $CONF_FILE ==="

# Crear bloque de tuning CDTalleres al final del archivo
cat >> $CONF_FILE << EOF

# === CDTalleres Performance Tuning 2026-04-25 ===
# innodb_buffer_pool_size = ${BUFFER_POOL_MB}M   # descomentar si es correcto
innodb_lock_wait_timeout = 30
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1
log_queries_not_using_indexes = 0
innodb_flush_log_at_trx_commit = 2
max_connections = 200
thread_cache_size = 8
tmp_table_size = 64M
max_heap_table_size = 64M
EOF

echo "=== Config añadida ==="
tail -20 $CONF_FILE

echo "=== Validar config MariaDB ==="
mysqld --validate-config 2>&1 || mysqlcheck --defaults-file=$CONF_FILE 2>/dev/null || echo "validate no disponible"
'
```

**NOTA sobre `innodb_buffer_pool_size`**: el bloque lo deja comentado — el agente debe evaluar la RAM actual y descomentar con el valor correcto si el actual es demasiado bajo.

```bash
tg_notify "✅ *CDT 022 T5* — Tuning MariaDB escrito en config"
```

---

### T6 — Reiniciar MariaDB y verificar parámetros

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== Reiniciando MariaDB ==="
systemctl restart mariadb
sleep 5
systemctl status mariadb --no-pager | head -10

echo "=== Verificar parámetros aplicados ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT variable_name, variable_value
FROM information_schema.global_variables
WHERE variable_name IN (
  '"'"'innodb_lock_wait_timeout'"'"',
  '"'"'slow_query_log'"'"',
  '"'"'slow_query_log_file'"'"',
  '"'"'long_query_time'"'"',
  '"'"'innodb_flush_log_at_trx_commit'"'"',
  '"'"'max_connections'"'"',
  '"'"'innodb_buffer_pool_size'"'"'
)
ORDER BY variable_name;" 2>/dev/null

echo "=== Test conexión DB desde backend ==="
'

# Test desde backend
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
DB_PASS=$(python3 -c "import json; cfg=json.load(open('"'"'/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json'"'"')); print(cfg.get('"'"'db_password'"'"','"'"''"'"'))" 2>/dev/null)
mysql -h 10.124.0.7 -u _0646d69b639ad0ff -p"$DB_PASS" _0646d69b639ad0ff -e "SELECT 1 AS db_ok;" 2>&1
'
```

```bash
tg_notify "✅ *CDT 022 T6* — MariaDB reiniciado con tuning aplicado"
```

---

### T7 — Verificar slow query log funciona

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== Crear directorio log si no existe ==="
mkdir -p /var/log/mysql
chown mysql:mysql /var/log/mysql 2>/dev/null
ls -la /var/log/mysql/

echo "=== Forzar una query lenta (SLEEP 2s) para test ==="
mysql -u root -p".Overskull2026.m" -e "SELECT SLEEP(2);" 2>/dev/null

echo "=== Verificar slow query log ==="
sleep 1
cat /var/log/mysql/slow.log 2>/dev/null | tail -20 || echo "Log vacío o no existe aun"

echo "=== Estado slow_query_log ==="
mysql -u root -p".Overskull2026.m" -e "SHOW GLOBAL STATUS LIKE '"'"'Slow_queries'"'"';" 2>/dev/null
'
```

```bash
tg_notify "🏁 *CDT 022 TERMINÓ* — Gunicorn 5 workers + MariaDB tuning aplicado\nVer: c:\\dev\\cdtalleres\\tuning-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\tuning-results.md
```

### Estructura obligatoria

```markdown
# Tuning Gunicorn + MariaDB CDTalleres — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T1. Auditoría Gunicorn | ✅/❌ | workers actuales: X, config: |
| T2. Config Gunicorn 3→5 workers | ✅/❌ | archivo modificado: |
| T3. Supervisor reiniciado | ✅/❌ | workers activos: X |
| T4. Auditoría MariaDB | ✅/❌ | buffer_pool: , lock_timeout: , slow_log: |
| T5. Tuning MariaDB escrito | ✅/❌ | parámetros: |
| T6. MariaDB reiniciado | ✅/❌ | estado: |
| T7. Slow query log verificado | ✅/❌ | query lenta capturada: sí/no |

## Valores antes/después

| Parámetro | Antes | Después |
|---|---|---|
| gunicorn workers | 3 | 5 |
| innodb_lock_wait_timeout | ? | 30 |
| slow_query_log | OFF | ON |
| long_query_time | 10 | 1 |
| max_connections | ? | 200 |
| innodb_buffer_pool_size | ? | ? |

## Bloqueos y errores

[vacío si todo OK]
```
