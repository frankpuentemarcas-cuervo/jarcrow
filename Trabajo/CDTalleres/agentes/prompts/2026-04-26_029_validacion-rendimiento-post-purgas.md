---
fecha: 2026-04-26
agente_id: "029"
descripcion: validacion-rendimiento-post-purgas-stress-200u
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\validacion-rendimiento-results.md"
dependencia: "CDT-TASK-028 ✅ (tabVersion purgada, INSERT: 71,000ms → 10ms)"
tarea_origen: CDT-TASK-029
---

# Validación de Rendimiento Final — Post Todas las Optimizaciones

## Contexto para el agente

Proyecto CDTalleres: ERPNext 3 servidores DigitalOcean. Se han completado **todas** las optimizaciones planificadas. Este prompt valida el rendimiento real del sistema con un stress test idéntico al baseline original.

### Historial completo de optimizaciones aplicadas

| Optimización | Resultado medido |
|---|---|
| Red privada DB `10.124.0.7` | Latencia DB: 1.18ms |
| Gunicorn 5 workers + MariaDB tuning | lock_wait_timeout: 30s |
| Purga tabWorkflow Action 3M→848K | -924MB |
| SEQUENCE OT-2, PO, PI, Historial | lock_time_avg: 14,740ms → 0ms |
| SEQUENCE GL Entry + Stock Ledger Entry | lock_waits: 29 → eliminados |
| **Purga tabVersion 27.7M → 556K filas** | **INSERT: 71,000ms → 10ms / +12.4GB libres** |

### Resultado del test 027 (antes de purgar tabVersion)

- CPU: 94% saturado
- Latencia p50: 71s (causado por INSERTs en tabVersion de 71,000ms)
- Fail%: ~98% (504 Gateway Timeout — Gunicorn queue llena)
- Punto de ruptura: 200u (CPU + tabVersion)

### Objetivo de este prompt

Repetir test **200u / ramp 10/s / 15 minutos** con tabVersion purgada. Con INSERT de 10ms en vez de 71,000ms, Gunicorn ya no se bloquea esperando la DB — esperar una mejora drástica en fail% y latencia.

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

- Target: `https://cdtalleres-copia.shalom.com.pe`
- DB name: `_0646d69b639ad0ff`
- Slow log: `/var/log/mysql/mariadb-slow.log`

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear `c:\dev\cdtalleres\validacion-rendimiento-results.md` y actualizar después de CADA tarea
2. Documentar resultado (✅/❌), métricas exactas, output completo
3. Si el sistema colapsa → NO detener Locust — dejar correr los 15 minutos completos
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
echo "=== Gunicorn workers ==="
ps aux | grep gunicorn | grep -v grep | wc -l
echo "Esperado: 6 (1 master + 5)"

echo "=== RAM disponible ==="
free -h | head -3

echo "=== Test HTTP target ==="
curl -s -o /dev/null -w "HTTP: %{http_code} | tiempo: %{time_total}s\n" \
  https://cdtalleres-copia.shalom.com.pe 2>/dev/null
'

# DB — verificar estado post-purga
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== tabVersion post-purga ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT COUNT(*) AS filas,
  MIN(creation) AS mas_antiguo,
  MAX(creation) AS mas_reciente
FROM tabVersion;" 2>/dev/null

echo "=== Tamaño tabVersion ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name, ROUND((data_length+index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema='"'"'_0646d69b639ad0ff'"'"'
  AND table_name='"'"'tabVersion'"'"';" 2>/dev/null

echo "=== INSERT test tabVersion (confirmar 10ms) ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SET @start = NOW(6);
INSERT INTO tabVersion (name, creation, modified, owner, ref_doctype, docname, data)
VALUES (UUID(), NOW(), NOW(), '"'"'test'"'"', '"'"'Purchase Order'"'"', '"'"'TEST-PRE029'"'"', '"'"'{}'"'"');
SET @end = NOW(6);
SELECT TIMESTAMPDIFF(MICROSECOND, @start, @end)/1000 AS insert_ms;
DELETE FROM tabVersion WHERE docname='"'"'TEST-PRE029'"'"';
" 2>/dev/null

echo "=== SEQUENCES activas ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_schema='"'"'_0646d69b639ad0ff'"'"';" 2>/dev/null

echo "=== Espacio disco ==="
df -h /var/lib/mysql 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 029 T1* — Pre-test OK. tabVersion: 556K filas, INSERT <15ms. Iniciando validación."
```

---

### T2 — Limpiar logs y resetear contadores

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
SLOW_LOG="/var/log/mysql/mariadb-slow.log"
cp $SLOW_LOG ${SLOW_LOG}.pre-029 2>/dev/null
> $SLOW_LOG
echo "Slow log limpiado: $(date)"

mysql -u root -p".Overskull2026.m" -e "FLUSH STATUS;" 2>/dev/null

echo "=== Baseline InnoDB (debe ser 0 tras FLUSH) ==="
mysql -u root -p".Overskull2026.m" -e "
SHOW GLOBAL STATUS WHERE Variable_name IN (
  '"'"'Innodb_row_lock_waits'"'"',
  '"'"'Innodb_row_lock_time_avg'"'"',
  '"'"'Slow_queries'"'"',
  '"'"'Threads_connected'"'"'
);" 2>/dev/null
'

sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
> /var/log/nginx/error.log 2>/dev/null || true
echo "Nginx error log limpiado"
'
```

```bash
tg_notify "✅ *CDT 029 T2* — Logs limpiados. Contadores reseteados."
```

---

### T3 — Verificar script Locust (campo placa obligatorio)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
LOCUST_DIR="/home/erpnext/locust"

echo "=== Scripts disponibles ==="
ls -la $LOCUST_DIR/

SCRIPT=$(ls $LOCUST_DIR/locustfile*.py 2>/dev/null | sort | tail -1)
echo "Script a usar: $SCRIPT"

echo "=== Verificar campo placa en OT-2 ==="
grep -n "placa" $SCRIPT && echo "✅ placa presente" || echo "⚠️ placa AUSENTE — agregar"

echo "=== Host configurado ==="
grep "host" $SCRIPT | head -3
'
```

Si `placa` no está en el script, agregar al payload de OT-2:
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
SCRIPT=$(ls /home/erpnext/locust/locustfile*.py | sort | tail -1)
# Solo si placa no existe en el script:
grep -q "placa" $SCRIPT || \
  sed -i '"'"'s/"company": "CDTalleres SAC"}/"company": "CDTalleres SAC", "placa": "ABC-123"}/'"'"' $SCRIPT
grep "placa" $SCRIPT
'
```

```bash
tg_notify "✅ *CDT 029 T3* — Script Locust verificado."
```

---

### T4 — Ejecutar validación: 200u / ramp 10/s / 15 minutos

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
LOCUST_DIR="/home/erpnext/locust"
SCRIPT=$(ls $LOCUST_DIR/locustfile*.py | sort | tail -1)
RESULTS_CSV="/tmp/locust_029"

echo "=== VALIDACIÓN FINAL ==="
echo "Usuarios: 200 | Ramp: 10/s | Duración: 15 minutos"
echo "Script: $SCRIPT"
echo "Inicio: $(date)"

nohup locust \
  -f $SCRIPT \
  --headless \
  --users 200 \
  --spawn-rate 10 \
  --run-time 15m \
  --csv $RESULTS_CSV \
  --html /tmp/locust_029_report.html \
  --host https://cdtalleres-copia.shalom.com.pe \
  > /tmp/locust_029_output.log 2>&1 &

LOCUST_PID=$!
echo "Locust PID: $LOCUST_PID"
echo $LOCUST_PID > /tmp/locust_029.pid

echo "=== Monitoreo cada 60s ==="
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  sleep 60
  USERS_EXPECTED=$((i * 10))
  [ $USERS_EXPECTED -gt 200 ] && USERS_EXPECTED=200

  echo ""
  echo "========== MINUTO $i (~${USERS_EXPECTED}u) =========="

  # Métricas DB
  sshpass -p '"'"'.Overskull2026.m'"'"' ssh -o StrictHostKeyChecking=no root@165.232.130.222 "
mysql -u root -p'.Overskull2026.m' -e \"
SELECT NOW() as t,
  (SELECT variable_value FROM information_schema.global_status WHERE variable_name='Threads_connected') AS conn,
  (SELECT variable_value FROM information_schema.global_status WHERE variable_name='Innodb_row_lock_waits') AS lock_waits,
  (SELECT variable_value FROM information_schema.global_status WHERE variable_name='Innodb_row_lock_time_avg') AS lock_ms,
  (SELECT variable_value FROM information_schema.global_status WHERE variable_name='Slow_queries') AS slow_q;
\" 2>/dev/null" 2>/dev/null

  # CPU backend
  top -bn1 | grep "Cpu(s)" | awk "{print \"CPU: \" 100-\$8 \"% used\"}"

  # Locust stats
  curl -s http://localhost:8089/stats/requests 2>/dev/null | \
    python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for s in d.get('stats', []):
        if s.get('name') != 'Aggregated':
            fail = round(s['num_failures']/max(s['num_requests'],1)*100,1)
            p50 = s.get('response_times',{}).get('50',0)
            p95 = s.get('response_times',{}).get('95',0)
            print(f\"  {s['name']}: {s['num_requests']}req | {fail}%fail | p50:{p50}ms | p95:{p95}ms\")
except: pass
" 2>/dev/null || true

  if ! kill -0 $LOCUST_PID 2>/dev/null; then
    echo "⚠️ Locust terminó en minuto $i"
    break
  fi
done

echo ""
echo "=== Test finalizado: $(date) ==="
cat /tmp/locust_029_output.log | tail -50
echo "=== CSV final ==="
cat ${RESULTS_CSV}_stats.csv 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 029 T4* — Test 200u/15min completado."
```

---

### T5 — Métricas DB post-test

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== InnoDB post-test ==="
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

echo "=== Slow queries ==="
wc -l /var/log/mysql/mariadb-slow.log 2>/dev/null
ls -lh /var/log/mysql/mariadb-slow.log 2>/dev/null

echo "=== tabSeries en slow log (debe ser 0) ==="
grep -c "tabSeries\|FOR UPDATE" /var/log/mysql/mariadb-slow.log 2>/dev/null || echo 0

echo "=== tabVersion en slow log ==="
grep -c "tabVersion" /var/log/mysql/mariadb-slow.log 2>/dev/null || echo 0

echo "=== INSERT test tabVersion post-carga ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SET @start = NOW(6);
INSERT INTO tabVersion (name, creation, modified, owner, ref_doctype, docname, data)
VALUES (UUID(), NOW(), NOW(), '"'"'test'"'"', '"'"'Purchase Order'"'"', '"'"'TEST-POST029'"'"', '"'"'{}'"'"');
SET @end = NOW(6);
SELECT TIMESTAMPDIFF(MICROSECOND, @start, @end)/1000 AS insert_ms;
DELETE FROM tabVersion WHERE docname='"'"'TEST-POST029'"'"';
" 2>/dev/null
'
```

---

### T6 — Errores Nginx + comparación final

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
echo "=== Top errores Nginx ==="
grep "error\|upstream" /var/log/nginx/error.log 2>/dev/null | \
  grep -oP '"'"'(upstream timed out|connect\(\) failed|no live upstreams|504)[^"]*'"'"' | \
  sort | uniq -c | sort -rn | head -10
echo "Total líneas error log:"
wc -l /var/log/nginx/error.log 2>/dev/null
'

sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Stats history Locust ==="
cat /tmp/locust_029_stats_history.csv 2>/dev/null | head -40
'
```

```bash
tg_notify "🏁 *CDT 029 TERMINÓ* — Validación rendimiento completada\nVer: c:\\dev\\cdtalleres\\validacion-rendimiento-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\validacion-rendimiento-results.md
```

### Estructura obligatoria

```markdown
# Validación Rendimiento Post-Optimizaciones — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T1. Pre-test verificado | ✅/❌ | tabVersion: 556K filas, INSERT: Xms |
| T2. Logs limpiados | ✅/❌ | — |
| T3. Script Locust verificado | ✅/❌ | placa: presente/ausente |
| T4. Test 200u/15min ejecutado | ✅/❌ | — |
| T5. Métricas DB post-test | ✅/❌ | lock_waits: X, lock_avg: Xms |
| T6. Nginx + comparación final | ✅/❌ | — |

## Comparación completa — Baseline vs Todas las Optimizaciones

| Métrica | Baseline (014) | Post-SEQUENCE (027) | Post-tabVersion (029) |
|---|---|---|---|
| INSERT tabVersion (ms) | ~71,000 | ~71,000 | ~10 |
| lock_time_avg (ms) | 14,740 | 3,500 | ? |
| lock_waits | alto | 29 | ? |
| OT-2 fail% | 96.3% | ? | ? |
| PO fail% | 95.9% | ? | ? |
| PI fail% | 95.5% | ? | ? |
| CPU max backend | ? | 94% | ? |
| Latencia p50 | ? | 71s | ? |
| Punto ruptura | 50-70u | 200u (CPU+tabVersion) | ? |

## Monitoreo minuto a minuto

| Minuto | Usuarios | conn | lock_waits | lock_ms | slow_q | CPU% |
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

## Conclusión

[Sistema aguantó X usuarios con Y% fail. Mejora total vs baseline: Z. Próximo paso: ...]

## Bloqueos y errores

[vacío si todo OK]
```
