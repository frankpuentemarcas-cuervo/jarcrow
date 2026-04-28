---
fecha: 2026-04-26
agente_id: "027"
descripcion: stress-test-final-validacion-completa-200u
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\stress-test-final-results.md"
dependencia: "CDT-TASK-025 ✅"
tarea_origen: CDT-TASK-027
---

# Stress Test Final 200u — Validación Completa Post-Optimizaciones

## Contexto para el agente

Proyecto CDTalleres: ERPNext con 3 servidores DigitalOcean. Este es el test de validación final — se han aplicado **todas** las optimizaciones planificadas y hay que confirmar el nuevo punto de ruptura.

### Historial de optimizaciones (estado completo al 2026-04-26)

| Optimización | Tarea | Estado |
|---|---|---|
| Red privada DB por IP `10.124.0.7` | CDT-020 | ✅ |
| Grafana + Locust dashboards | CDT-021 | ✅ |
| Gunicorn 5 workers + MariaDB tuning | CDT-022 | ✅ |
| Purga tabWorkflow Action 3M→848K filas | CDT-023 | ✅ |
| SEQUENCE para OT-2, PO, PI, Historial | CDT-018/022 | ✅ |
| SEQUENCE para GL Entry + Stock Ledger Entry | CDT-025 | ✅ |

### Resultado del test anterior (prompt 024 — primer test post-opt)

- Sistema colapsó a **200u** (mismo que baseline)
- Causa: **CPU 94%**, Gunicorn 6 workers saturados (p50 latency 71s)
- DB locks: `29 lock_waits`, `lock_time_avg 3,500ms` → causado por ACC-GLE y MAT-SLE
- **Desde entonces**: CDT-025 migró GL Entry + SLE a SEQUENCE → locks DB eliminados

### Objetivo de este prompt

Repetir test 200u/ramp 10/s/15min con todas las optimizaciones activas incluyendo CDT-025. Determinar:
1. ¿Bajaron los lock_waits a 0?
2. ¿Sigue siendo CPU el cuello de botella?
3. ¿Cuál es el nuevo fail% en OT-2, PO, PI?
4. ¿El sistema aguanta 200u completos?

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
- Dashboard Node Exporter: `http://164.92.94.47:3000/d/rYdddlPWk/node-exporter-full`
- Dashboard MySQL: `http://164.92.94.47:3000/d/MQWgroiiz/mysql-overview`

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear `c:\dev\cdtalleres\stress-test-final-results.md` y actualizar después de CADA tarea
2. Documentar resultado (✅/❌), métricas exactas, output completo
3. Si el sistema colapsa → NO detener Locust — dejar correr los 15 minutos para capturar punto exacto
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

### T1 — Verificar estado pre-test + SEQUENCES activas

```bash
# Backend
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Locust disponible ==="
which locust && locust --version

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

# DB — verificar SEQUENCES de CDT-025
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== MariaDB estado ==="
systemctl status mariadb --no-pager | head -5

echo "=== SEQUENCES activas (deben incluir seq_gl_entry y seq_stock_ledger) ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_schema = '"'"'_0646d69b639ad0ff'"'"';" 2>/dev/null

echo "=== autoname GL Entry y SLE (deben ser Prompt) ==="
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, autoname FROM tabDocType
WHERE name IN ('"'"'GL Entry'"'"', '"'"'Stock Ledger Entry'"'"', '"'"'Orden de Trabajo 2'"'"', '"'"'Purchase Order'"'"', '"'"'Purchase Invoice'"'"');" 2>/dev/null

echo "=== Server Scripts activos ==="
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, dt, event, enabled FROM '"'"'tabServer Script'"'"'
WHERE name LIKE '"'"'%SEQUENCE%'"'"' OR name LIKE '"'"'%seq%'"'"'
ORDER BY name;" 2>/dev/null

echo "=== Conexiones actuales ==="
mysql -u root -p".Overskull2026.m" -e "SHOW STATUS LIKE '"'"'Threads_connected'"'"';" 2>/dev/null

echo "=== innodb_lock_wait_timeout ==="
mysql -u root -p".Overskull2026.m" -e "SHOW VARIABLES LIKE '"'"'innodb_lock_wait_timeout'"'"';" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 027 T1* — Pre-test OK. SEQUENCES verificadas. Iniciando test final 200u/15min."
```

---

### T2 — Limpiar logs y resetear contadores

```bash
# Limpiar slow log en DB
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
SLOW_LOG="/var/log/mysql/mariadb-slow.log"
cp $SLOW_LOG ${SLOW_LOG}.pre-027 2>/dev/null
> $SLOW_LOG
echo "Slow log limpiado: $(date)"

mysql -u root -p".Overskull2026.m" -e "FLUSH STATUS;" 2>/dev/null

echo "=== Baseline métricas InnoDB (deben ser 0 tras FLUSH) ==="
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
tg_notify "✅ *CDT 027 T2* — Logs limpiados. Contadores reseteados."
```

---

### T3 — Verificar / preparar script Locust

Usar el script del prompt 024 (`locustfile_024.py`) si existe. **IMPORTANTE**: verificar que el payload de OT-2 incluya el campo `placa` (fue la causa del HTTP 417 en el test 024).

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
LOCUST_DIR="/home/erpnext/locust"
mkdir -p $LOCUST_DIR

echo "=== Scripts existentes ==="
ls -la $LOCUST_DIR/ 2>/dev/null

# Mostrar contenido del script a usar
SCRIPT=$(ls $LOCUST_DIR/locustfile*.py 2>/dev/null | sort | tail -1)
if [ -n "$SCRIPT" ]; then
  echo "=== Script encontrado: $SCRIPT ==="
  cat $SCRIPT
  
  echo ""
  echo "=== Verificar campo placa en OT-2 payload ==="
  grep -n "placa" $SCRIPT && echo "✅ placa presente" || echo "⚠️ placa NO encontrado — agregar al payload"
else
  echo "=== No hay script — creando locustfile_027.py ==="
  
  # Obtener token API del site_config
  API_KEY=$(mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff \
    -e "SELECT api_key FROM tabUser WHERE name='"'"'Administrator'"'"';" \
    -ss 2>/dev/null | head -1)
  
  cat > $LOCUST_DIR/locustfile_027.py << '"'"'LOCUSTEOF'"'"'
from locust import HttpUser, task, between
import urllib3
urllib3.disable_warnings()

class ERPNextUser(HttpUser):
    wait_time = between(1, 3)
    host = "https://cdtalleres-copia.shalom.com.pe"

    def on_start(self):
        self.client.post(
            "/api/method/login",
            json={"usr": "Administrator", "pwd": "Admin@CDT2024"},
            verify=False,
            name="[login]"
        )

    @task(3)
    def create_orden_trabajo(self):
        self.client.post(
            "/api/resource/Orden%20de%20Trabajo%202",
            json={
                "doctype": "Orden de Trabajo 2",
                "company": "CDTalleres SAC",
                "placa": "ABC-123"
            },
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
  echo "Script creado: $LOCUST_DIR/locustfile_027.py"
  SCRIPT="$LOCUST_DIR/locustfile_027.py"
fi

echo "=== Script listo: $SCRIPT ==="
'
```

```bash
tg_notify "✅ *CDT 027 T3* — Script Locust verificado (placa OK)."
```

---

### T4 — Ejecutar test final: 200u / ramp 10/s / 15 minutos

**Mismo parámetros que baseline original (prompt 014) y test 024. Tercera y última comparación.**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
LOCUST_DIR="/home/erpnext/locust"
SCRIPT=$(ls $LOCUST_DIR/locustfile*.py | sort | tail -1)
RESULTS_CSV="/tmp/locust_027"

echo "=== STRESS TEST FINAL ==="
echo "Usuarios: 200 | Ramp: 10/s | Duración: 15 minutos"
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
  --html /tmp/locust_027_report.html \
  --host https://cdtalleres-copia.shalom.com.pe \
  > /tmp/locust_027_output.log 2>&1 &

LOCUST_PID=$!
echo "Locust PID: $LOCUST_PID"
echo $LOCUST_PID > /tmp/locust_027.pid

# Monitoreo minuto a minuto — 15 iteraciones
echo "=== Iniciando monitoreo paralelo cada 60s ==="
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  sleep 60
  MINS=$i
  USERS_EXPECTED=$((i * 10))
  [ $USERS_EXPECTED -gt 200 ] && USERS_EXPECTED=200

  echo ""
  echo "========== MINUTO $MINS (esperado ~${USERS_EXPECTED}u) =========="

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

  # Locust stats en vivo
  curl -s http://localhost:8089/stats/requests 2>/dev/null | \
    python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    stats = d.get('stats', [])
    for s in stats:
        if s.get('name') != 'Aggregated':
            fail_pct = round(s['num_failures']/max(s['num_requests'],1)*100,1)
            p50 = s.get('response_times', {}).get('50', 0)
            p95 = s.get('response_times', {}).get('95', 0)
            print(f\"  {s['name']}: {s['num_requests']} req | {fail_pct}% fail | p50:{p50}ms | p95:{p95}ms\")
except: pass
" 2>/dev/null || true

  # ¿Locust sigue corriendo?
  if ! kill -0 $LOCUST_PID 2>/dev/null; then
    echo "⚠️ Locust terminó prematuramente en minuto $MINS"
    break
  fi
done

echo ""
echo "=== Test finalizado: $(date) ==="
echo "=== Output Locust final ==="
cat /tmp/locust_027_output.log | tail -50

echo "=== Resultados CSV ==="
cat ${RESULTS_CSV}_stats.csv 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 027 T4* — Test 200u/15min completado."
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

echo ""
echo "=== Comparación vs test 024 ==="
echo "Test 024 (pre-CDT-025): lock_waits=29, lock_avg=3500ms"
echo "Test 027 (post-CDT-025): ver Innodb_row_lock_waits arriba"

echo ""
echo "=== Slow queries capturadas ==="
wc -l /var/log/mysql/mariadb-slow.log 2>/dev/null
ls -lh /var/log/mysql/mariadb-slow.log 2>/dev/null

echo ""
echo "=== Contenido slow log ==="
cat /var/log/mysql/mariadb-slow.log 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 027 T5* — Métricas DB post-test capturadas."
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
        print("✅ Sin slow queries — sistema corrió fluido")
except Exception as e:
    print(f"Error: {e}")
PYEOF

echo ""
echo "=== Verificar que tabSeries NO aparece en slow log ==="
TABSERIES_REFS=$(grep -c "tabSeries\|FOR UPDATE" /var/log/mysql/mariadb-slow.log 2>/dev/null || echo 0)
echo "Referencias tabSeries en slow log: $TABSERIES_REFS (debe ser 0)"

echo ""
echo "=== Verificar que GLE y SLE usan SEQUENCE ==="
SEQUENCE_REFS=$(grep -c "seq_gl_entry\|seq_stock_ledger\|NEXTVAL" /var/log/mysql/mariadb-slow.log 2>/dev/null || echo 0)
echo "Referencias SEQUENCE en slow log: $SEQUENCE_REFS"
'
```

```bash
tg_notify "✅ *CDT 027 T6* — Slow queries analizadas."
```

---

### T7 — EXPLAIN en queries lentas + errores Nginx

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Tablas más grandes post-test ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT table_name,
  ROUND((data_length + index_length)/1024/1024, 1) AS size_mb,
  table_rows
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
ORDER BY size_mb DESC LIMIT 15;" 2>/dev/null

echo ""
echo "=== Verificar SEQUENCE GL Entry actual ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT NEXTVAL(seq_gl_entry) AS next_gle,
       NEXTVAL(seq_stock_ledger) AS next_sle;" 2>/dev/null
'

# Errores Nginx post-test
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
echo "=== Top errores Nginx ==="
grep "error\|upstream" /var/log/nginx/error.log 2>/dev/null | \
  grep -oP '"'"'(upstream timed out|connect\(\) failed|no live upstreams)[^"]*'"'"' | \
  sort | uniq -c | sort -rn | head -10
echo "Total líneas error log:"
wc -l /var/log/nginx/error.log 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 027 T7* — EXPLAIN y errores Nginx capturados."
```

---

### T8 — Comparar vs baseline y determinar conclusión final

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Resultados finales Locust ==="
cat /tmp/locust_027_stats.csv 2>/dev/null

echo ""
echo "=== Historial stats por tiempo ==="
cat /tmp/locust_027_stats_history.csv 2>/dev/null | head -40

echo ""
echo "=== Output completo Locust ==="
cat /tmp/locust_027_output.log 2>/dev/null
'
```

Con los datos anteriores, completar la comparación final:

| Métrica | Baseline (014) | Test 024 (post-020-023) | Test 027 (post-025) |
|---|---|---|---|
| lock_waits | ~14,740ms avg | 29 waits / 3,500ms | ? |
| CPU máximo | ? | 94% | ? |
| OT-2 fail% | 96.3% | ? | ? |
| PO fail% | 95.9% | ? | ? |
| PI fail% | 95.5% | ? | ? |
| Punto ruptura | 50-70u | 200u (CPU) | ? |

```bash
tg_notify "🏁 *CDT 027 TERMINÓ* — Stress test final completado\nVer: c:\\dev\\cdtalleres\\stress-test-final-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\stress-test-final-results.md
```

### Estructura obligatoria

```markdown
# Stress Test Final 200u CDTalleres — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T1. Pre-test + SEQUENCES verificadas | ✅/❌ | seq_gl_entry: OK / seq_stock_ledger: OK |
| T2. Logs limpiados | ✅/❌ | — |
| T3. Script Locust listo | ✅/❌ | placa campo presente: sí/no |
| T4. Test 200u/15min ejecutado | ✅/❌ | — |
| T5. Métricas DB capturadas | ✅/❌ | lock_waits: X, lock_avg: Xms |
| T6. Slow queries analizadas | ✅/❌ | total: X, tabSeries refs: 0 |
| T7. EXPLAIN + Nginx errors | ✅/❌ | — |
| T8. Comparación final completa | ✅/❌ | — |

## Comparación final — Baseline vs Optimizaciones

| Métrica | Baseline (014) | Post-020-023 (024) | Post-025 (027) | Mejora total |
|---|---|---|---|---|
| lock_time_avg | 14,740ms | 3,500ms | ? | ? |
| lock_waits | alto | 29 | ? | ? |
| OT-2 fail% | 96.3% | ? | ? | ? |
| PO fail% | 95.9% | ? | ? | ? |
| PI fail% | 95.5% | ? | ? | ? |
| CPU max | ? | 94% | ? | ? |
| Punto ruptura | 50-70u | 200u (CPU) | ? | ? |

## Monitoreo minuto a minuto

| Minuto | Usuarios | threads_conn | lock_waits | lock_avg_ms | slow_q | CPU% |
|---|---|---|---|---|---|---|
| 1 | 10 | | | | | |
| 2 | 20 | | | | | |
| 3 | 30 | | | | | |
| 4 | 40 | | | | | |
| 5 | 50 | | | | | |
| 6 | 60 | | | | | |
| 7 | 70 | | | | | |
| 8 | 80 | | | | | |
| 9 | 90 | | | | | |
| 10 | 100 | | | | | |
| 11 | 110 | | | | | |
| 12 | 120 | | | | | |
| 13 | 130 | | | | | |
| 14 | 140 | | | | | |
| 15 | 200 | | | | | |

## Top Slow Queries identificadas

| # | Query_time | Lock_time | Rows_examined | Query |
|---|---|---|---|---|
| 1 | | | | |

## Errores Nginx

[tipos de error y cantidad]

## Conclusión final

[Sistema aguantó X usuarios con Y% fail. DB locks: Z ms (antes 14,740ms). Cuello de botella: A. Recomendación: B]

## Bloqueos y errores

[vacío si todo OK]
```
