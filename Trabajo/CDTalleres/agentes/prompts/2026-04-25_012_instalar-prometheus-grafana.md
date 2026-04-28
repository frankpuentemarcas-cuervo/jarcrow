---
fecha: 2026-04-25
agente_id: "012"
descripcion: instalar-prometheus-grafana-dashboards
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\prometheus-grafana-results.md"
dependencia: "011 (exporters instalados y verificados)"
---

# Instalar Prometheus + Grafana + Dashboards — CDTalleres Stress Test

## Contexto para el agente

Proyecto CDTalleres stress test diagnóstico. Los exporters ya están corriendo (prompt 011). Ahora hay que instalar Prometheus y Grafana en el servidor Backend (164.92.94.47) para capturar y visualizar métricas durante el test de carga.

### Arquitectura objetivo

```
Backend (164.92.94.47)
├── Prometheus :9090  — scraping de 4 exporters cada 5s
└── Grafana :3000     — dashboards en tiempo real
    ├── Locust Load Dashboard
    ├── MariaDB Dashboard
    └── Sistema (3 nodos) Dashboard
```

### Targets que Prometheus debe scraping

| Job | Target | Puerto |
|---|---|---|
| node_frontend | 209.38.75.235 | :9100 |
| node_backend | 164.92.94.47 (localhost) | :9100 |
| node_db | 165.232.130.222 | :9100 |
| mysqld | 165.232.130.222 | :9104 |
| locust | localhost | :9646 |

### Credenciales

| Sistema | Usuario | Password |
|---|---|---|
| SSH Backend | root | .Overskull2026.m |
| Grafana | admin | CDTStress2026 |

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

## Tareas a ejecutar (todas en 164.92.94.47)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47
```

### 1. Instalar Prometheus

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
PROM_VER="2.51.2"

if systemctl is-active prometheus &>/dev/null; then
  echo "Prometheus ya corre"; prometheus --version 2>&1 | head -1; exit 0
fi

cd /tmp
wget -q "https://github.com/prometheus/prometheus/releases/download/v${PROM_VER}/prometheus-${PROM_VER}.linux-amd64.tar.gz" -O prometheus.tar.gz
tar xzf prometheus.tar.gz
cd prometheus-${PROM_VER}.linux-amd64

cp prometheus /usr/local/bin/
cp promtool /usr/local/bin/
mkdir -p /etc/prometheus /var/lib/prometheus
cp -r consoles console_libraries /etc/prometheus/

useradd --no-create-home --shell /bin/false prometheus 2>/dev/null || true
chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus

# Config Prometheus con todos los targets
cat > /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: node_frontend
    static_configs:
      - targets: ["209.38.75.235:9100"]
        labels:
          servidor: frontend

  - job_name: node_backend
    static_configs:
      - targets: ["localhost:9100"]
        labels:
          servidor: backend

  - job_name: node_db
    static_configs:
      - targets: ["165.232.130.222:9100"]
        labels:
          servidor: db

  - job_name: mysqld
    static_configs:
      - targets: ["165.232.130.222:9104"]
        labels:
          servidor: db

  - job_name: locust
    static_configs:
      - targets: ["localhost:9646"]
        labels:
          servidor: backend
EOF

chown prometheus:prometheus /etc/prometheus/prometheus.yml

cat > /etc/systemd/system/prometheus.service << EOF
[Unit]
Description=Prometheus
After=network.target

[Service]
User=prometheus
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus \
  --web.listen-address=0.0.0.0:9090 \
  --storage.tsdb.retention.time=7d
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable prometheus
systemctl start prometheus
sleep 3
systemctl status prometheus | head -8
curl -s http://localhost:9090/-/ready && echo "Prometheus READY"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T1* — Prometheus instalado en Backend :9090"
```

---

### 2. Instalar Grafana

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
if systemctl is-active grafana-server &>/dev/null; then
  echo "Grafana ya corre"; exit 0
fi

# Instalar via apt (repositorio oficial)
apt-get install -y apt-transport-https software-properties-common wget -qq 2>/dev/null
wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key
echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://apt.grafana.com stable main" > /etc/apt/sources.list.d/grafana.list
apt-get update -qq
apt-get install -y grafana 2>/dev/null

# Configurar password admin
sed -i "s/;admin_password = admin/admin_password = CDTStress2026/" /etc/grafana/grafana.ini
sed -i "s/;admin_user = admin/admin_user = admin/" /etc/grafana/grafana.ini

systemctl daemon-reload
systemctl enable grafana-server
systemctl start grafana-server
sleep 5
systemctl status grafana-server | head -8
curl -s http://localhost:3000/api/health | head -5
echo "Grafana en :3000"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T2* — Grafana instalado en Backend :3000 (admin/CDTStress2026)"
```

---

### 3. Configurar Prometheus como datasource en Grafana

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
sleep 3
# Agregar datasource via API
curl -s -X POST http://admin:CDTStress2026@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://localhost:9090",
    "access": "proxy",
    "isDefault": true
  }'"'"' | python3 -c "import json,sys; r=json.load(sys.stdin); print(r.get('"'"'message'"'"', r))"
'
```

---

### 4. Importar dashboards vía API Grafana

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
# Obtener UID del datasource Prometheus
DS_UID=$(curl -s http://admin:CDTStress2026@localhost:3000/api/datasources/name/Prometheus | python3 -c "import json,sys; print(json.load(sys.stdin).get('"'"'uid'"'"', '"'"'prometheus'"'"'))")
echo "Datasource UID: $DS_UID"

# Dashboard 1: Node Exporter Full (ID 1860 — dashboard oficial de la comunidad)
curl -s -X POST http://admin:CDTStress2026@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d "{\"dashboardId\": 1860, \"overwrite\": true, \"inputs\": [{\"name\": \"DS_PROMETHEUS\", \"type\": \"datasource\", \"pluginId\": \"prometheus\", \"value\": \"$DS_UID\"}]}" \
  | python3 -c "import json,sys; r=json.load(sys.stdin); print('"'"'Dashboard Node Exporter:'"'"', r.get('"'"'status'"'"'), r.get('"'"'importedUrl'"'"', '"'"''"'"'))"

# Dashboard 2: MySQL Overview (ID 7362 — dashboard oficial mysqld_exporter)
curl -s -X POST http://admin:CDTStress2026@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d "{\"dashboardId\": 7362, \"overwrite\": true, \"inputs\": [{\"name\": \"DS_PROMETHEUS\", \"type\": \"datasource\", \"pluginId\": \"prometheus\", \"value\": \"$DS_UID\"}]}" \
  | python3 -c "import json,sys; r=json.load(sys.stdin); print('"'"'Dashboard MySQL:'"'"', r.get('"'"'status'"'"'), r.get('"'"'importedUrl'"'"', '"'"''"'"'))"

# Dashboard 3: Locust — dashboard custom para el stress test
cat > /tmp/locust_dashboard.json << '"'"'DASHBOARD_EOF'"'"'
{
  "dashboard": {
    "title": "CDTalleres Locust Stress Test",
    "tags": ["locust", "cdtalleres"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Requests per Second",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
        "targets": [{"expr": "locust_requests_current_rps", "legendFormat": "RPS"}]
      },
      {
        "title": "Error Rate %",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
        "targets": [{"expr": "rate(locust_requests_num_failures_total[1m]) / rate(locust_requests_num_requests_total[1m]) * 100", "legendFormat": "Error %"}]
      },
      {
        "title": "Usuarios activos",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
        "targets": [{"expr": "locust_users", "legendFormat": "Usuarios"}]
      },
      {
        "title": "Latencia p95 por endpoint",
        "type": "graph",
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 4},
        "targets": [{"expr": "locust_requests_current_response_time_percentile_95", "legendFormat": "p95 {{name}}"}]
      }
    ],
    "schemaVersion": 27,
    "version": 1
  },
  "overwrite": true
}
DASHBOARD_EOF

curl -s -X POST http://admin:CDTStress2026@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @/tmp/locust_dashboard.json \
  | python3 -c "import json,sys; r=json.load(sys.stdin); print('"'"'Dashboard Locust:'"'"', r.get('"'"'status'"'"'), r.get('"'"'url'"'"', '"'"''"'"'))"

echo "=== DASHBOARDS DISPONIBLES ==="
curl -s http://admin:CDTStress2026@localhost:3000/api/search | python3 -c "
import json, sys
dashboards = json.load(sys.stdin)
for d in dashboards:
    print(f\"  - {d.get('"'"'title'"'"')} → {d.get('"'"'url'"'"')}\")
"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T3* — Dashboards Grafana configurados\nAcceso: http://164.92.94.47:3000 (admin/CDTStress2026)"
```

---

### 5. Verificar que Prometheus scraping los targets

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
sleep 10
echo "=== TARGETS PROMETHEUS ==="
curl -s http://localhost:9090/api/v1/targets | python3 -c "
import json, sys
data = json.load(sys.stdin)
for t in data['"'"'data'"'"']['"'"'activeTargets'"'"']:
    job = t['"'"'labels'"'"'].get('"'"'job'"'"', '"'"'?'"'"')
    instance = t['"'"'labels'"'"'].get('"'"'instance'"'"', '"'"'?'"'"')
    state = t['"'"'health'"'"']
    print(f'"'"'  {job} | {instance} | {state}'"'"')
"

echo ""
echo "=== SAMPLE MÉTRICAS MARIADB ==="
curl -s "http://localhost:9090/api/v1/query?query=mysql_up" | python3 -c "
import json,sys; r=json.load(sys.stdin); 
results = r.get('"'"'data'"'"',{}).get('"'"'result'"'"',[])
for res in results: print(f\"mysql_up = {res['"'"'value'"'"'][1]}\")
"

echo ""
echo "=== SAMPLE MÉTRICAS NODOS ==="
curl -s "http://localhost:9090/api/v1/query?query=up" | python3 -c "
import json,sys; r=json.load(sys.stdin);
results = r.get('"'"'data'"'"',{}).get('"'"'result'"'"',[])
for res in results:
    job = res['"'"'metric'"'"'].get('"'"'job'"'"','"'"'?'"'"')
    inst = res['"'"'metric'"'"'].get('"'"'instance'"'"','"'"'?'"'"')
    val = res['"'"'value'"'"'][1]
    print(f\"  {job}/{inst} up={val}\")
"
'
```

Notificar al terminar:
```bash
tg_notify "🏁 *CDT 012 TERMINÓ* — Prometheus+Grafana listos\nGrafana: http://164.92.94.47:3000\nPrometheus: http://164.92.94.47:9090\nListo para instalar Locust (prompt 013)\nVer: c:\\dev\\cdtalleres\\prometheus-grafana-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\prometheus-grafana-results.md
```

### Estructura obligatoria

```markdown
# Prometheus + Grafana CDTalleres — YYYY-MM-DD HH:MM

## Instalación

| Componente | Estado | Puerto | URL |
|---|---|---|---|
| Prometheus | ✅/❌ | :9090 | http://164.92.94.47:9090 |
| Grafana | ✅/❌ | :3000 | http://164.92.94.47:3000 |

## Targets Prometheus

| Job | Instance | Estado |
|---|---|---|
| node_frontend | 209.38.75.235:9100 | up/down |
| node_backend | localhost:9100 | up/down |
| node_db | 165.232.130.222:9100 | up/down |
| mysqld | 165.232.130.222:9104 | up/down |
| locust | localhost:9646 | down (se activa en 013) |

## Dashboards importados

| Dashboard | URL |
|---|---|
| Node Exporter Full | /d/... |
| MySQL Overview | /d/... |
| CDTalleres Locust | /d/... |

## mysql_up value: [0/1]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
