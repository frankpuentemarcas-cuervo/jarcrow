---
fecha: 2026-04-25
agente_id: "010"
descripcion: fix-backend-db-host-y-gunicorn-workers
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\backend-fix-results.md"
dependencia: "005 (profiling identificó db_host incorrecto en Backend)"
---

# Fix Backend: db_host + Gunicorn Workers — CDTalleres

## Contexto para el agente

Proyecto CDTalleres (ERPNext v13.9.2 / Frappe 13.9.1 para Shalom / Overskull). El profiling (prompt 005) identificó dos problemas en el servidor Backend (164.92.94.47):

1. **`db_host = 127.0.0.1`** en `site_config.json` del Backend — causa errores `pymysql.err.OperationalError: (2003, Can't connect to MySQL server on '127.0.0.1')`. La DB está en 165.232.130.222, no local.
2. **Gunicorn workers = 3** — con 2 CPU cores, el óptimo es 5 (2×2+1).

El Frontend (209.38.75.235) ya tiene `db_host=165.232.130.222` correcto (prompt 007). El Backend quedó sin corregir.

### Arquitectura

| Servidor | IP | Rol |
|---|---|---|
| Frontend/App | 209.38.75.235 | Nginx + Gunicorn principal |
| Backend | 164.92.94.47 | Workers adicionales — **aquí se trabaja** |
| DB | 165.232.130.222 | MariaDB |

### Datos del sitio (obtenidos en prompt 005)
- **DB real name**: `_0646d69b639ad0ff` (NO es "CDTALLERES")
- **DB host correcto**: `165.232.130.222`
- **Bench path**: `/home/erpnext/frappe-bench`
- **Site**: `CDTALLERES`
- **Usuario bench**: `erpnext`

### Credenciales SSH

| Servidor | Usuario | Password |
|---|---|---|
| 164.92.94.47 | root | .Overskull2026.m |
| 165.232.130.222 | root | .Overskull2026.m |

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Genera o actualiza el archivo de salida inmediatamente con lo ejecutado
2. Documenta CADA tarea: resultado (✅/❌), output exacto, error completo si falló
3. Nunca termines sin el archivo de salida. Aunque sea parcial.
4. Si una tarea falla, documentarla y continuar con la siguiente.

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

## ⚠️ REGLA DE SEGURIDAD

- Backup de `site_config.json` ANTES de modificar
- Si Frappe workers no levantan después del cambio, restaurar backup y documentar

---

## Tareas a ejecutar

### 1. Ver estado actual en Backend (164.92.94.47)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
BENCH=/home/erpnext/frappe-bench

echo "=== site_config.json ACTUAL ==="
cat $BENCH/sites/CDTALLERES/site_config.json

echo "=== SUPERVISOR CONFIG (workers gunicorn) ==="
cat $BENCH/config/supervisor.conf 2>/dev/null | grep -A 5 -i "gunicorn\|workers"

echo "=== SUPERVISOR STATUS ==="
supervisorctl status 2>/dev/null

echo "=== LOGS RECIENTES (errores DB) ==="
tail -20 $BENCH/logs/worker.log 2>/dev/null | grep -i "error\|cant connect\|refused" || echo "sin errores recientes"
'
```

Notificar:
```bash
tg_notify "📋 *CDT T1* — Estado actual Backend auditado"
```

---

### 2. Backup + corregir db_host en Backend

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
BENCH=/home/erpnext/frappe-bench
DATE=$(date +%Y%m%d_%H%M)

echo "=== BACKUP ==="
cp $BENCH/sites/CDTALLERES/site_config.json $BENCH/sites/CDTALLERES/site_config.json.bak.$DATE
ls -lh $BENCH/sites/CDTALLERES/site_config.json.bak.$DATE

echo "=== ACTUALIZAR db_host ==="
python3 -c "
import json
f = '"'"'$BENCH/sites/CDTALLERES/site_config.json'"'"'
with open(f) as fp:
    cfg = json.load(fp)
print('"'"'ANTES: db_host ='"'"', cfg.get('"'"'db_host'"'"', '"'"'(no definido)'"'"'))
cfg['"'"'db_host'"'"'] = '"'"'165.232.130.222'"'"'
cfg['"'"'db_port'"'"'] = 3306
with open(f, '"'"'w'"'"') as fp:
    json.dump(cfg, fp, indent=1)
print('"'"'DESPUÉS:'"'"', json.dumps(cfg, indent=1))
"

echo "=== VERIFICAR CONEXIÓN DB REMOTA ==="
DB_PASS=$(python3 -c "import json; print(json.load(open('"'"'$BENCH/sites/CDTALLERES/site_config.json'"'"'))['\"'db_password'\"'])")
DB_NAME=$(python3 -c "import json; print(json.load(open('"'"'$BENCH/sites/CDTALLERES/site_config.json'"'"'))['\"'db_name'\"'])")
echo "DB Name: $DB_NAME"
mysql -h 165.232.130.222 -u "$DB_NAME" -p"$DB_PASS" "$DB_NAME" -e "SELECT COUNT(*) as total FROM tabDocType;" 2>&1
'
```

Notificar según resultado:
```bash
# Si éxito:
tg_notify "✅ *CDT T2* — db_host corregido en Backend → 165.232.130.222\nConexión MariaDB remota: OK"
# Si falla:
tg_notify "❌ *CDT T2* — Error corrigiendo db_host en Backend\nVer: c:\\dev\\cdtalleres\\backend-fix-results.md"
```

---

### 3. Aumentar Gunicorn workers 3 → 5

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
BENCH=/home/erpnext/frappe-bench
DATE=$(date +%Y%m%d_%H%M)

echo "=== BACKUP supervisor.conf ==="
cp $BENCH/config/supervisor.conf $BENCH/config/supervisor.conf.bak.$DATE 2>/dev/null && echo "backup OK" || echo "no encontrado"

echo "=== CONFIG ACTUAL DE WORKERS ==="
grep -n "numprocs\|workers\|gunicorn" $BENCH/config/supervisor.conf 2>/dev/null | head -20

echo "=== CAMBIAR workers a 5 ==="
# Método 1: sed en supervisor.conf
sed -i "s/--workers [0-9]*/--workers 5/" $BENCH/config/supervisor.conf 2>/dev/null && echo "sed OK" || echo "sed no encontró patron"

# Verificar cambio
echo "=== DESPUÉS DEL CAMBIO ==="
grep -n "workers\|gunicorn" $BENCH/config/supervisor.conf 2>/dev/null | head -10

# Método alternativo si bench tiene comando para esto
cd $BENCH
sudo -u erpnext bench config gunicorn_workers 5 2>/dev/null && echo "bench config OK" || echo "sin bench config"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T3* — Gunicorn workers actualizados a 5 en Backend"
```

---

### 4. Reiniciar workers y verificar

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
BENCH=/home/erpnext/frappe-bench

echo "=== RELOAD SUPERVISOR ==="
supervisorctl reread 2>/dev/null
supervisorctl update 2>/dev/null
supervisorctl restart all 2>/dev/null
sleep 8

echo "=== STATUS DESPUÉS ==="
supervisorctl status 2>/dev/null

echo "=== LOGS POST-RESTART (verificar sin errores DB) ==="
sleep 5
tail -30 $BENCH/logs/worker.log 2>/dev/null | tail -20
tail -10 $BENCH/logs/worker.error.log 2>/dev/null || echo "sin worker.error.log"

echo "=== VERIFICAR WORKERS GUNICORN ACTIVOS ==="
ps aux | grep gunicorn | grep -v grep | wc -l
echo "procesos gunicorn activos"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T4* — Workers Backend reiniciados\nVerificando logs..."
```

---

### 5. Verificación final — sin errores de conexión DB

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
BENCH=/home/erpnext/frappe-bench

echo "=== ERRORES DB EN LOGS (últimos 5 min) ==="
tail -100 $BENCH/logs/worker.log 2>/dev/null | grep -i "cant connect\|connection refused\|127.0.0.1\|OperationalError" | tail -10
echo "---fin errores---"

echo "=== site_config.json FINAL ==="
cat $BENCH/sites/CDTALLERES/site_config.json | python3 -c "import json,sys; cfg=json.load(sys.stdin); print(f\"db_host: {cfg.get('"'"'db_host'"'"')}\ndb_port: {cfg.get('"'"'db_port'"'"')}\ndb_name: {cfg.get('"'"'db_name'"'"')}\")"

echo "=== GUNICORN WORKERS ACTIVOS ==="
ps aux | grep "gunicorn" | grep -v grep
'
```

Notificar al terminar:
```bash
tg_notify "🏁 *CDT 010 TERMINÓ* — Backend fix completo\n✅ db_host → 165.232.130.222\n✅ Gunicorn workers → 5\nVer: c:\\dev\\cdtalleres\\backend-fix-results.md"
```

---

## Archivo de salida

**Crear o actualizar después de CADA tarea:**
```
c:\dev\cdtalleres\backend-fix-results.md
```

### Estructura obligatoria

```markdown
# Backend Fix CDTalleres — YYYY-MM-DD HH:MM

## Estado antes de cambios

- db_host original: [valor]
- db_port original: [valor]
- Gunicorn workers original: [N]
- Errores en logs: [sí/no — extracto]

## Cambios realizados

| Tarea | Estado | Detalle |
|---|---|---|
| 1. Auditoría estado actual | ✅/❌ | |
| 2. db_host corregido | ✅/❌ | 127.0.0.1 → 165.232.130.222 |
| 3. Conexión DB remota verificada | ✅/❌ | tabDocType count: N |
| 4. Gunicorn workers actualizados | ✅/❌ | 3 → 5 |
| 5. Workers reiniciados | ✅/❌ | supervisor status |
| 6. Sin errores DB en logs | ✅/❌ | |

## Logs post-restart

[últimas líneas de worker.log]

## Gunicorn workers activos

[output de ps aux | grep gunicorn]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
