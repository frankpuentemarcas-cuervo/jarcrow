---
fecha: 2026-04-25
agente_id: "005"
descripcion: profiling-performance-mariadb
proyecto: CDTalleres
ia_destino: antigravity
tipo: debug
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\performance-profiling-results.md"
dependencia: "003 y 004 deben completarse primero"
---

# Profiling de Performance — MariaDB y tabSeries

## Contexto para el agente

Proyecto CDTalleres (ERPNext v13.9.2 / Frappe 13.9.1 para Shalom / Overskull). Estamos investigando demoras en producción que NO aparecen en logs estándar. La sospecha principal es contención en la tabla `tabSeries` (Naming Series de Frappe) por `SELECT FOR UPDATE` bajo alta concurrencia.

### Servidores

| Rol | IP | Usuario | Password |
|---|---|---|---|
| Backend | 164.92.94.47 | root | .Overskull2026.m |
| DB | 165.232.130.222 | root | .Overskull2026.m |
| Frontend | 209.38.75.235 | root | .Overskull2026.m |

- **Bench path**: `/home/erpnext/frappe-bench`
- **Site**: `CDTALLERES`
- **MariaDB**: 10.4.21 en servidor DB
- **Apps custom**: `notification`, `scanpda` (DocTypes propios que probablemente usan Naming Series)

### Problema
Frappe usa `tabSeries` para numeración automática de documentos. Cada nuevo documento hace `SELECT ... FOR UPDATE` sobre esa tabla → bajo carga concurrente genera row locks → esperas no visibles en logs Frappe.

---

## ⚠️ REGLA CRÍTICA — Reporte de bloqueos

**SIEMPRE, ante cualquier error, bloqueo o impedimento:**

1. Genera el archivo de salida con lo que tengas hasta ese momento
2. Documenta el problema en la sección `## Bloqueos y errores`
3. Incluye: qué intentaste, error EXACTO, alternativas probadas, qué se necesita

**Nunca termines sin generar el archivo de salida.** Aunque sea parcial.

---

## Tareas a ejecutar

### 1. Habilitar slow query log en MariaDB

En servidor DB (165.232.130.222):

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root << EOF
-- Habilitar slow query log
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 0.5;
SET GLOBAL slow_query_log_file = "/var/log/mysql/slow-queries.log";
SET GLOBAL log_queries_not_using_indexes = ON;

-- Verificar
SHOW VARIABLES LIKE "slow_query%";
SHOW VARIABLES LIKE "long_query_time";
EOF
'
```

### 2. Analizar tabSeries — estado actual

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root << EOF
USE \`CDTALLERES\`;

-- Ver todas las series y su contador actual
SELECT name, current FROM tabSeries ORDER BY current DESC LIMIT 30;

-- Cuántas series existen
SELECT COUNT(*) as total_series FROM tabSeries;

-- Ver DocTypes con naming series (los que generan locks)
SELECT dt.name, dt.autoname
FROM tabDocType dt
WHERE dt.autoname LIKE "%.####%" OR dt.autoname LIKE "%series%"
ORDER BY dt.name;
EOF
'
```

### 3. Analizar InnoDB — locks y estado

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root << EOF
-- Status de InnoDB (buscar lock waits)
SHOW ENGINE INNODB STATUS\G

-- Variables clave de performance
SHOW GLOBAL VARIABLES LIKE "innodb_buffer_pool_size";
SHOW GLOBAL VARIABLES LIKE "innodb_flush%";
SHOW GLOBAL VARIABLES LIKE "max_connections";
SHOW GLOBAL VARIABLES LIKE "thread_cache_size";

-- Status actual de conexiones y locks
SHOW GLOBAL STATUS LIKE "Threads_connected";
SHOW GLOBAL STATUS LIKE "Threads_running";
SHOW GLOBAL STATUS LIKE "Innodb_row_lock%";
SHOW GLOBAL STATUS LIKE "Innodb_buffer_pool%";

-- Procesos activos
SHOW FULL PROCESSLIST;
EOF
'
```

### 4. Revisar logs de Frappe en servidor Backend

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
BENCH=/home/erpnext/frappe-bench

echo "=== ÚLTIMAS 50 LÍNEAS web.log ==="
tail -50 $BENCH/logs/web.log 2>/dev/null

echo "=== ÚLTIMAS 50 LÍNEAS worker.log ==="
tail -50 $BENCH/logs/worker.log 2>/dev/null

echo "=== ERRORES EN LOGS (últimas 100 líneas) ==="
tail -100 $BENCH/logs/frappe.log 2>/dev/null | grep -iE "(error|exception|timeout|lock|slow)"

echo "=== GUNICORN WORKERS ==="
ps aux | grep gunicorn | grep -v grep

echo "=== SUPERVISOR STATUS ==="
supervisorctl status 2>/dev/null
'
```

### 5. Revisar configuración actual de Gunicorn

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
cat /home/erpnext/frappe-bench/config/supervisor.conf 2>/dev/null | grep -A5 "gunicorn"
cat /home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json 2>/dev/null
cat /home/erpnext/frappe-bench/sites/common_site_config.json 2>/dev/null
'
```

### 6. Revisar slow queries (si ya hay datos)

Esperar 5 minutos con el sistema en uso, luego:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
# Ver slow queries capturadas
tail -100 /var/log/mysql/slow-queries.log 2>/dev/null

# Resumen con mysqldumpslow (si disponible)
mysqldumpslow -s t -t 10 /var/log/mysql/slow-queries.log 2>/dev/null
'
```

---

## Archivo de salida

**Crear al terminar (aunque sea parcial):**
```
c:\dev\cdtalleres\performance-profiling-results.md
```

### Estructura obligatoria

```markdown
# Profiling de Performance CDTalleres — YYYY-MM-DD HH:MM

## Estado de tabSeries
- Total de series: [número]
- Series con mayor contador (top 10): [tabla]
- DocTypes con naming series: [lista]

## Estado de InnoDB
- innodb_buffer_pool_size actual: [valor]
- Innodb_row_lock_waits: [valor]
- Innodb_row_lock_time_avg: [valor]
- Threads_connected: [valor]
- Threads_running: [valor]

## Configuración Gunicorn
- Workers actuales: [número]
- CPU cores disponibles: [número]
- Workers recomendados: [(2 * cores) + 1]

## Errores encontrados en logs
[Lista de errores relevantes con contexto]

## Slow queries capturadas
[Si hay datos — queries más lentas]

## Diagnóstico
[Análisis del agente: ¿confirma contención en tabSeries? ¿otros cuellos de botella?]

## Recomendaciones priorizadas
1. [más urgente]
2. [...]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
