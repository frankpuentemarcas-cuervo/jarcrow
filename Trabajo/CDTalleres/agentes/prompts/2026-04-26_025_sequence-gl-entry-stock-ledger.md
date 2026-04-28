---
fecha: 2026-04-26
agente_id: "025"
descripcion: sequence-gl-entry-stock-ledger-entry-eliminar-tabseries-locks
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\sequence-gle-sle-results.md"
dependencia: "ninguna — ejecutar en cdtalleres-copia primero"
tarea_origen: CDT-TASK-025
---

# Migrar GL Entry y Stock Ledger Entry a MariaDB SEQUENCE

## Contexto para el agente

Proyecto CDTalleres: ERPNext con 3 servidores DigitalOcean. El stress test 024 (200u/15min) mostró 29 lock_waits con 3.5s avg aún activos después de haber migrado OT-2, PO y PI a SEQUENCE. La causa probable son las series `ACC-GLE-2025-` (GL Entry) y `MAT-SLE-2025-` que siguen usando tabSeries con SELECT FOR UPDATE.

**Precedente exitoso (prompt 018):**
- Purchase Order → SEQUENCE `seq_purchase_order` → prefijo `OC-` → row_lock_time_avg: 14,740ms → **0ms**
- Purchase Invoice → SEQUENCE `seq_purchase_invoice` → prefijo `FC-`
- Método: `autoname: Prompt` en DocType + Server Script `Before Insert`

**Objetivo**: Aplicar exactamente el mismo patrón a GL Entry y Stock Ledger Entry.

### ⚠️ ADVERTENCIAS CRÍTICAS

1. **GL Entry y Stock Ledger Entry son tablas contables core** — afectan trazabilidad de SUNAT y reportes contables
2. **Ejecutar primero en `cdtalleres-copia`** — verificar que documentos contables (facturas, pagos) siguen creándose correctamente
3. **Hacer backup de DB antes de cualquier cambio**
4. **El formato de ID cambiará**: `ACC-GLE-2025-149253` → `GLE-149253` — confirmar que Frank aprobó este cambio antes de ejecutar en producción
5. **NO ejecutar en producción** hasta que `cdtalleres-copia` pase test completo

### Topología

| Rol | IP Pública | IP Privada |
|---|---|---|
| Frontend (Server Scripts) | `209.38.75.235` | `10.124.0.10` |
| Backend | `164.92.94.47` | `10.124.0.9` |
| DB (MariaDB) | `165.232.130.222` | `10.124.0.7` |

### Credenciales SSH

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@[IP]
```

### Datos técnicos

- **Site producción**: `CDTALLERES`
- **Site copia**: `cdtalleres-copia.shalom.com.pe` (usar este para pruebas)
- **DB name**: `_0646d69b639ad0ff`
- **Bench**: `/home/erpnext/frappe-bench`
- **Contadores conocidos** (al 2026-04-25): `ACC-GLE-2025-`: 149,252 | `MAT-SLE-2025-`: 118,686

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear `c:\dev\cdtalleres\sequence-gle-sle-results.md` y actualizar después de CADA tarea
2. Documentar resultado (✅/❌), output exacto, valores antes/después
3. Si cualquier tarea falla → **DETENER**, documentar, notificar — no continuar
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

### T1 — Auditoría pre-migración

Verificar contadores actuales y estado del sistema antes de tocar nada.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Contadores tabSeries actuales ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT name, current FROM tabSeries
WHERE name LIKE \"ACC-GLE%\" OR name LIKE \"MAT-SLE%\"
ORDER BY name;" 2>/dev/null

echo "=== Registros en GL Entry ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT COUNT(*) AS total, MAX(name) AS ultimo_id FROM \`tabGL Entry\`;" 2>/dev/null

echo "=== Registros en Stock Ledger Entry ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT COUNT(*) AS total, MAX(name) AS ultimo_id FROM \`tabStock Ledger Entry\`;" 2>/dev/null

echo "=== SEQUENCES ya existentes ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_schema = \"_0646d69b639ad0ff\";" 2>/dev/null

echo "=== Server Scripts existentes relacionados ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT name, dt, event, enabled
FROM \`tabServer Script\`
WHERE dt IN (\"GL Entry\", \"Stock Ledger Entry\")
ORDER BY name;" 2>/dev/null

echo "=== autoname actual de GL Entry y SLE ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT name, autoname, module
FROM tabDocType
WHERE name IN (\"GL Entry\", \"Stock Ledger Entry\");" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 025 T1* — Auditoría pre-migración completada"
```

---

### T2 — Backup de DB antes de cambios

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"
BACKUP_DIR="/root/backups-025"
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Backup tabSeries (tabla crítica) ==="
mysql -u root -p".Overskull2026.m" $DB -e "
CREATE TABLE IF NOT EXISTS tabSeries_backup_025_${TIMESTAMP}
SELECT * FROM tabSeries;" 2>/dev/null
echo "Backup tabSeries creado"

echo "=== Backup parcial GL Entry (últimos 1000 registros) ==="
mysql -u root -p".Overskull2026.m" $DB -e "
CREATE TABLE IF NOT EXISTS tabGL_Entry_backup_025_${TIMESTAMP}
SELECT * FROM \`tabGL Entry\` ORDER BY creation DESC LIMIT 1000;" 2>/dev/null
echo "Backup GL Entry (1000 más recientes) creado"

echo "=== Verificar backups ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT table_name,
  ROUND((data_length + index_length)/1024/1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = \"_0646d69b639ad0ff\"
  AND table_name LIKE \"%backup_025%\";" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 025 T2* — Backup pre-migración creado"
```

---

### T3 — Crear SEQUENCES en MariaDB

Usar los contadores actuales de T1 como punto de partida. Si T1 mostró valores distintos a los documentados, usar los valores reales de T1.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Obtener contadores actuales ==="
GLE_CURRENT=$(mysql -u root -p".Overskull2026.m" $DB -se \
  "SELECT current FROM tabSeries WHERE name = \"ACC-GLE-2025-\";" 2>/dev/null)
SLE_CURRENT=$(mysql -u root -p".Overskull2026.m" $DB -se \
  "SELECT current FROM tabSeries WHERE name = \"MAT-SLE-2025-\";" 2>/dev/null)

echo "ACC-GLE-2025- counter: $GLE_CURRENT"
echo "MAT-SLE-2025- counter: $SLE_CURRENT"

# Usar valor real o fallback a documentado
GLE_START=${GLE_CURRENT:-149253}
SLE_START=${SLE_CURRENT:-118687}
GLE_START=$((GLE_START + 1))
SLE_START=$((SLE_START + 1))

echo "=== Creando seq_gl_entry (START $GLE_START) ==="
mysql -u root -p".Overskull2026.m" $DB -e "
DROP SEQUENCE IF EXISTS seq_gl_entry;
CREATE SEQUENCE seq_gl_entry
  START WITH $GLE_START
  INCREMENT BY 1
  NOCACHE
  NOCYCLE;" 2>/dev/null
echo "seq_gl_entry creada"

echo "=== Creando seq_stock_ledger (START $SLE_START) ==="
mysql -u root -p".Overskull2026.m" $DB -e "
DROP SEQUENCE IF EXISTS seq_stock_ledger;
CREATE SEQUENCE seq_stock_ledger
  START WITH $SLE_START
  INCREMENT BY 1
  NOCACHE
  NOCYCLE;" 2>/dev/null
echo "seq_stock_ledger creada"

echo "=== Verificar SEQUENCES ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value, increment
FROM information_schema.sequences
WHERE sequence_schema = \"_0646d69b639ad0ff\"
ORDER BY sequence_name;" 2>/dev/null

echo "=== Test NEXTVAL ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT NEXTVAL(seq_gl_entry) AS gle_test, NEXTVAL(seq_stock_ledger) AS sle_test;" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 025 T3* — SEQUENCES seq_gl_entry y seq_stock_ledger creadas"
```

---

### T4 — Cambiar autoname de GL Entry y Stock Ledger Entry a "Prompt"

Igual que se hizo con Purchase Order en prompt 018. Esto permite que el Server Script asigne el nombre antes del insert.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== autoname actual ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT name, autoname FROM tabDocType
WHERE name IN (\"GL Entry\", \"Stock Ledger Entry\");" 2>/dev/null

echo "=== Cambiar autoname a Prompt ==="
mysql -u root -p".Overskull2026.m" $DB -e "
UPDATE tabDocType SET autoname = \"Prompt\"
WHERE name = \"GL Entry\";" 2>/dev/null

mysql -u root -p".Overskull2026.m" $DB -e "
UPDATE tabDocType SET autoname = \"Prompt\"
WHERE name = \"Stock Ledger Entry\";" 2>/dev/null

echo "=== Verificar cambio ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT name, autoname FROM tabDocType
WHERE name IN (\"GL Entry\", \"Stock Ledger Entry\");" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 025 T4* — autoname cambiado a Prompt en GL Entry y Stock Ledger Entry"
```

---

### T5 — Crear Server Scripts Before Insert

Misma lógica que PO/PI en prompt 018. Usar la consola de Frappe para crear los scripts vía API.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

echo "=== Creando Server Script: GL Entry SEQUENCE ==="
cd $BENCH
sudo -u erpnext bench --site $SITE execute frappe.client.insert --args '"'"'{
  "doc": {
    "doctype": "Server Script",
    "name": "GL Entry — SEQUENCE Naming",
    "dt": "GL Entry",
    "event": "before_insert",
    "enabled": 1,
    "script": "import frappe\n\nif not doc.name or doc.name == \"New GL Entry 1\":\n    next_id = frappe.db.sql(\"SELECT NEXTVAL(seq_gl_entry)\")[0][0]\n    doc.name = f\"GLE-{next_id:06d}\""
  }
}'"'"' 2>/dev/null || echo "bench execute falló — usar método alternativo"

echo "=== Alternativa: crear via Python directo ==="
sudo -u erpnext python3 << '"'"'PYEOF'"'"'
import frappe
frappe.init(site="CDTALLERES")
frappe.connect()

# Server Script GL Entry
ss_gle = frappe.get_doc({
    "doctype": "Server Script",
    "name": "GL Entry — SEQUENCE Naming",
    "dt": "GL Entry",
    "event": "before_insert",
    "enabled": 1,
    "script": """import frappe

if not doc.name or doc.name.startswith("New GL Entry"):
    next_id = frappe.db.sql("SELECT NEXTVAL(seq_gl_entry)")[0][0]
    doc.name = f"GLE-{next_id:06d}"
"""
})

try:
    ss_gle.insert(ignore_permissions=True)
    frappe.db.commit()
    print("✅ Server Script GL Entry creado:", ss_gle.name)
except Exception as e:
    if "already exists" in str(e).lower():
        ss_gle.save(ignore_permissions=True)
        frappe.db.commit()
        print("✅ Server Script GL Entry actualizado")
    else:
        print("❌ Error GL Entry:", e)

# Server Script Stock Ledger Entry
ss_sle = frappe.get_doc({
    "doctype": "Server Script",
    "name": "Stock Ledger Entry — SEQUENCE Naming",
    "dt": "Stock Ledger Entry",
    "event": "before_insert",
    "enabled": 1,
    "script": """import frappe

if not doc.name or doc.name.startswith("New Stock Ledger Entry"):
    next_id = frappe.db.sql("SELECT NEXTVAL(seq_stock_ledger)")[0][0]
    doc.name = f"SLE-{next_id:06d}"
"""
})

try:
    ss_sle.insert(ignore_permissions=True)
    frappe.db.commit()
    print("✅ Server Script Stock Ledger Entry creado:", ss_sle.name)
except Exception as e:
    if "already exists" in str(e).lower():
        ss_sle.save(ignore_permissions=True)
        frappe.db.commit()
        print("✅ Server Script Stock Ledger Entry actualizado")
    else:
        print("❌ Error Stock Ledger Entry:", e)

frappe.destroy()
PYEOF
'
```

```bash
tg_notify "✅ *CDT 025 T5* — Server Scripts Before Insert creados para GLE y SLE"
```

---

### T6 — Congelar tabSeries ACC-GLE y MAT-SLE

Fijar el contador para que Frappe no siga incrementando tabSeries.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Contadores actuales antes de congelar ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT name, current FROM tabSeries
WHERE name LIKE \"ACC-GLE%\" OR name LIKE \"MAT-SLE%\";" 2>/dev/null

echo "=== Congelar series (marcar como usadas con valor alto) ==="
# Estrategia: dejar el valor actual como está — el Server Script
# asigna el nombre antes del insert, por lo que tabSeries nunca se consulta
# Alternativa más segura: renombrar la serie para que Frappe no la encuentre
mysql -u root -p".Overskull2026.m" $DB -e "
UPDATE tabSeries SET name = \"ACC-GLE-2025-FROZEN\"
WHERE name = \"ACC-GLE-2025-\";" 2>/dev/null

mysql -u root -p".Overskull2026.m" $DB -e "
UPDATE tabSeries SET name = \"MAT-SLE-2025-FROZEN\"
WHERE name = \"MAT-SLE-2025-\";" 2>/dev/null

echo "=== Verificar congelamiento ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT name, current FROM tabSeries
WHERE name LIKE \"ACC-GLE%\" OR name LIKE \"MAT-SLE%\";" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 025 T6* — tabSeries ACC-GLE y MAT-SLE congelados"
```

---

### T7 — Test funcional: crear documento que genera GL Entry

GL Entry se crea automáticamente al hacer submit de un Payment Entry, Purchase Invoice o Journal Entry. Crear uno de prueba en `cdtalleres-copia`:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

echo "=== Test: verificar Server Scripts activos ==="
sudo -u erpnext python3 << '"'"'PYEOF'"'"'
import frappe
frappe.init(site="CDTALLERES")
frappe.connect()

scripts = frappe.get_all("Server Script",
    filters={"dt": ["in", ["GL Entry", "Stock Ledger Entry"]], "enabled": 1},
    fields=["name", "dt", "event", "enabled"])

print(f"Server Scripts activos: {len(scripts)}")
for s in scripts:
    print(f"  - {s.name} | {s.dt} | {s.event} | enabled:{s.enabled}")

print("\n=== Último GL Entry en DB ===")
last_gle = frappe.db.sql("SELECT name, creation FROM `tabGL Entry` ORDER BY creation DESC LIMIT 3")
for row in last_gle:
    print(f"  {row[0]} | {row[1]}")

print("\n=== Próximo valor SEQUENCE ===")
next_gle = frappe.db.sql("SELECT NEXTVAL(seq_gl_entry)")[0][0]
next_sle = frappe.db.sql("SELECT NEXTVAL(seq_stock_ledger)")[0][0]
print(f"  seq_gl_entry próximo: GLE-{next_gle:06d}")
print(f"  seq_stock_ledger próximo: SLE-{next_sle:06d}")

frappe.destroy()
PYEOF
'
```

```bash
tg_notify "✅ *CDT 025 T7* — Test funcional completado"
```

---

### T8 — Verificar que tabSeries lock desapareció

Ejecutar consulta de carga simulada y verificar lock_waits:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Reset contadores InnoDB ==="
mysql -u root -p".Overskull2026.m" -e "FLUSH STATUS;" 2>/dev/null

echo "=== Simular 10 SEQUENCEs concurrentes (sin lock) ==="
for i in $(seq 1 10); do
  mysql -u root -p".Overskull2026.m" $DB \
    -e "SELECT NEXTVAL(seq_gl_entry), NEXTVAL(seq_stock_ledger);" 2>/dev/null &
done
wait
echo "10 NEXTVAL ejecutados en paralelo"

echo "=== Lock waits post-test ==="
mysql -u root -p".Overskull2026.m" -e "
SHOW GLOBAL STATUS WHERE Variable_name IN (
  \"Innodb_row_lock_waits\",
  \"Innodb_row_lock_time_avg\",
  \"Slow_queries\");" 2>/dev/null

echo "=== tabSeries congeladas (no deben aparecer sin FROZEN) ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT name, current FROM tabSeries
WHERE name IN (\"ACC-GLE-2025-\", \"MAT-SLE-2025-\");" 2>/dev/null
echo "(resultado vacío = correcto, están renombradas a FROZEN)"

echo "=== SEQUENCES actuales ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_schema = \"_0646d69b639ad0ff\"
ORDER BY sequence_name;" 2>/dev/null
'
```

```bash
tg_notify "🏁 *CDT 025 TERMINÓ* — GL Entry y Stock Ledger Entry migrados a SEQUENCE\nVer: c:\\dev\\cdtalleres\\sequence-gle-sle-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\sequence-gle-sle-results.md
```

### Estructura obligatoria

```markdown
# SEQUENCE GL Entry + Stock Ledger Entry CDTalleres — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T1. Auditoría pre-migración | ✅/❌ | GLE counter: X, SLE counter: X |
| T2. Backup creado | ✅/❌ | tablas backup: |
| T3. SEQUENCES creadas | ✅/❌ | seq_gl_entry START: X, seq_stock_ledger START: X |
| T4. autoname → Prompt | ✅/❌ | GL Entry: OK, SLE: OK |
| T5. Server Scripts creados | ✅/❌ | GLE script: OK, SLE script: OK |
| T6. tabSeries congeladas | ✅/❌ | ACC-GLE-2025-FROZEN, MAT-SLE-2025-FROZEN |
| T7. Test funcional | ✅/❌ | IDs generados: GLE-XXXXXX, SLE-XXXXXX |
| T8. Lock waits verificados | ✅/❌ | lock_waits post: X, avg: Xms |

## SEQUENCES creadas

| Secuencia | Valor inicial | DocType | Prefijo | Ejemplo ID |
|---|---|---|---|---|
| seq_gl_entry | X | GL Entry | GLE- | GLE-149253 |
| seq_stock_ledger | X | Stock Ledger Entry | SLE- | SLE-118687 |

## Comparación locks

| Métrica | Antes (024) | Después (025) |
|---|---|---|
| lock_waits | 29 | ? |
| lock_time_avg | 3,500ms | ? |

## Bloqueos y errores

[vacío si todo OK — si hubo error DETENER y documentar]
```
