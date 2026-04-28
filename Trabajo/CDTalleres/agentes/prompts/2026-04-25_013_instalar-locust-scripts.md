---
fecha: 2026-04-25
agente_id: "013"
descripcion: instalar-locust-crear-script-carga-usuario-api
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: completado
falla: "Solicitud de Pagos devuelve 417 (campo extra requerido) — parcial"
archivo_salida: "c:\\dev\\cdtalleres\\locust-setup-results.md"
dependencia: "012 (Prometheus+Grafana instalados)"
---

# Instalar Locust + Script de Carga — CDTalleres Stress Test

## Contexto para el agente

Proyecto CDTalleres stress test diagnóstico. Prometheus+Grafana ya están listos (prompt 012). Ahora hay que:
1. Instalar Locust en Backend (164.92.94.47)
2. Crear el script de carga que ataca los 4 DocTypes target via API REST de Frappe
3. Crear un usuario API en ERPNext con los permisos necesarios
4. Instalar locust-exporter para que Prometheus capture métricas de Locust
5. Verificar que el script puede autenticarse y crear documentos

### DocTypes a estresar

| DocType | Peso | Naming Series esperada |
|---|---|---|
| Purchase Order | 30% | PO- o similar |
| Purchase Invoice | 25% | ACC-PINV- o similar |
| Orden de Trabajo 2 | 25% | Orden-Trabajo- (42k+ en tabSeries) |
| Solicitud de Pagos | 20% | custom |

### Credenciales

| Sistema | Dato |
|---|---|
| SSH Backend | root / .Overskull2026.m |
| ERPNext URL | https://cdtalleres-copia.shalom.com.pe |
| SSH Frontend (para crear usuario API) | root / .Overskull2026.m en 209.38.75.235 |

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

### 1. Instalar Locust en Backend (164.92.94.47)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
# Verificar Python3 + pip
python3 --version
pip3 --version 2>/dev/null || (apt-get install -y python3-pip -qq && echo "pip instalado")

# Instalar Locust y exporter
pip3 install locust locust-exporter 2>&1 | tail -5
locust --version

mkdir -p /opt/cdtalleres-stress
echo "Locust instalado en Backend"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T1* — Locust instalado en Backend"
```

---

### 2. Crear usuario API en ERPNext (en servidor Frontend)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench

echo "=== CREAR USUARIO STRESS TEST ==="
cd $BENCH
sudo -u erpnext bench --site CDTALLERES execute frappe.client.insert --args '"'"'{
  "doctype": "User",
  "email": "stress-test@cdtalleres.local",
  "first_name": "StressTest",
  "send_welcome_email": 0,
  "new_password": "StressTest2026!",
  "roles": [{"role": "System Manager"}]
}'"'"' 2>&1 || echo "usuario puede ya existir, continuando"

echo "=== GENERAR API KEY Y SECRET ==="
sudo -u erpnext bench --site CDTALLERES execute frappe.core.doctype.user.user.generate_keys --args '"'"'["stress-test@cdtalleres.local"]'"'"' 2>&1

echo "=== OBTENER CLAVES GENERADAS ==="
sudo -u erpnext bench --site CDTALLERES execute frappe.db.get_value --args '"'"'["User", "stress-test@cdtalleres.local", ["api_key", "api_secret"]]'"'"' 2>&1
'
```

**IMPORTANTE**: Documentar el `api_key` y `api_secret` que devuelva este comando — se usan en el script Locust.

Notificar:
```bash
tg_notify "✅ *CDT T2* — Usuario API stress-test creado en ERPNext\nDocumentar api_key y api_secret en archivo de salida"
```

---

### 3. Verificar campos requeridos de los DocTypes target

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench

echo "=== CAMPOS REQUERIDOS — Purchase Order ==="
sudo -u erpnext bench --site CDTALLERES execute frappe.get_meta --args '"'"'["Purchase Order"]'"'"' 2>&1 | python3 -c "
import json, sys
try:
    meta = json.load(sys.stdin)
    required = [f['"'"'fieldname'"'"'] for f in meta.get('"'"'fields'"'"',[]) if f.get('"'"'reqd'"'"')]
    print('"'"'Required fields:'"'"', required[:15])
except:
    print(sys.stdin.read()[:500])
" 2>/dev/null || echo "revisar manualmente"

echo "=== CAMPOS REQUERIDOS — Purchase Invoice ==="
sudo -u erpnext bench --site CDTALLERES execute frappe.get_meta --args '"'"'["Purchase Invoice"]'"'"' 2>&1 | python3 -c "
import json, sys
try:
    meta = json.load(sys.stdin)
    required = [f['"'"'fieldname'"'"'] for f in meta.get('"'"'fields'"'"',[]) if f.get('"'"'reqd'"'"')]
    print('"'"'Required fields:'"'"', required[:15])
except:
    print(sys.stdin.read()[:300])
" 2>/dev/null || echo "revisar manualmente"

echo "=== VERIFICAR NOMBRE EXACTO DocType Orden de Trabajo 2 ==="
sudo -u erpnext bench --site CDTALLERES execute frappe.db.get_value --args '"'"'["DocType", {"name": ["like", "%Orden%"]}, "name"]'"'"' 2>&1

echo "=== VERIFICAR NOMBRE EXACTO DocType Solicitud de Pagos ==="
sudo -u erpnext bench --site CDTALLERES execute frappe.db.get_value --args '"'"'["DocType", {"name": ["like", "%Solicitud%Pago%"]}, "name"]'"'"' 2>&1
'
```

**IMPORTANTE**: Documentar los nombres exactos de los DocTypes y campos requeridos — necesarios para el script Locust.

---

### 4. Crear script Locust con los datos reales

Una vez obtenidos api_key, api_secret, nombres exactos de DocTypes y campos requeridos, crear el script en el Backend:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
# REEMPLAZAR estos valores con los obtenidos en tareas 2 y 3:
API_KEY="REEMPLAZAR_CON_KEY_REAL"
API_SECRET="REEMPLAZAR_CON_SECRET_REAL"
DOCTYPE_OT="Orden de Trabajo 2"        # ajustar si nombre exacto es diferente
DOCTYPE_SP="Solicitud de Pagos"         # ajustar si nombre exacto es diferente

cat > /opt/cdtalleres-stress/locustfile.py << PYEOF
import random
import string
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask

API_KEY = "${API_KEY}"
API_SECRET = "${API_SECRET}"

def random_str(n=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))

class FrappeUser(HttpUser):
    wait_time = between(0, 1)
    
    def on_start(self):
        self.headers = {
            "Authorization": f"token {API_KEY}:{API_SECRET}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # Verificar auth
        r = self.client.get("/api/method/frappe.auth.get_logged_user",
                            headers=self.headers, catch_response=True)
        if r.status_code != 200:
            r.failure(f"Auth falló: {r.status_code}")

    @task(3)
    def create_purchase_order(self):
        """30% — Purchase Order crea entrada tabSeries PO-"""
        payload = {
            "doctype": "Purchase Order",
            "supplier": "Test Supplier " + random_str(),
            "transaction_date": "2026-04-25",
            "schedule_date": "2026-05-25",
            "items": [{
                "item_code": "STRESS-ITEM-001",
                "qty": random.randint(1, 10),
                "rate": random.uniform(10, 1000),
                "schedule_date": "2026-05-25"
            }]
        }
        with self.client.post("/api/resource/Purchase Order",
                              json=payload, headers=self.headers,
                              catch_response=True, name="POST /Purchase Order") as r:
            if r.status_code in (200, 201):
                r.success()
            elif r.status_code == 409:
                r.success()  # duplicate naming — esperado bajo carga
            else:
                r.failure(f"HTTP {r.status_code}: {r.text[:200]}")

    @task(25)
    def create_purchase_invoice(self):
        """25% — Purchase Invoice → tabSeries ACC-PINV-"""
        payload = {
            "doctype": "Purchase Invoice",
            "supplier": "Test Supplier " + random_str(),
            "posting_date": "2026-04-25",
            "items": [{
                "item_code": "STRESS-ITEM-001",
                "qty": 1,
                "rate": 100
            }]
        }
        with self.client.post("/api/resource/Purchase Invoice",
                              json=payload, headers=self.headers,
                              catch_response=True, name="POST /Purchase Invoice") as r:
            if r.status_code in (200, 201):
                r.success()
            elif r.status_code == 409:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}: {r.text[:200]}")

    @task(25)
    def create_orden_trabajo(self):
        """25% — Orden de Trabajo 2 → tabSeries Orden-Trabajo- (42k+)"""
        payload = {
            "doctype": "${DOCTYPE_OT}",
        }
        with self.client.post(f"/api/resource/${DOCTYPE_OT}",
                              json=payload, headers=self.headers,
                              catch_response=True, name="POST /Orden de Trabajo 2") as r:
            if r.status_code in (200, 201):
                r.success()
            elif r.status_code == 409:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}: {r.text[:200]}")

    @task(20)
    def create_solicitud_pagos(self):
        """20% — Solicitud de Pagos"""
        payload = {
            "doctype": "${DOCTYPE_SP}",
        }
        with self.client.post(f"/api/resource/${DOCTYPE_SP}",
                              json=payload, headers=self.headers,
                              catch_response=True, name="POST /Solicitud de Pagos") as r:
            if r.status_code in (200, 201):
                r.success()
            elif r.status_code == 409:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}: {r.text[:200]}")

    @task(5)
    def list_purchase_orders(self):
        """GET lista — simular lectura concurrente"""
        with self.client.get("/api/resource/Purchase Order?limit=20",
                             headers=self.headers,
                             catch_response=True, name="GET /Purchase Order list") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")
PYEOF

echo "Script Locust creado en /opt/cdtalleres-stress/locustfile.py"
cat /opt/cdtalleres-stress/locustfile.py | head -30
'
```

Notificar:
```bash
tg_notify "✅ *CDT T4* — Script Locust creado en Backend\n/opt/cdtalleres-stress/locustfile.py"
```

---

### 5. Test de conectividad — un usuario, 5 requests

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
cd /opt/cdtalleres-stress

echo "=== TEST RAPIDO — 1 usuario, 10 requests, 30s ==="
timeout 35 locust \
  --locustfile locustfile.py \
  --host https://cdtalleres-copia.shalom.com.pe \
  --users 1 \
  --spawn-rate 1 \
  --run-time 30s \
  --headless \
  --csv /tmp/locust_test \
  2>&1 | tail -30

echo "=== RESULTADOS TEST ==="
cat /tmp/locust_test_stats.csv 2>/dev/null | head -10
'
```

Notificar según resultado:
```bash
tg_notify "✅ *CDT T5* — Test Locust 1 usuario: OK — listo para stress test real (prompt 014)"
# O si falla:
tg_notify "❌ *CDT T5* — Test Locust falló — revisar api_key/campos DocType\nVer: c:\\dev\\cdtalleres\\locust-setup-results.md"
```

---

### 6. Verificar que locust-exporter está disponible para Prometheus

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
# locust-exporter se activa cuando Locust corre con --exporter-enabled
# Verificar que el paquete instaló el exporter
pip3 show locust-exporter 2>/dev/null || echo "locust-exporter no encontrado como paquete separado"

# Alternativa: usar --web-port y prometheus scraping nativo de Locust (Locust 2.x lo incluye)
locust --version
echo "Locust 2.x tiene /metrics endpoint nativo en --web-port"
echo "Prometheus scraping target: localhost:8089/metrics (cuando Locust corre)"
'
```

Notificar al terminar:
```bash
tg_notify "🏁 *CDT 013 TERMINÓ* — Locust listo para stress test\nScript: /opt/cdtalleres-stress/locustfile.py\nVer: c:\\dev\\cdtalleres\\locust-setup-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\locust-setup-results.md
```

### Estructura obligatoria

```markdown
# Locust Setup CDTalleres — YYYY-MM-DD HH:MM

## Usuario API ERPNext

- Email: stress-test@cdtalleres.local
- api_key: [VALOR REAL]
- api_secret: [VALOR REAL]
- Creado: ✅/❌

## DocTypes verificados

| DocType | Nombre exacto en sistema | Campos requeridos |
|---|---|---|
| Purchase Order | [nombre] | [lista] |
| Purchase Invoice | [nombre] | [lista] |
| Orden de Trabajo 2 | [nombre real] | [lista] |
| Solicitud de Pagos | [nombre real] | [lista] |

## Locust

- Versión instalada: [X.X.X]
- Script en: /opt/cdtalleres-stress/locustfile.py
- Test 1 usuario (30s): ✅/❌
  - Requests: N
  - Failures: N
  - Avg response: Nms

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
