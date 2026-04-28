---
fecha: 2026-04-25
agente_id: "021"
descripcion: fix-grafana-dashboards-locust-target
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\grafana-fix-results.md"
dependencia: "ninguna — independiente"
tarea_origen: CDT-TASK-021
---

# Fix Grafana — Importar Dashboards y Corregir Locust Target

## Contexto para el agente

Proyecto CDTalleres: Grafana + Prometheus instalados en backend `164.92.94.47`. Todos los exporters (node_exporter, mysqld_exporter) están UP en Prometheus pero los dashboards no muestran data porque el import via ID falló — Grafana 11+ requiere el JSON completo del dashboard, no solo el ID.

**Problema actual:**
- Dashboard 1860 (Node Exporter Full) → importado pero sin data o no importado
- Dashboard 7362 (MySQL Overview) → importado pero sin data o no importado
- Target `locust:9646` → DOWN en Prometheus

**Objetivo**: Dashboards funcionales con métricas en tiempo real.

### Accesos

| Servicio | URL | Credenciales |
|---|---|---|
| Grafana | `http://164.92.94.47:3000` | admin / admin (verificar) |
| Prometheus | `http://164.92.94.47:9090` | — |
| Backend SSH | `164.92.94.47` | root / `.Overskull2026.m` |

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47
```

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear `c:\dev\cdtalleres\grafana-fix-results.md` y actualizar después de CADA tarea
2. Documentar resultado (✅/❌), output exacto, errores completos
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

### T1 — Verificar estado actual de Grafana y password

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Estado Grafana ==="
systemctl status grafana-server --no-pager | head -10

echo "=== Versión Grafana ==="
grafana-server -v 2>/dev/null || grafana --version 2>/dev/null || apt show grafana 2>/dev/null | grep Version

echo "=== Test API con admin/admin ==="
curl -s -u admin:admin http://localhost:3000/api/org | python3 -c "import sys,json; d=json.load(sys.stdin); print(\"Org:\", d.get(\"name\",\"ERROR - credenciales incorrectas\"))" 2>/dev/null || echo "curl fallo"

echo "=== Datasources configurados ==="
curl -s -u admin:admin http://localhost:3000/api/datasources | python3 -c "
import sys, json
try:
    ds = json.load(sys.stdin)
    for d in ds:
        print(f\"  - {d.get('"'"'name'"'"')} | type: {d.get('"'"'type'"'"')} | url: {d.get('"'"'url'"'"')} | id: {d.get('"'"'id'"'"')}\")
except:
    print(sys.stdin.read())
" 2>/dev/null

echo "=== Dashboards actuales ==="
curl -s -u admin:admin "http://localhost:3000/api/search?type=dash-db" | python3 -c "
import sys, json
try:
    ds = json.load(sys.stdin)
    print(f\"Total dashboards: {len(ds)}\")
    for d in ds:
        print(f\"  - {d.get('"'"'title'"'"')} | uid: {d.get('"'"'uid'"'"')}\")
except:
    print(sys.stdin.read())
" 2>/dev/null
'
```

**Si admin/admin no funciona**, probar `admin:cdtalleres` o `admin:Overskull2026`:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
for PASS in admin cdtalleres ".Overskull2026.m" Overskull2026; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -u admin:$PASS http://localhost:3000/api/org)
  echo "admin:$PASS → HTTP $CODE"
done
'
```

```bash
tg_notify "✅ *CDT 021 T1* — Estado Grafana verificado"
```

---

### T2 — Importar Dashboard Node Exporter Full (ID 1860)

Grafana 11+ requiere JSON completo. Descargar desde grafana.com y hacer import via API.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
# Detectar password correcto
GPASS="admin"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -u admin:$GPASS http://localhost:3000/api/org)
[ "$CODE" != "200" ] && GPASS=".Overskull2026.m"

echo "=== Descargando dashboard 1860 ==="
curl -s "https://grafana.com/api/dashboards/1860/revisions/latest/download" -o /tmp/dashboard-1860.json
echo "Tamaño: $(wc -c < /tmp/dashboard-1860.json) bytes"
head -c 200 /tmp/dashboard-1860.json

echo "=== Obteniendo UID del datasource Prometheus ==="
DS_UID=$(curl -s -u admin:$GPASS http://localhost:3000/api/datasources | \
  python3 -c "import sys,json; ds=json.load(sys.stdin); [print(d[\"uid\"]) for d in ds if \"prometheus\" in d.get(\"type\",\"\").lower()]" 2>/dev/null | head -1)
echo "Datasource UID: $DS_UID"

echo "=== Importando dashboard 1860 ==="
python3 << PYEOF
import json, subprocess, sys

with open("/tmp/dashboard-1860.json") as f:
    dash = json.load(f)

# Reemplazar datasource con el UID correcto
ds_uid = "$DS_UID"
dash_str = json.dumps(dash)
# Node exporter usa DS_PROMETHEUS como variable
import re
dash_str = re.sub(r'"datasource":\s*\{[^}]*"type":\s*"prometheus"[^}]*\}',
    f'"datasource": {{"type": "prometheus", "uid": "{ds_uid}"}}', dash_str)

payload = {
    "dashboard": json.loads(dash_str),
    "overwrite": True,
    "folderId": 0,
    "inputs": [{"name": "DS_PROMETHEUS", "type": "datasource", "pluginId": "prometheus", "value": ds_uid}]
}

# Escribir payload
with open("/tmp/import-1860.json", "w") as f:
    json.dump(payload, f)
print("Payload escrito")
PYEOF

curl -s -u admin:$GPASS \
  -H "Content-Type: application/json" \
  -d @/tmp/import-1860.json \
  http://localhost:3000/api/dashboards/import | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(\"Status:\", r.get(\"status\",\"?\"))
print(\"URL:\", r.get(\"importedUrl\", r.get(\"url\", \"?\")))
if \"message\" in r: print(\"Message:\", r[\"message\"])
"
'
```

```bash
tg_notify "✅ *CDT 021 T2* — Dashboard 1860 (Node Exporter Full) importado"
```

---

### T3 — Importar Dashboard MySQL Overview (ID 7362)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
GPASS="admin"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -u admin:$GPASS http://localhost:3000/api/org)
[ "$CODE" != "200" ] && GPASS=".Overskull2026.m"

echo "=== Descargando dashboard 7362 ==="
curl -s "https://grafana.com/api/dashboards/7362/revisions/latest/download" -o /tmp/dashboard-7362.json
echo "Tamaño: $(wc -c < /tmp/dashboard-7362.json) bytes"

echo "=== Obteniendo UID datasource Prometheus ==="
DS_UID=$(curl -s -u admin:$GPASS http://localhost:3000/api/datasources | \
  python3 -c "import sys,json; ds=json.load(sys.stdin); [print(d[\"uid\"]) for d in ds if \"prometheus\" in d.get(\"type\",\"\").lower()]" 2>/dev/null | head -1)
echo "Datasource UID: $DS_UID"

echo "=== Importando dashboard 7362 ==="
python3 << PYEOF
import json

with open("/tmp/dashboard-7362.json") as f:
    dash = json.load(f)

ds_uid = "$DS_UID"

payload = {
    "dashboard": dash,
    "overwrite": True,
    "folderId": 0,
    "inputs": [
        {"name": "DS_PROMETHEUS", "type": "datasource", "pluginId": "prometheus", "value": ds_uid},
        {"name": "DS_MYSQL", "type": "datasource", "pluginId": "prometheus", "value": ds_uid}
    ]
}

with open("/tmp/import-7362.json", "w") as f:
    json.dump(payload, f)
print("Payload escrito")
PYEOF

curl -s -u admin:$GPASS \
  -H "Content-Type: application/json" \
  -d @/tmp/import-7362.json \
  http://localhost:3000/api/dashboards/import | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(\"Status:\", r.get(\"status\",\"?\"))
print(\"URL:\", r.get(\"importedUrl\", r.get(\"url\", \"?\")))
if \"message\" in r: print(\"Message:\", r[\"message\"])
"
'
```

```bash
tg_notify "✅ *CDT 021 T3* — Dashboard 7362 (MySQL Overview) importado"
```

---

### T4 — Verificar métricas en tiempo real

Confirmar que los dashboards muestran datos reales (no "No data").

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
GPASS="admin"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -u admin:$GPASS http://localhost:3000/api/org)
[ "$CODE" != "200" ] && GPASS=".Overskull2026.m"

echo "=== Dashboards importados ==="
curl -s -u admin:$GPASS "http://localhost:3000/api/search?type=dash-db" | python3 -c "
import sys, json
ds = json.load(sys.stdin)
print(f\"Total: {len(ds)} dashboards\")
for d in ds:
    print(f\"  - {d.get('"'"'title'"'"')} | uid: {d.get('"'"'uid'"'"')}\")
"

echo "=== Test métrica node_exporter — CPU ==="
curl -s "http://localhost:9090/api/v1/query?query=node_cpu_seconds_total" | \
  python3 -c "import sys,json; r=json.load(sys.stdin); print(f\"CPU metrics: {len(r.get('"'"'data'"'"',{}).get('"'"'result'"'"',[]))} series\")"

echo "=== Test métrica mysqld — conexiones ==="
curl -s "http://localhost:9090/api/v1/query?query=mysql_global_status_connections" | \
  python3 -c "import sys,json; r=json.load(sys.stdin); print(f\"MySQL connections metric: {len(r.get('"'"'data'"'"',{}).get('"'"'result'"'"',[]))} series\")"

echo "=== Targets Prometheus ==="
curl -s "http://localhost:9090/api/v1/targets" | python3 -c "
import sys, json
r = json.load(sys.stdin)
targets = r.get(\"data\",{}).get(\"activeTargets\",[])
for t in targets:
    print(f\"  {t.get(\"labels\",{}).get(\"job\",\"?\")} | {t.get(\"scrapeUrl\",\"?\")} | {t.get(\"health\",\"?\")}\")"
'
```

```bash
tg_notify "✅ *CDT 021 T4* — Métricas verificadas en Prometheus"
```

---

### T5 — Diagnosticar y corregir target Locust (9646)

Locust puede exponer métricas Prometheus nativamente. Verificar si está corriendo y con qué flags.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== Proceso Locust activo ==="
ps aux | grep locust | grep -v grep || echo "Locust NO está corriendo"

echo "=== Config Prometheus — target locust ==="
grep -r "9646\|locust" /etc/prometheus/ 2>/dev/null || echo "no hay config locust en prometheus"

echo "=== Puerto 9646 ==="
ss -tlnp | grep 9646 || echo "puerto 9646 no escucha"

echo "=== Scripts locust disponibles ==="
ls -la /home/erpnext/locust/ 2>/dev/null || echo "directorio no existe"
'
```

**Decisión basada en diagnóstico:**

- Si Locust no está corriendo → target DOWN es esperado, no es error. Locust solo corre durante tests.
- Si Locust está corriendo pero sin flag `--csv` → el exporter de métricas no está activo.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
# Actualizar config Prometheus: marcar locust como "solo activo durante tests"
# Verificar si hay job locust en prometheus.yml
cat /etc/prometheus/prometheus.yml 2>/dev/null | grep -A5 "locust" || echo "sin job locust"

# Opcion: remover job locust de prometheus (evita alarma DOWN permanente)
# Solo ejecutar si Frank lo aprueba — documentar recomendación
echo ""
echo "RECOMENDACION: el target locust:9646 solo estara UP durante stress tests activos."
echo "Opciones:"
echo "  A) Dejar como está — DOWN en reposo es normal"
echo "  B) Eliminar job locust de prometheus.yml — limpiar alertas falsas"
echo "  C) Configurar locust con --web-port 9646 cuando se ejecute el proximo test"
'
```

```bash
tg_notify "✅ *CDT 021 T5* — Diagnóstico Locust completado"
```

---

### T6 — Resumen final y URLs de dashboards

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
GPASS="admin"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -u admin:$GPASS http://localhost:3000/api/org)
[ "$CODE" != "200" ] && GPASS=".Overskull2026.m"

echo "=== URLs finales de dashboards ==="
curl -s -u admin:$GPASS "http://localhost:3000/api/search?type=dash-db" | python3 -c "
import sys, json
ds = json.load(sys.stdin)
for d in ds:
    print(f\"http://164.92.94.47:3000{d.get('"'"'url'"'"','"'"'?'"'"')}  —  {d.get('"'"'title'"'"')}\")"
'
```

```bash
tg_notify "🏁 *CDT 021 TERMINÓ* — Grafana dashboards configurados\nGrafana: http://164.92.94.47:3000\nVer: c:\\dev\\cdtalleres\\grafana-fix-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\grafana-fix-results.md
```

### Estructura obligatoria

```markdown
# Fix Grafana CDTalleres — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T1. Estado Grafana + credenciales | ✅/❌ | password: , versión: |
| T2. Dashboard 1860 (Node Exporter) | ✅/❌ | URL: |
| T3. Dashboard 7362 (MySQL Overview) | ✅/❌ | URL: |
| T4. Métricas en tiempo real | ✅/❌ | CPU series: , MySQL series: |
| T5. Diagnóstico Locust target | ✅/❌ | estado: DOWN/UP, recomendación: |
| T6. URLs finales | ✅/❌ | — |

## URLs de dashboards

- Node Exporter Full: http://164.92.94.47:3000/d/[uid]/...
- MySQL Overview: http://164.92.94.47:3000/d/[uid]/...

## Estado Locust target

[Explicación de por qué está DOWN y recomendación]

## Bloqueos y errores

[vacío si todo OK]
```
