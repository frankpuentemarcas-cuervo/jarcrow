---
fecha: 2026-04-25
agente_id: "011"
descripcion: instalar-node-exporter-mysqld-exporter
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\exporters-install-results.md"
dependencia: "010 (backend fix) — puede correr en paralelo"
---

# Instalar Exporters Prometheus — CDTalleres Stress Test

## Contexto para el agente

Proyecto CDTalleres (ERPNext v13.9.2). Preparación del stack de observabilidad para stress test diagnóstico. Hay que instalar exporters de Prometheus en los 3 servidores para capturar métricas en tiempo real durante la prueba de carga.

### Qué instalar en cada servidor

| Servidor | IP | Exporters |
|---|---|---|
| Frontend/App | 209.38.75.235 | node_exporter :9100 |
| Backend | 164.92.94.47 | node_exporter :9100 |
| DB | 165.232.130.222 | node_exporter :9100 + mysqld_exporter :9104 |

### Credenciales SSH

| Servidor | Usuario | Password |
|---|---|---|
| 209.38.75.235 | root | .Overskull2026.m |
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

---

## Tareas a ejecutar

### 1. Instalar node_exporter en FRONTEND (209.38.75.235)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
set -e
NODE_VER="1.7.0"

# Verificar si ya existe
if systemctl is-active node_exporter &>/dev/null; then
  echo "node_exporter ya corre — versión:"; node_exporter --version 2>&1 | head -1
  exit 0
fi

# Descargar e instalar
cd /tmp
wget -q "https://github.com/prometheus/node_exporter/releases/download/v${NODE_VER}/node_exporter-${NODE_VER}.linux-amd64.tar.gz" -O node_exporter.tar.gz
tar xzf node_exporter.tar.gz
cp node_exporter-${NODE_VER}.linux-amd64/node_exporter /usr/local/bin/
chmod +x /usr/local/bin/node_exporter

# Crear usuario
useradd --no-create-home --shell /bin/false node_exporter 2>/dev/null || true

# Systemd service — bind solo a IP privada + localhost
cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter --web.listen-address=0.0.0.0:9100
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter
sleep 2
systemctl status node_exporter | head -8

echo "=== TEST MÉTRICAS ==="
curl -s http://localhost:9100/metrics | head -5
echo "node_exporter OK en :9100"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T1* — node_exporter instalado en Frontend (209.38.75.235):9100"
```

---

### 2. Instalar node_exporter en BACKEND (164.92.94.47)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
set -e
NODE_VER="1.7.0"

if systemctl is-active node_exporter &>/dev/null; then
  echo "node_exporter ya corre"; exit 0
fi

cd /tmp
wget -q "https://github.com/prometheus/node_exporter/releases/download/v${NODE_VER}/node_exporter-${NODE_VER}.linux-amd64.tar.gz" -O node_exporter.tar.gz
tar xzf node_exporter.tar.gz
cp node_exporter-${NODE_VER}.linux-amd64/node_exporter /usr/local/bin/
chmod +x /usr/local/bin/node_exporter
useradd --no-create-home --shell /bin/false node_exporter 2>/dev/null || true

cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter --web.listen-address=0.0.0.0:9100
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter
sleep 2
systemctl status node_exporter | head -8
curl -s http://localhost:9100/metrics | head -3
echo "node_exporter OK en :9100"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T2* — node_exporter instalado en Backend (164.92.94.47):9100"
```

---

### 3. Instalar node_exporter + mysqld_exporter en DB (165.232.130.222)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
NODE_VER="1.7.0"
MYSQL_VER="0.15.1"

echo "=== NODE EXPORTER ==="
if ! systemctl is-active node_exporter &>/dev/null; then
  cd /tmp
  wget -q "https://github.com/prometheus/node_exporter/releases/download/v${NODE_VER}/node_exporter-${NODE_VER}.linux-amd64.tar.gz" -O node_exporter.tar.gz
  tar xzf node_exporter.tar.gz
  cp node_exporter-${NODE_VER}.linux-amd64/node_exporter /usr/local/bin/
  chmod +x /usr/local/bin/node_exporter
  useradd --no-create-home --shell /bin/false node_exporter 2>/dev/null || true

  cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter --web.listen-address=0.0.0.0:9100
Restart=always

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable node_exporter
  systemctl start node_exporter
  echo "node_exporter instalado"
else
  echo "node_exporter ya existe"
fi

echo "=== MYSQLD EXPORTER ==="
if ! systemctl is-active mysqld_exporter &>/dev/null; then
  cd /tmp
  wget -q "https://github.com/prometheus/mysqld_exporter/releases/download/v${MYSQL_VER}/mysqld_exporter-${MYSQL_VER}.linux-amd64.tar.gz" -O mysqld_exporter.tar.gz
  tar xzf mysqld_exporter.tar.gz
  cp mysqld_exporter-${MYSQL_VER}.linux-amd64/mysqld_exporter /usr/local/bin/
  chmod +x /usr/local/bin/mysqld_exporter

  # Crear usuario MySQL para el exporter
  mysql -u root -p".Overskull2026.m" -e "
    CREATE USER IF NOT EXISTS '"'"'exporter'"'"'@'"'"'localhost'"'"' IDENTIFIED BY '"'"'ExporterPass2026'"'"';
    GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO '"'"'exporter'"'"'@'"'"'localhost'"'"';
    FLUSH PRIVILEGES;
  " 2>&1

  # Config file para mysqld_exporter
  cat > /etc/mysqld_exporter.cnf << EOF
[client]
user=exporter
password=ExporterPass2026
host=localhost
EOF
  chmod 600 /etc/mysqld_exporter.cnf

  useradd --no-create-home --shell /bin/false mysqld_exporter 2>/dev/null || true
  chown mysqld_exporter:mysqld_exporter /etc/mysqld_exporter.cnf

  cat > /etc/systemd/system/mysqld_exporter.service << EOF
[Unit]
Description=Prometheus MySQL Exporter
After=network.target mysql.service

[Service]
User=mysqld_exporter
ExecStart=/usr/local/bin/mysqld_exporter --config.my-cnf=/etc/mysqld_exporter.cnf --web.listen-address=0.0.0.0:9104
Restart=always

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable mysqld_exporter
  systemctl start mysqld_exporter
  echo "mysqld_exporter instalado"
else
  echo "mysqld_exporter ya existe"
fi

sleep 3
echo "=== STATUS ==="
systemctl status node_exporter | grep -E "Active|running"
systemctl status mysqld_exporter | grep -E "Active|running"

echo "=== TEST MÉTRICAS ==="
curl -s http://localhost:9100/metrics | grep "node_cpu" | head -3
curl -s http://localhost:9104/metrics | grep "mysql_up" | head -3
'
```

Notificar:
```bash
tg_notify "✅ *CDT T3* — node_exporter + mysqld_exporter instalados en DB (165.232.130.222):9100/:9104"
```

---

### 4. Verificar conectividad desde Backend hacia exporters

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== CONECTIVIDAD EXPORTERS DESDE BACKEND ==="

echo "node_exporter Frontend (209.38.75.235:9100):"
curl -s --max-time 5 http://209.38.75.235:9100/metrics | grep "node_cpu_seconds" | head -2 && echo "✅ OK" || echo "❌ FALLA"

echo "node_exporter DB (165.232.130.222:9100):"
curl -s --max-time 5 http://165.232.130.222:9100/metrics | grep "node_cpu_seconds" | head -2 && echo "✅ OK" || echo "❌ FALLA"

echo "mysqld_exporter DB (165.232.130.222:9104):"
curl -s --max-time 5 http://165.232.130.222:9104/metrics | grep "mysql_up" | head -2 && echo "✅ OK" || echo "❌ FALLA"

echo "node_exporter local (164.92.94.47:9100):"
curl -s --max-time 5 http://localhost:9100/metrics | grep "node_cpu_seconds" | head -2 && echo "✅ OK" || echo "❌ FALLA"
'
```

Notificar al terminar:
```bash
tg_notify "🏁 *CDT 011 TERMINÓ* — Exporters instalados y verificados en 3 servidores\nListo para instalar Prometheus+Grafana (prompt 012)\nVer: c:\\dev\\cdtalleres\\exporters-install-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\exporters-install-results.md
```

### Estructura obligatoria

```markdown
# Exporters Install CDTalleres — YYYY-MM-DD HH:MM

## Estado de instalación

| Servidor | Exporter | Puerto | Estado | Métricas OK |
|---|---|---|---|---|
| Frontend (209.38.75.235) | node_exporter | :9100 | ✅/❌ | ✅/❌ |
| Backend (164.92.94.47) | node_exporter | :9100 | ✅/❌ | ✅/❌ |
| DB (165.232.130.222) | node_exporter | :9100 | ✅/❌ | ✅/❌ |
| DB (165.232.130.222) | mysqld_exporter | :9104 | ✅/❌ | ✅/❌ |

## Conectividad desde Backend

| Target | Accesible |
|---|---|
| 209.38.75.235:9100 | ✅/❌ |
| 165.232.130.222:9100 | ✅/❌ |
| 165.232.130.222:9104 | ✅/❌ |

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
