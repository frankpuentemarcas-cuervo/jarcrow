---
fecha: 2026-04-25
agente_id: "018"
descripcion: implementar-sequence-mariadb-naming-legible-sin-lock
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\sequence-naming-results.md"
dependencia: "016 (hash aplicado, contadores conocidos: OT=43200, NOT=95737)"
---

# Implementar Naming con MariaDB SEQUENCE — IDs legibles sin tabSeries lock

## Contexto para el agente

Proyecto CDTalleres. El prompt 016 migró `Orden de Trabajo 2` e `Historial Notificaciones` a `autoname=hash`. Los IDs resultantes (`55d5ed17be`) son ilegibles para el usuario. El prompt 016 también confirmó que `Purchase Order` y `Purchase Invoice` siguen con `naming_series` y mantienen `row_lock_time_avg` en 14,226ms.

**Objetivo**: Reemplazar `hash` y `naming_series` con una solución basada en **SEQUENCE de MariaDB**:
- Atómica: sin `SELECT ... FOR UPDATE`, sin lock de fila en `tabSeries`
- Legible: `OT-043201`, `HIST-095738`, `OC-026873`, `FC-025921`
- Secuencial: continúa desde el número actual, sin brechas

### Rutas y credenciales

```
Bench:  /home/erpnext/frappe-bench
Site:   CDTALLERES
DB:     _0646d69b639ad0ff
```

| Rol | IP | Credenciales |
|---|---|---|
| Frontend/App (bench + código) | 209.38.75.235 | root / .Overskull2026.m |
| DB (MariaDB) | 165.232.130.222 | root / .Overskull2026.m |

### DocTypes a intervenir

| DocType | Tipo | Prefijo objetivo | Contador inicial | Método |
|---|---|---|---|---|
| Orden de Trabajo 2 | Custom (en erpnext/HR) | `OT-` | 43200 | Controller `before_insert` |
| Historial Notificaciones | Custom (app notification) | `HIST-` | 95737 | Controller `before_insert` |
| Purchase Order | Core ERPNext | `OC-` | valor actual en tabSeries | Server Script DB |
| Purchase Invoice | Core ERPNext | `FC-` | valor actual en tabSeries | Server Script DB |

**IMPORTANTE sobre Purchase Order y Purchase Invoice**: Son DocTypes core de ERPNext. NO modificar su archivo JSON ni su controller Python. El override se hace vía **Server Script** (`before_insert`) desde la UI de Frappe, que tiene precedencia sobre el naming automático cuando se establece `self.name` antes del insert.

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear o actualizar `c:\dev\cdtalleres\sequence-naming-results.md` tras cada tarea
2. Documentar resultado (✅/❌), output exacto, error completo si falló
3. Nunca terminar sin el archivo de salida. Aunque sea parcial.
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

### 1. Obtener contadores actuales de tabSeries para PO y PI

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT name, current
FROM tabSeries
WHERE name LIKE \"PUR-%\" OR name LIKE \"ACC-PINV%\" OR name LIKE \"PO-%\"
   OR name LIKE \"PINV%\" OR name LIKE \"ACC-PI%\"
ORDER BY current DESC
LIMIT 20;
" 2>/dev/null
'
```

Documentar el nombre exacto de la serie y su contador para PO y PI — se usan en T2.

Notificar:
```bash
tg_notify "✅ *CDT 018 T1* — Contadores actuales de PO y PI registrados"
```

---

### 2. Crear las 4 SEQUENCES en MariaDB

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff

# Reemplazar XXXX con el valor actual de PO y PI obtenido en T1
PO_INICIO=XXXX
PI_INICIO=XXXX

mysql -u root -p".Overskull2026.m" "$DB" -e "
-- Secuencia para Orden de Trabajo 2 (arranca desde 43200 — valor post-016)
CREATE SEQUENCE IF NOT EXISTS seq_orden_trabajo
  START WITH 43201
  INCREMENT BY 1
  MINVALUE 1
  NOCYCLE;

-- Secuencia para Historial Notificaciones (arranca desde 95737)
CREATE SEQUENCE IF NOT EXISTS seq_historial_notificaciones
  START WITH 95738
  INCREMENT BY 1
  MINVALUE 1
  NOCYCLE;

-- Secuencia para Purchase Order
CREATE SEQUENCE IF NOT EXISTS seq_purchase_order
  START WITH ${PO_INICIO}
  INCREMENT BY 1
  MINVALUE 1
  NOCYCLE;

-- Secuencia para Purchase Invoice
CREATE SEQUENCE IF NOT EXISTS seq_purchase_invoice
  START WITH ${PI_INICIO}
  INCREMENT BY 1
  MINVALUE 1
  NOCYCLE;

-- Verificar creación
SHOW CREATE SEQUENCE seq_orden_trabajo;
SHOW CREATE SEQUENCE seq_historial_notificaciones;
SHOW CREATE SEQUENCE seq_purchase_order;
SHOW CREATE SEQUENCE seq_purchase_invoice;
" 2>/dev/null
'
```

**Verificar que las 4 secuencias existen**:
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT table_name AS secuencia
FROM information_schema.TABLES
WHERE table_schema = \"$DB\"
  AND table_name LIKE \"seq_%\"
  AND table_type = \"SEQUENCE\";
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 018 T2* — 4 SEQUENCES creadas en MariaDB"
```

---

### 3. Modificar controller de Orden de Trabajo 2

Primero localizar el archivo controller:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
find /home/erpnext/frappe-bench/apps/erpnext -type f -name "*.py" | \
  xargs grep -l "Orden de Trabajo 2\|orden_de_trabajo_2\|OrdenDeTrabajo" 2>/dev/null | \
  grep -v "__pycache__" | grep -v ".pyc"
'
```

Una vez localizado el archivo controller (probablemente `orden_de_trabajo_2.py`), agregar el hook `before_insert`:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
# REEMPLAZAR con la ruta real encontrada arriba
CONTROLLER=/home/erpnext/frappe-bench/apps/erpnext/erpnext/[RUTA]/orden_de_trabajo_2.py

echo "=== Contenido actual del controller ==="
cat "$CONTROLLER"
'
```

Editar el controller para agregar `before_insert`. El agente debe agregar el método si no existe, o agregarlo al inicio de la clase si ya existe:

```python
# Agregar dentro de la clase del DocType (o crear la clase si no existe):

import frappe
from frappe.model.document import Document

class OrdenDeTrabajo2(Document):
    def before_insert(self):
        # Solo generar nombre si no viene asignado ya
        if not self.name or self.name.startswith("new-"):
            next_val = frappe.db.sql(
                "SELECT NEXTVAL(seq_orden_trabajo) FROM DUAL"
            )[0][0]
            self.name = "OT-{:06d}".format(int(next_val))
```

Notificar:
```bash
tg_notify "✅ *CDT 018 T3* — Controller Orden de Trabajo 2 actualizado con SEQUENCE"
```

---

### 4. Modificar controller de Historial Notificaciones

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
find /home/erpnext/frappe-bench/apps/notification -type f -name "*.py" | \
  grep -i "historial" | grep -v "__pycache__"
'
```

Editar el controller encontrado:

```python
import frappe
from frappe.model.document import Document

class HistorialNotificaciones(Document):
    def before_insert(self):
        if not self.name or self.name.startswith("new-"):
            next_val = frappe.db.sql(
                "SELECT NEXTVAL(seq_historial_notificaciones) FROM DUAL"
            )[0][0]
            self.name = "HIST-{:06d}".format(int(next_val))
```

Notificar:
```bash
tg_notify "✅ *CDT 018 T4* — Controller Historial Notificaciones actualizado con SEQUENCE"
```

---

### 5. Cambiar autoname de OT2 e Historial de "hash" a "field:name"

El `autoname = "hash"` del prompt 016 ya no aplica — ahora el nombre lo genera el controller. Cambiar a `field:name` para que Frappe no intente generar un nombre propio y use el que setea `before_insert`.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

echo "=== Cambiar autoname: Orden de Trabajo 2 ==="
sudo -u erpnext bench --site $SITE execute frappe.db.set_value \
  --args '["DocType", "Orden de Trabajo 2", "autoname", "field:name"]' 2>&1

echo "=== Cambiar autoname: Historial Notificaciones ==="
sudo -u erpnext bench --site $SITE execute frappe.db.set_value \
  --args '["DocType", "Historial Notificaciones", "autoname", "field:name"]' 2>&1

echo "=== Limpiar caché ==="
sudo -u erpnext bench --site $SITE clear-cache 2>&1 | tail -3
'
```

Notificar:
```bash
tg_notify "✅ *CDT 018 T5* — autoname cambiado a field:name en OT2 e Historial"
```

---

### 6. Crear Server Scripts para Purchase Order y Purchase Invoice

Para DocTypes core de ERPNext, usar Server Script desde la UI de Frappe (no tocar código fuente). El Server Script en evento `before_insert` tiene precedencia sobre el naming automático.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

echo "=== Crear Server Script: Purchase Order → SEQUENCE ==="
sudo -u erpnext bench --site $SITE execute frappe.client.insert --args '"'"'{
  "doctype": "Server Script",
  "name": "CDT-PO-Sequence-Naming",
  "script_type": "DocType Event",
  "reference_doctype": "Purchase Order",
  "doctype_event": "Before Insert",
  "enabled": 1,
  "script": "next_val = frappe.db.sql(\"SELECT NEXTVAL(seq_purchase_order) FROM DUAL\")[0][0]\ndoc.name = \"OC-{:06d}\".format(int(next_val))"
}'"'"' 2>&1 | tail -5

echo "=== Crear Server Script: Purchase Invoice → SEQUENCE ==="
sudo -u erpnext bench --site $SITE execute frappe.client.insert --args '"'"'{
  "doctype": "Server Script",
  "name": "CDT-PI-Sequence-Naming",
  "script_type": "DocType Event",
  "reference_doctype": "Purchase Invoice",
  "doctype_event": "Before Insert",
  "enabled": 1,
  "script": "next_val = frappe.db.sql(\"SELECT NEXTVAL(seq_purchase_invoice) FROM DUAL\")[0][0]\ndoc.name = \"FC-{:06d}\".format(int(next_val))"
}'"'"' 2>&1 | tail -5

sudo -u erpnext bench --site $SITE clear-cache 2>&1 | tail -3
'
```

Notificar:
```bash
tg_notify "✅ *CDT 018 T6* — Server Scripts creados para PO y PI con SEQUENCE"
```

---

### 7. Verificar los 4 DocTypes — crear documentos de prueba

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

echo "=== TEST: Orden de Trabajo 2 ==="
sudo -u erpnext bench --site $SITE execute frappe.client.insert \
  --args '{"doctype": "Orden de Trabajo 2"}' 2>&1 | grep '"name"' | head -2
# Esperado: "OT-043201"

echo ""
echo "=== TEST: Historial Notificaciones ==="
sudo -u erpnext bench --site $SITE execute frappe.client.insert \
  --args '{"doctype": "Historial Notificaciones"}' 2>&1 | grep '"name"' | head -2
# Esperado: "HIST-095738"

echo ""
echo "=== TEST: Purchase Order ==="
sudo -u erpnext bench --site $SITE execute frappe.client.insert --args '"'"'{
  "doctype": "Purchase Order",
  "supplier": "PROVEEDOR-TEST",
  "transaction_date": "2026-04-25",
  "schedule_date": "2026-05-25",
  "items": [{"item_code": "STRESS-ITEM-001", "qty": 1, "rate": 100, "schedule_date": "2026-05-25"}]
}'"'"' 2>&1 | grep '"name"' | head -2
# Esperado: "OC-XXXXXX"

echo ""
echo "=== TEST: Purchase Invoice ==="
sudo -u erpnext bench --site $SITE execute frappe.client.insert --args '"'"'{
  "doctype": "Purchase Invoice",
  "supplier": "PROVEEDOR-TEST",
  "posting_date": "2026-04-25",
  "items": [{"item_code": "STRESS-ITEM-001", "qty": 1, "rate": 100}]
}'"'"' 2>&1 | grep '"name"' | head -2
# Esperado: "FC-XXXXXX"
'
```

Notificar:
```bash
tg_notify "✅ *CDT 018 T7* — 4 DocTypes verificados con naming tipo OT-043201"
```

---

### 8. Verificar que tabSeries NO incrementa para ninguno de los 4

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff

echo "=== Contadores tabSeries ANTES de crear docs ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT name, current FROM tabSeries
WHERE name IN (\"Orden-Trabajo-\", \"NOT\")
   OR name LIKE \"PUR-%\" OR name LIKE \"ACC-PINV%\" OR name LIKE \"PO-%\"
ORDER BY current DESC LIMIT 10;
" 2>/dev/null
'

# Crear 3 docs de cada tipo
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

for dt in "Orden de Trabajo 2" "Historial Notificaciones"; do
  for i in 1 2 3; do
    sudo -u erpnext bench --site $SITE execute frappe.client.insert \
      --args "{\"doctype\": \"$dt\"}" 2>&1 | grep '"name"' | head -1
  done
done
'

# Contadores DESPUÉS — deben ser iguales
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT name, current FROM tabSeries
WHERE name IN (\"Orden-Trabajo-\", \"NOT\")
   OR name LIKE \"PUR-%\" OR name LIKE \"ACC-PINV%\" OR name LIKE \"PO-%\"
ORDER BY current DESC LIMIT 10;
" 2>/dev/null
'
```

**Esperado**: todos los contadores en tabSeries sin cambio.

Notificar:
```bash
tg_notify "✅ *CDT 018 T8* — tabSeries congelado. SEQUENCES funcionando correctamente."
```

---

### 9. Mini stress test final — 50 usuarios, 3 minutos

```bash
# Reset contadores InnoDB para medición limpia
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "FLUSH STATUS;" 2>/dev/null
'

sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
cd /opt/cdtalleres-stress
mkdir -p /opt/cdtalleres-stress/results_sequence

locust \
  --locustfile locustfile.py \
  --host https://cdtalleres-copia.shalom.com.pe \
  --users 50 \
  --spawn-rate 10 \
  --run-time 3m \
  --headless \
  --csv /opt/cdtalleres-stress/results_sequence/stress_sequence \
  2>&1 | tail -40

cat /opt/cdtalleres-stress/results_sequence/stress_sequence_stats.csv 2>/dev/null
'

# Métricas DB post-test
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "
  SHOW GLOBAL STATUS LIKE \"Innodb_row_lock_waits\";
  SHOW GLOBAL STATUS LIKE \"Innodb_row_lock_time_avg\";
  SHOW GLOBAL STATUS LIKE \"Threads_connected\";
" 2>/dev/null
'
```

**Tabla comparativa objetivo**:

| Métrica | Baseline (sin fix) | Post-016 (hash) | Post-018 (SEQUENCE) |
|---|---|---|---|
| `row_lock_time_avg` | 14,740ms | 14,226ms | < 500ms |
| Fail rate OT2 | 96.3% | 6.6% | < 2% |
| Fail rate PO/PI | 95.5% | 0% (50u) | < 2% |
| Latencia p50 OT2 | 120s | 47s | < 3s |

Notificar:
```bash
tg_notify "🏁 *CDT 018 TERMINÓ* — SEQUENCE naming implementado en 4 DocTypes\nVer: c:\\dev\\cdtalleres\\sequence-naming-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\sequence-naming-results.md
```

### Estructura obligatoria

```markdown
# Sequence Naming CDTalleres — YYYY-MM-DD HH:MM

## SEQUENCES creadas en MariaDB

| Secuencia | Valor inicial | DocType | Estado |
|---|---|---|---|
| seq_orden_trabajo | 43201 | Orden de Trabajo 2 | ✅/❌ |
| seq_historial_notificaciones | 95738 | Historial Notificaciones | ✅/❌ |
| seq_purchase_order | XXXXX | Purchase Order | ✅/❌ |
| seq_purchase_invoice | XXXXX | Purchase Invoice | ✅/❌ |

## DocTypes modificados

| DocType | Método | Prefijo | Ejemplo ID | Controller editado |
|---|---|---|---|---|
| Orden de Trabajo 2 | before_insert + SEQUENCE | OT- | OT-043201 | apps/erpnext/.../orden_de_trabajo_2.py |
| Historial Notificaciones | before_insert + SEQUENCE | HIST- | HIST-095738 | apps/notification/.../historial_notificaciones.py |
| Purchase Order | Server Script before_insert | OC- | OC-026873 | CDT-PO-Sequence-Naming |
| Purchase Invoice | Server Script before_insert | FC- | FC-025921 | CDT-PI-Sequence-Naming |

## Verificación tabSeries — congelado

| Serie | Contador antes | Contador después | Resultado |
|---|---|---|---|
| Orden-Trabajo- | 43200 | 43200 | ✅ congelado |
| NOT | 95737 | 95737 | ✅ congelado |
| [serie PO] | XXXX | XXXX | ✅ congelado |
| [serie PI] | XXXX | XXXX | ✅ congelado |

## Resultado stress test (50u, 3min) — comparación

| Métrica | Baseline | Post-016 hash | Post-018 SEQUENCE |
|---|---|---|---|
| row_lock_time_avg | 14,740ms | 14,226ms | [valor]ms |
| Fail rate OT2 | 96.3% | 6.6% | [valor]% |
| Fail rate PO | 95.5% | 0% | [valor]% |
| Latencia p50 | 120s | 47s | [valor]s |

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
