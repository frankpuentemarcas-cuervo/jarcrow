---
fecha: 2026-04-26
agente_id: "024"
descripcion: stress-test-breakpoint-200u-identificar-punto-ruptura
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\stress-test-50u-results.md"
dependencia: "CDT-TASK-020 ✅ CDT-TASK-022 ✅"
tarea_origen: CDT-TASK-024
---

# Stress Test Breakpoint — Hasta dónde aguanta el sistema post-optimización

## Contexto para el agente

Proyecto CDTalleres: ERPNext con 3 servidores DigitalOcean. Baseline original (prompt 014):
- **200 usuarios, ramp 10/s, 15 minutos**
- Sistema colapsó entre **50-70 usuarios concurrentes**
- Causa: tabSeries lock contention — `row_lock_time_avg` 14,740ms
- Resultado: 96%+ fail en OT-2, PO, PI desde el minuto 1

**Optimizaciones aplicadas desde entonces:**
- ✅ MariaDB SEQUENCE para OT-2, Historial, PO, PI → `row_lock_time_avg` = 0ms
- ✅ Red privada DB por IP `10.124.0.7` (sin gateway público)
- ✅ Gunicorn: 5 workers activos
- ✅ `innodb_lock_wait_timeout` = 30s (antes 50s)
- ✅ tabWorkflow Action: 3M → 848K filas, liberados 924MB

**Objetivo de este prompt**: Repetir exactamente el mismo test (200u, ramp 10/s, 15min) para ver hasta qué punto de usuarios el sistema aguanta ahora. Identificar el nuevo punto de ruptura y capturar qué causa el fallo (slow queries, CPU, RAM, conexiones).

### Topología

| Rol | IP Pública | IP Privada |
|---|---|---|
| Frontend | `209.38.75.235` | `10.124.0.10` |
| Backend (Locust) | `164.92.94.47` | `10.124.0.9` |
| DB (MariaDB) | `165.232.130.222` | `10.124.0.7` |

### Credenciales SSH

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@[IP]
```

### Datos técnicos

- Target: `https://cdtalleres-copia.shalom.com.pe`
- DB name: `_0646d69b639ad0ff`
- Slow query log: `/var/log/mysql/mariadb-slow.log`
- Grafana: `http://164.92.94.47:3000` (admin / cdtalleres)
- Dashboards: Node Exporter `http://164.92.94.47:3000/d/rYdddlPWk/node-exporter-full`
- MySQL Overview: `http://164.92.94.47:3000/d/MQWgroiiz/mysql-overview`

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear `c:\dev\cdtalleres\stress-test-50u-results.md` y actualizar después de CADA tarea
2. Documentar resultado (✅/❌), métricas exactas, output completo
3. Si el sistema colapsa durante el test → NO detener Locust — dejar correr los 15 minutos completos para capturar el punto exacto de ruptura
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

### T1 — Verificar estado pre-test

```bash
# Backend
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Locust disponible ==="
which locust && locust --version || echo "locust NO encontrado"

echo "=== Scripts Locust ==="
ls /home/erpnext/locust/ 2>/dev/null || find /home -name "locustfile*.py" 2>/dev/null | head -5

echo "=== Gunicorn workers ==="
ps aux | grep gunicorn | grep -v grep | wc -l
echo "Workers activos (debe ser 6: 1 master + 5)"

echo "=== Test HTTP target ==="
curl -s -o /dev/null -w "HTTP: %{http_code} | tiempo: %{time_total}s\n" \
  https://cdtalleres-copia.shalom.com.pe 2>/dev/null

echo "=== RAM disponible ==="
free -h | head -3

echo "=== CPU cores ==="
nproc
'

# DB
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== MariaDB estado ==="
systemctl status mariadb --no-pager | head -5

echo "=== Conexiones actuales ==="
mysql -u root -p".Overskull2026.m" -e "SHOW STATUS LIKE '"'"'Threads_connected'"'"';" 2>/dev/null

echo "=== SEQUENCE activas ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_schema = '"'"'_0646d69b639ad0ff'"'"';" 2>/dev/null

echo "=== Slow log configurado ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT variable_name, variable_value
FROM information_schema.global_variables
WHERE variable_name IN (
  '"'"'slow_query_log'"'"','"'"'slow_query_log_file'"'"',
  '"'"'long_query_time'"'"','"'"'innodb_lock_wait_timeout'"'"'
);" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 024 T1* — Pre-test OK. Iniciando breakpoint test 200u/15min."
```

---

### T2 — Limpiar logs y resetear contadores

```bash
# Limpiar slow log en DB
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
SLOW_LOG="/var/log/mysql/mariadb-slow.log"
cp $SLOW_LOG ${SLOW_LOG}.pre-024 2>/dev/null
> $SLOW_LOG
echo "Slow log limpiado: $(date)"

mysql -u root -p".Overskull2026.m" -e "FLUSH STATUS;" 2>/dev/null

echo "=== Baseline métricas InnoDB ==="
mysql -u root -p".Overskull2026.m" -e "
SHOW GLOBAL STATUS WHERE Variable_name IN (
  '"'"'Innodb_row_lock_waits'"'"',
  '"'"'Innodb_row_lock_time_avg'"'"',
  '"'"'Slow_queries'"'"',
  '"'"'Threads_connected'"'"'
);" 2>/dev/null
'

# Limpiar logs nginx en frontend
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
> /var/log/nginx/error.log 2>/dev/null || true
echo "Nginx error log limpiado"
'
```

```bash
tg_notify "✅ *CDT 024 T2* — Logs limpiados. Contadores reseteados."
```

---

### T3 — Verificar / preparar script Locust

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
LOCUST_DIR="/home/erpnext/locust"
mkdir -p $LOCUST_DIR

echo "=== Scripts existentes ==="
ls -la $LOCUST_DIR/ 2>/dev/null

# Mostrar contenido del script que se usará
SCRIPT=$(ls $LOCUST_DIR/locustfile*.py 2>/dev/null | head -1)
if [ -n "$SCRIPT" ]; then
  echo "=== Usando script existente: $SCRIPT ==="
  cat $SCRIPT
else
  echo "=== No hay script — creando locustfile_024.py ==="
  # Obtener credenciales de API del site_config para autenticación real
  API_KEY=$(python3 -c "
import json
try:
    with open('"'"'/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json'"'"') as f:
        cfg = json.load(f)
    print(cfg.get('"'"'api_key'"'"', '"'"''"'"'))
except: print('"'"''"'"')
" 2>/dev/null)

  cat > $LOCUST_DIR/locustfile_024.py << '"'"'LOCUSTEOF'"'"'
from locust import HttpUser, task, between
import urllib3
urllib3.disable_warnings()

class ERPNextUser(HttpUser):
    wait_time = between(1, 3)
    host = "https://cdtalleres-copia.shalom.com.pe"

    def on_start(self):
        resp = self.client.post(
            "/api/method/login",
            json={"usr": "Administrator", "pwd": "Admin@CDT2024"},
            verify=False,
            name="[login]"
        )

    @task(3)
    def create_orden_trabajo(self):
        self.client.post(
            "/api/resource/Orden%20de%20Trabajo%202",
            json={"doctype": "Orden de Trabajo 2", "company": "CDTalleres SAC"},
            verify=False,
            name="POST /Orden de Trabajo 2"
        )

    @task(2)
    def create_purchase_order(self):
        self.client.post(
            "/api/resource/Purchase%20Order",
            json={
                "doctype": "Purchase Order",
                "company": "CDTalleres SAC",
                "supplier": "Proveedor Test",
                "schedule_date": "2026-06-01",
                "items": [{"item_code": "ITEM-TEST", "qty": 1, "rate": 100}]
            },
            verify=False,
            name="POST /Purchase Order"
        )

    @task(2)
    def create_purchase_invoice(self):
        self.client.post(
            "/api/resource/Purchase%20Invoice",
            json={
                "doctype": "Purchase Invoice",
                "company": "CDTalleres SAC",
                "supplier": "Proveedor Test",
                "posting_date": "2026-04-26",
                "items": [{"item_code": "ITEM-TEST", "qty": 1, "rate": 100}]
            },
            verify=False,
            name="POST /Purchase Invoice"
        )
LOCUSTEOF
  echo "Script creado: $LOCUST_DIR/locustfile_024.py"
fi
'
```

**IMPORTANTE**: Si el script existente del prompt 013 tiene credenciales/datos reales del sistema (como API key Token), usar ese. No reemplazar — solo verificar que el `host` apunte a `cdtalleres-copia.shalom.com.pe`.

```bash
tg_notify "✅ *CDT 024 T3* — Script Locust verificado."
```

---

### T4 — Ejecutar breakpoint test: 200u / ramp 10/s / 15 minutos

**Este test es idéntico al baseline original (prompt 014).** Mismo parámetros, diferente resultado esperado.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
LOCUST_DIR="/home/erpnext/locust"
SCRIPT=$(ls $LOCUST_DIR/locustfile*.py | head -1)
RESULTS_CSV="/tmp/locust_024"

echo "=== BREAKPOINT TEST ==="
echo "Usuarios: 200 | Ramp: 10/s | Duración: 15 minutos"
echo "Mismo parámetros que baseline (prompt 014)"
echo "Script: $SCRIPT"
echo "Inicio: $(date)"

# Ejecutar Locust en background
nohup locust \
  -f $SCRIPT \
  --headless \
  --users 200 \
  --spawn-rate 10 \
  --run-time 15m \
  --csv $RESULTS_CSV \
  --html /tmp/locust_024_report.html \
  --host https://cdtalleres-copia.shalom.com.pe \
  > /tmp/locust_024_output.log 2>&1 &

LOCUST_PID=$!
echo "Locust PID: $LOCUST_PID"
echo $LOCUST_PID > /tmp/locust_024.pid

# Monitoreo cada 60s: capturar métricas DB + backend durante el test
echo "=== Iniciando monitoreo paralelo cada 60s ==="
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  sleep 60
  MINS=$i
  echo ""
  echo "========== MINUTO $MINS =========="

  # Métricas DB
  sshpass -p '"'"'.Overskull2026.m'"'"' ssh -o StrictHostKeyChecking=no root@165.232.130.222 "
mysql -u root -p'.Overskull2026.m' -e \"
SELECT NOW() as tiempo,
  (SELECT variable_value FROM information_schema.global_status WHERE variable_name='Threads_connected') AS threads_conn,
  (SELECT variable_value FROM information_schema.global_status WHERE variable_name='Innodb_row_lock_waits') AS lock_waits,
  (SELECT variable_value FROM information_schema.global_status WHERE variable_name='Innodb_row_lock_time_avg') AS lock_avg_ms,
  (SELECT variable_value FROM information_schema.global_status WHERE variable_name='Slow_queries') AS slow_q;
\" 2>/dev/null" 2>/dev/null

  # CPU backend
  echo "CPU backend:"
  top -bn1 | grep "Cpu(s)" | awk "{print \"  CPU: \" 100-\$8 \"% used\"}"

  # Locust stats en vivo (si tiene endpoint)
  curl -s http://localhost:8089/stats/requests 2>/dev/null | \
    python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    stats = d.get('stats', [])
    for s in stats:
        if s.get('name') != 'Aggregated':
            fail_pct = round(s['num_failures']/max(s['num_requests'],1)*100,1)
            print(f\"  {s['name']}: {s['num_requests']} req | {fail_pct}% fail | p50:{s['response_times'].get('50',0)}ms\")
except: pass
" 2>/dev/null || true

  # ¿Locust sigue corriendo?
  if ! kill -0 $LOCUST_PID 2>/dev/null; then
    echo "Locust terminó en minuto $MINS"
    break
  fi
done

echo "=== Test finalizado: $(date) ==="
echo "=== Output Locust ==="
cat /tmp/locust_024_output.log | tail -30

echo "=== Resultados CSV finales ==="
cat ${RESULTS_CSV}_stats.csv 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 024 T4* — Breakpoint test 200u/15min completado."
```

---

### T5 — Capturar métricas DB post-test

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== Métricas InnoDB post-test ==="
mysql -u root -p".Overskull2026.m" -e "
SHOW GLOBAL STATUS WHERE Variable_name IN (
  '"'"'Innodb_row_lock_waits'"'"',
  '"'"'Innodb_row_lock_time'"'"',
  '"'"'Innodb_row_lock_time_avg'"'"',
  '"'"'Slow_queries'"'"',
  '"'"'Threads_connected'"'"',
  '"'"'Threads_running'"'"',
  '"'"'Questions'"'"'
);" 2>/dev/null

echo "=== Slow queries capturadas ==="
wc -l /var/log/mysql/mariadb-slow.log 2>/dev/null
ls -lh /var/log/mysql/mariadb-slow.log 2>/dev/null

echo "=== Contenido slow log ==="
cat /var/log/mysql/mariadb-slow.log 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 024 T5* — Métricas DB post-test capturadas."
```

---

### T6 — Analizar slow queries

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== Análisis slow queries ==="
python3 << '"'"'PYEOF'"'"'
import re

try:
    with open("/var/log/mysql/mariadb-slow.log") as f:
        content = f.read()

    blocks = re.split(r"# Time:", content)
    queries = []

    for block in blocks[1:]:
        lines = block.strip().split("\n")
        query_time = 0
        lock_time = 0
        rows_examined = 0
        query_text = ""
        for line in lines:
            if "Query_time:" in line:
                m = re.search(r"Query_time: ([\d.]+)", line)
                if m: query_time = float(m.group(1))
                m = re.search(r"Lock_time: ([\d.]+)", line)
                if m: lock_time = float(m.group(1))
                m = re.search(r"Rows_examined: (\d+)", line)
                if m: rows_examined = int(m.group(1))
            if not line.startswith("#") and line.strip() and "SET timestamp" not in line:
                query_text = line.strip()[:300]

        if query_time > 0:
            queries.append((query_time, lock_time, rows_examined, query_text))

    queries.sort(reverse=True)
    print(f"Total slow queries: {len(queries)}")
    if queries:
        print(f"Query_time máximo: {queries[0][0]:.3f}s")
        print(f"Query_time promedio: {sum(q[0] for q in queries)/len(queries):.3f}s")
        print("\nTOP 10 queries más lentas:")
        for i, (t, lt, rows, q) in enumerate(queries[:10], 1):
            print(f"\n[{i}] Query_time:{t:.3f}s | Lock_time:{lt:.3f}s | Rows_examined:{rows}")
            print(f"    {q}")
    else:
        print("Sin slow queries — sistema corrió fluido o log vacío")
except Exception as e:
    print(f"Error: {e}")
PYEOF
'
```

```bash
tg_notify "✅ *CDT 024 T6* — Slow queries analizadas."
```

---

### T7 — EXPLAIN en queries lentas + errores Nginx

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Verificar SEQUENCE no aparece en slow log ==="
grep -i "tabSeries\|FOR UPDATE" /var/log/mysql/mariadb-slow.log 2>/dev/null | wc -l
echo "referencias a tabSeries en slow log (debe ser 0)"

echo "=== Tablas más escaneadas bajo carga ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT table_name,
  ROUND((data_length + index_length)/1024/1024, 1) AS size_mb,
  table_rows
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
ORDER BY size_mb DESC LIMIT 15;" 2>/dev/null
'

# Errores Nginx post-test
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
echo "=== Top errores Nginx ==="
grep "error\|upstream" /var/log/nginx/error.log 2>/dev/null | \
  grep -oP '"'"'(upstream timed out|connect\(\) failed|no live upstreams)[^"]*'"'"' | \
  sort | uniq -c | sort -rn | head -10
echo "Total errores:"
wc -l /var/log/nginx/error.log 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 024 T7* — EXPLAIN y errores Nginx capturados."
```

---

### T8 — Determinar punto de ruptura y comparar vs baseline

Con los datos del monitoreo minuto a minuto (T4) y los resultados Locust (CSV), determinar:

1. **¿En qué minuto/usuario aumentó el fail%?**
2. **¿Cuál fue la causa?** (CPU, RAM, DB locks, Nginx timeout, Gunicorn queue)
3. **¿Llegó a 200u sin colapso?** → si sí: el sistema aguanta, pasar a CDT-027 (test final)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Resultados finales Locust ==="
cat /tmp/locust_024_stats.csv 2>/dev/null

echo "=== Historial de stats por tiempo ==="
cat /tmp/locust_024_stats_history.csv 2>/dev/null | head -40

echo "=== Output completo Locust ==="
cat /tmp/locust_024_output.log 2>/dev/null
'
```

```bash
tg_notify "🏁 *CDT 024 TERMINÓ* — Breakpoint test completado\nVer: c:\\dev\\cdtalleres\\stress-test-50u-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\stress-test-50u-results.md
```

### Estructura obligatoria

```markdown
# Stress Test Breakpoint 200u CDTalleres — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T1. Pre-test verificado | ✅/❌ | gunicorn workers: , DB: OK |
| T2. Logs limpiados | ✅/❌ | — |
| T3. Script Locust listo | ✅/❌ | script: |
| T4. Test 200u/15min ejecutado | ✅/❌ | — |
| T5. Métricas DB capturadas | ✅/❌ | slow_queries: X, lock_avg: Xms |
| T6. Slow queries analizadas | ✅/❌ | total: X |
| T7. EXPLAIN + Nginx errors | ✅/❌ | — |
| T8. Punto de ruptura determinado | ✅/❌ | usuarios: X |

## Resultados Locust — Comparación baseline vs post-optimización

| Endpoint | Baseline fail% | Este test fail% | Mejora |
|---|---|---|---|
| POST /Orden de Trabajo 2 | 96.3% | ? | ? |
| POST /Purchase Order | 95.9% | ? | ? |
| POST /Purchase Invoice | 95.5% | ? | ? |

## Punto de ruptura

- **Baseline**: colapso a ~50-70 usuarios concurrentes
- **Post-optimización**: colapso a ~? usuarios (o aguantó 200u completos)
- **Causa del fallo** (si hubo): CPU / RAM / DB / Nginx / Gunicorn

## Monitoreo minuto a minuto

| Minuto | Usuarios | threads_conn | lock_waits | lock_avg_ms | slow_q | CPU% |
|---|---|---|---|---|---|---|
| 1 | 10 | | | | | |
| 2 | 20 | | | | | |
| ... | ... | | | | | |
| 15 | 200 | | | | | |

## Top Slow Queries identificadas

| # | Query_time | Query | Causa |
|---|---|---|---|
| 1 | | | |

## Errores Nginx

[tipos de error y cantidad]

## Conclusión

[Sistema aguantó X usuarios. Causa de fallo: Y. Próximo paso: Z]

## Bloqueos y errores

[vacío si todo OK]
```
