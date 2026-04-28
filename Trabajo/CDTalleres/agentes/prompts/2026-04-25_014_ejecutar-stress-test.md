---
fecha: 2026-04-25
agente_id: "014"
descripcion: ejecutar-stress-test-diagnostico-colapso
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: completado
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\stress-test-results.md"
dependencia: "013 (Locust + script listos, usuario API verificado)"
---

# Ejecutar Stress Test Diagnóstico — CDTalleres

## Contexto para el agente

Proyecto CDTalleres stress test diagnóstico. Todo el stack está listo:
- Exporters corriendo en 3 servidores (prompt 011)
- Prometheus + Grafana activos en Backend (prompt 012)
- Locust + script instalados (prompt 013)

**Objetivo**: Forzar colapso a 200 usuarios concurrentes, capturar métricas en tiempo real, identificar qué falla primero y a qué concurrencia.

### Parámetros del test

| Parámetro | Valor |
|---|---|
| Usuarios máximos | 200 |
| Ramp-up rate | 10 usuarios/segundo |
| Duración total | 15 minutos |
| Host target | https://cdtalleres-copia.shalom.com.pe |
| Script | /opt/cdtalleres-stress/locustfile.py |

### Servidores

| Rol | IP | Credenciales |
|---|---|---|
| Backend (Locust + Prometheus + Grafana) | 164.92.94.47 | root / .Overskull2026.m |
| DB | 165.232.130.222 | root / .Overskull2026.m |
| Frontend | 209.38.75.235 | root / .Overskull2026.m |

### Indicadores de colapso a vigilar

| Síntoma | Causa probable |
|---|---|
| Error rate >10% con HTTP 500 | Gunicorn workers saturados |
| Latencia p99 >10s | tabSeries lock contention |
| threads_connected MariaDB >150 | max_connections alcanzado |
| innodb_row_lock_waits creciente | SELECT FOR UPDATE en tabSeries |
| CPU Backend >90% | Workers Python agotados |
| HTTP 502/504 desde Nginx | Gunicorn muerto o timeout |

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

---

## Tareas a ejecutar

### 1. Snapshot pre-test — estado baseline antes del test

```bash
# BASELINE en los 3 servidores antes de lanzar carga
for IP in 209.38.75.235 164.92.94.47 165.232.130.222; do
  echo "=== BASELINE $IP ==="
  sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@$IP \
    'echo "CPU:"; top -bn1 | head -4; echo "RAM:"; free -h | head -2; echo "Load:"; uptime; echo "Conexiones:"; ss -s | grep -E "Total|TCP"' 2>/dev/null
done

# Baseline MariaDB
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "
  SHOW GLOBAL STATUS LIKE '"'"'Threads_connected'"'"';
  SHOW GLOBAL STATUS LIKE '"'"'Innodb_row_lock_waits'"'"';
  SHOW GLOBAL STATUS LIKE '"'"'Innodb_row_lock_time_avg'"'"';
  SELECT name, current FROM tabSeries ORDER BY current DESC LIMIT 5;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "📋 *CDT T1* — Baseline capturado pre-test\nLanzando stress test en 30s..."
```

---

### 2. Lanzar monitor de métricas DB en background (durante el test)

```bash
# En servidor DB: capturar métricas cada 15s durante el test
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
cat > /tmp/monitor_db.sh << '"'"'MONITOR_EOF'"'"'
#!/bin/bash
LOG=/tmp/db_stress_monitor.log
echo "timestamp,threads_connected,row_lock_waits,row_lock_time_avg,processlist_count" > $LOG
for i in $(seq 1 60); do
  TS=$(date +"%H:%M:%S")
  STATS=$(mysql -u root -p".Overskull2026.m" -sN -e "
    SELECT 
      (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='"'"'Threads_connected'"'"') AS tc,
      (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='"'"'Innodb_row_lock_waits'"'"') AS rlw,
      (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='"'"'Innodb_row_lock_time_avg'"'"') AS rlta,
      (SELECT COUNT(*) FROM information_schema.processlist WHERE command != '"'"'Sleep'"'"') AS pl
    " 2>/dev/null | tr "\t" ",")
  echo "$TS,$STATS" | tee -a $LOG
  sleep 15
done
echo "Monitor DB finalizado. Log: $LOG"
MONITOR_EOF
chmod +x /tmp/monitor_db.sh
nohup /tmp/monitor_db.sh > /tmp/monitor_db_out.log 2>&1 &
echo "Monitor DB PID: $!"
'
```

---

### 3. Lanzar monitor sistema en Backend en background

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
cat > /tmp/monitor_backend.sh << '"'"'MON_EOF'"'"'
#!/bin/bash
LOG=/tmp/backend_stress_monitor.log
echo "timestamp,cpu_pct,mem_used_mb,gunicorn_procs,connections" > $LOG
for i in $(seq 1 60); do
  TS=$(date +"%H:%M:%S")
  CPU=$(top -bn1 | grep "Cpu(s)" | awk '"'"'{print $2}'"'"' | cut -d'"'"'%'"'"' -f1)
  MEM=$(free -m | awk '"'"'/Mem:/{print $3}'"'"')
  GUNI=$(ps aux | grep gunicorn | grep -v grep | wc -l)
  CONN=$(ss -tn | grep ESTAB | wc -l)
  echo "$TS,$CPU,$MEM,$GUNI,$CONN" | tee -a $LOG
  sleep 15
done
echo "Monitor Backend finalizado"
MON_EOF
chmod +x /tmp/monitor_backend.sh
nohup /tmp/monitor_backend.sh > /tmp/monitor_backend_out.log 2>&1 &
echo "Monitor Backend PID: $!"
'
```

---

### 4. EJECUTAR STRESS TEST — Locust 200 usuarios, 15 minutos

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
cd /opt/cdtalleres-stress
mkdir -p /opt/cdtalleres-stress/results

echo "=== INICIANDO STRESS TEST ==="
echo "Usuarios: 200 | Ramp-up: 10/s | Duración: 15min"
echo "Target: https://cdtalleres-copia.shalom.com.pe"
echo "Start: $(date)"

locust \
  --locustfile locustfile.py \
  --host https://cdtalleres-copia.shalom.com.pe \
  --users 200 \
  --spawn-rate 10 \
  --run-time 15m \
  --headless \
  --csv /opt/cdtalleres-stress/results/stress_test \
  --html /opt/cdtalleres-stress/results/stress_report.html \
  --logfile /opt/cdtalleres-stress/results/locust.log \
  2>&1 | tee /opt/cdtalleres-stress/results/locust_stdout.log

echo "End: $(date)"
echo "=== TEST COMPLETADO ==="
'
```

**NOTA:** Este comando tarda ~15 minutos. Esperar a que complete.

Notificar al iniciar y al terminar:
```bash
# Al iniciar:
tg_notify "🚀 *CDT STRESS TEST INICIADO* — 200 usuarios contra cdtalleres-copia.shalom.com.pe\nDuración: 15 min\nGrafana: http://164.92.94.47:3000"

# Al terminar:
tg_notify "🏁 *CDT STRESS TEST TERMINÓ* — Procesando resultados..."
```

---

### 5. Capturar snapshot post-test — estado del sistema tras el colapso

```bash
# Estado de los 3 servidores después del test
for IP in 209.38.75.235 164.92.94.47 165.232.130.222; do
  echo "=== POST-TEST $IP ==="
  sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@$IP \
    'uptime; free -h | head -2; ss -s | grep -E "Total|TCP"; dmesg | tail -5 | grep -i "error\|oom\|killed" 2>/dev/null || true' 2>/dev/null
done

# Estado MariaDB post-test
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "
  SHOW GLOBAL STATUS LIKE '"'"'Threads_connected'"'"';
  SHOW GLOBAL STATUS LIKE '"'"'Innodb_row_lock_waits'"'"';
  SHOW GLOBAL STATUS LIKE '"'"'Innodb_row_lock_time_avg'"'"';
  SHOW GLOBAL STATUS LIKE '"'"'Aborted_connects'"'"';
  SHOW GLOBAL STATUS LIKE '"'"'Connection_errors_max_connections'"'"';
  SHOW GLOBAL STATUS LIKE '"'"'Max_used_connections'"'"';
  SELECT name, current FROM tabSeries ORDER BY current DESC LIMIT 10;
" 2>/dev/null

echo "=== MONITOR DB LOG ==="
cat /tmp/db_stress_monitor.log 2>/dev/null
'

# Estado supervisor/Gunicorn en Frontend
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
supervisorctl status 2>/dev/null
tail -30 /home/erpnext/frappe-bench/logs/web.error.log 2>/dev/null || echo "sin web.error.log"
tail -20 /var/log/nginx/error.log 2>/dev/null
'
```

---

### 6. Recopilar y analizar resultados Locust

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== RESULTADOS LOCUST ==="
ls -lh /opt/cdtalleres-stress/results/

echo ""
echo "=== STATS SUMMARY ==="
cat /opt/cdtalleres-stress/results/stress_test_stats.csv 2>/dev/null

echo ""
echo "=== FAILURES ==="
cat /opt/cdtalleres-stress/results/stress_test_failures.csv 2>/dev/null

echo ""
echo "=== ERRORES EN LOG ==="
grep -E "ERROR|FAIL|Exception|timeout" /opt/cdtalleres-stress/results/locust.log 2>/dev/null | tail -30

echo ""
echo "=== MONITOR BACKEND ==="
cat /tmp/backend_stress_monitor.log 2>/dev/null
'
```

---

### 7. Análisis diagnóstico — identificar cuello de botella

Con todos los datos recopilados, analizar y documentar:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== ANÁLISIS AUTOMÁTICO ==="

# Leer CSV de stats y calcular métricas clave
python3 << '"'"'PYEOF'"'"'
import csv, os

stats_file = "/opt/cdtalleres-stress/results/stress_test_stats.csv"
if os.path.exists(stats_file):
    with open(stats_file) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"Total endpoints testeados: {len(rows)}")
    for row in rows:
        name = row.get("Name", "?")
        reqs = row.get("Request Count", "?")
        fails = row.get("Failure Count", "?")
        p50 = row.get("50%", "?")
        p95 = row.get("95%", "?")
        p99 = row.get("99%", "?")
        avg = row.get("Average (ms)", "?")
        try:
            fail_pct = float(fails) / float(reqs) * 100 if float(reqs) > 0 else 0
        except:
            fail_pct = 0
        print(f"\n  {name}:")
        print(f"    Requests: {reqs} | Failures: {fails} ({fail_pct:.1f}%)")
        print(f"    Latencia: p50={p50}ms p95={p95}ms p99={p99}ms avg={avg}ms")
else:
    print(f"No se encontró {stats_file}")
PYEOF
'
```

Notificar con diagnóstico:
```bash
# Construir mensaje con hallazgo principal
tg_notify "📊 *CDT 014 — DIAGNÓSTICO STRESS TEST*

Ver reporte completo: c:\\dev\\cdtalleres\\stress-test-results.md
Grafana histórico: http://164.92.94.47:3000"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\stress-test-results.md
```

### Estructura obligatoria

```markdown
# Stress Test CDTalleres — YYYY-MM-DD HH:MM

## Parámetros ejecutados

- Usuarios máximos: 200
- Ramp-up: 10/s
- Duración: 15 minutos
- Target: https://cdtalleres-copia.shalom.com.pe

## Resultados Locust por endpoint

| Endpoint | Requests | Failures | Fail% | p50 | p95 | p99 |
|---|---|---|---|---|---|---|
| POST /Purchase Order | N | N | N% | Nms | Nms | Nms |
| POST /Purchase Invoice | N | N | N% | Nms | Nms | Nms |
| POST /Orden de Trabajo 2 | N | N | N% | Nms | Nms | Nms |
| POST /Solicitud de Pagos | N | N | N% | Nms | Nms | Nms |
| GET /Purchase Order list | N | N | N% | Nms | Nms | Nms |

## Métricas MariaDB durante el test

| Tiempo | threads_connected | row_lock_waits | row_lock_time_avg | processlist |
|---|---|---|---|---|
| [baseline] | N | N | Nms | N |
| [peak] | N | N | Nms | N |
| [post-test] | N | N | Nms | N |

## Métricas sistema Backend durante el test

| Tiempo | CPU% | RAM MB | Gunicorn procs | Conexiones ESTAB |
|---|---|---|---|---|
| [baseline] | N | N | N | N |
| [peak] | N | N | N | N |

## tabSeries — contadores antes vs después

| Serie | Antes | Después | Delta |
|---|---|---|---|
| Orden-Trabajo- | N | N | +N |
| ACC-PINV- | N | N | +N |

## Errores de Nginx/Gunicorn post-test

[contenido de error.log]

## Estado servicios post-test

[supervisorctl status]

## Diagnóstico — Cuello de botella identificado

### ¿Qué falló primero?
[OBLIGATORIO — describir con evidencia de métricas]

### ¿A qué concurrencia colapsó?
[N usuarios — métrica que lo confirma]

### Causa raíz
[tabSeries locks / Gunicorn queue / MariaDB connections / Red / otro]

### Recomendaciones priorizadas
1. [Fix crítico]
2. [Fix secundario]
3. [Fix opcional]

## Bloqueos y errores de ejecución
[OBLIGATORIO — vacío si todo fue bien]
```
