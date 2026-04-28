---
fecha: 2026-04-27
agente_id: "012"
descripcion: "ocultar-__newname-automatizar-todos-doctypes-sequence"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion
estado: completado
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_012_ocultar-__newname-todos-doctypes.md"
---

# Fix: Ocultar & Automatizar `__newname` en Todos los DocTypes (6 SEQUENCE)

## 🎯 Problema Global

Todos los DocTypes migrados de `tabSeries` → MariaDB `SEQUENCE` muestran campo `__newname` en formulario como **requerido/visible**.

Debe estar:
1. **Oculto** (hidden=1)
2. **No requerido** (reqd=0)
3. **ReadOnly** (read_only=1)
4. **Auto-generado** por `before_insert()` hook

---

## 📊 DocTypes Afectados (6 total)

| DocType | SEQUENCE | Status |
|---|---|---|
| Orden de Trabajo 2 | seq_orden_trabajo | ❌ __newname visible |
| Historial Notificaciones | seq_historial_notificaciones | ❌ __newname visible |
| Purchase Order | seq_purchase_order | ❌ __newname visible |
| Purchase Invoice | seq_purchase_invoice | ❌ __newname visible |
| GL Entry | seq_gl_entry | ❌ __newname visible |
| Stock Ledger Entry | seq_stock_ledger | ❌ __newname visible |
| **BONUS:** Historial Pagos TXT | seq_historial_pagos_txt | ❌ __newname visible |

**Total:** 7 DocTypes necesitan fix

---

## 📋 Tareas

### T1 — Auditar campos `__newname` y `name` en todos DocTypes

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Auditar campos críticos en TODOS los DocTypes ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  parent as doctype,
  fieldname,
  reqd,
  read_only,
  hidden
FROM tabDocField
WHERE parent IN (
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
)
AND fieldname IN ('"'"'__newname'"'"', '"'"'name'"'"')
ORDER BY parent, fieldname;
" 2>&1

'
```

**Esperado:** Salida muestra estado actual (probablemente `hidden=0`, `reqd=0 o 1`)

---

### T2 — Fix campo `name` en todos DocTypes

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Actualizar campo name (hidden + readonly) ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
UPDATE tabDocField 
SET reqd = 0, 
    read_only = 1, 
    hidden = 1
WHERE parent IN (
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
)
AND fieldname = '"'"'name'"'"';
" 2>&1

echo "✅ Campos name actualizados"

'
```

---

### T3 — Fix campo `__newname` en todos DocTypes

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Actualizar campo __newname (hidden + readonly) ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
UPDATE tabDocField 
SET reqd = 0, 
    read_only = 1, 
    hidden = 1,
    depends_on = NULL
WHERE parent IN (
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
)
AND fieldname = '"'"'__newname'"'"';
" 2>&1

echo "✅ Campos __newname actualizados"

'
```

---

### T4 — Verificar cambios

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Verificar campos después de fix ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  parent as doctype,
  fieldname,
  reqd,
  read_only,
  hidden
FROM tabDocField
WHERE parent IN (
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
)
AND fieldname IN ('"'"'__newname'"'"', '"'"'name'"'"')
ORDER BY parent, fieldname;
" 2>&1

'
```

**Esperado:**
- Todos: `reqd=0`, `read_only=1`, `hidden=1`

---

### T5 — Recargar DocTypes en Frappe (7 doctypes)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Recargar DocTypes en Frappe ===" 

bench --site $SITE console << "EOF"
import frappe

doctypes_to_reload = [
    "Orden de Trabajo 2",
    "Historial Notificaciones",
    "Purchase Order",
    "Purchase Invoice",
    "GL Entry",
    "Stock Ledger Entry",
    "Historial Pagos txt"
]

for dt in doctypes_to_reload:
    try:
        frappe.get_meta(dt, force=True)
        print(f"✅ {dt}")
    except Exception as e:
        print(f"❌ {dt}: {str(e)}")

print("\n✅ Todos los DocTypes recargados")
EOF

'
```

---

### T6 — Limpiar cache

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

cd /home/erpnext/frappe-bench

echo "=== Limpiar cache completo ===" 
bench clear-cache 2>&1

echo "=== Flush Redis (si necesario) ===" 
redis-cli FLUSHALL 2>&1 || echo "Redis N/A"

echo "=== Reiniciar servicios ===" 
supervisorctl restart all 2>&1

echo "=== Esperar 5s ===" 
sleep 5

echo "=== Status ===" 
supervisorctl status 2>&1 | head -5

'
```

---

### T7 — Test creación en cada DocType (muestreo)

**Test 1: Purchase Order**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Test Purchase Order ===" 

bench --site $SITE console << "EOF"
import frappe

try:
    doc = frappe.new_doc("Purchase Order")
    doc.supplier = "Supplier Test"  # Requerido
    doc.insert()
    
    print(f"✅ PO creado: {doc.name}")
    print(f"   __newname no debería estar en formulario (hidden)")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
EOF

'
```

**Test 2: GL Entry**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Test GL Entry ===" 

bench --site $SITE console << "EOF"
import frappe

try:
    doc = frappe.new_doc("GL Entry")
    doc.posting_date = frappe.utils.today()
    doc.account = "Test Account"
    doc.insert()
    
    print(f"✅ GLE creado: {doc.name}")
except Exception as e:
    print(f"❌ Error: {str(e)}")
EOF

'
```

---

### T8 — Validación Final Completa

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Estado final de campos en TODOS los DocTypes ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  CONCAT(parent) as doctype,
  GROUP_CONCAT(
    CONCAT(fieldname, '"'"'=hidden:', hidden, '"'"'')
  ) as campos
FROM tabDocField
WHERE parent IN (
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
)
AND fieldname IN ('"'"'__newname'"'"', '"'"'name'"'"')
GROUP BY parent
ORDER BY parent;
" 2>&1

'
```

---

## 📋 Checklist

- [ ] T1: Auditado estado inicial (6 doctypes + Historial)
- [ ] T2: Campo `name` updated (hidden=1, reqd=0, read_only=1) — 7 doctypes
- [ ] T3: Campo `__newname` updated (hidden=1, reqd=0, read_only=1) — 7 doctypes
- [ ] T4: Cambios verificados en BD
- [ ] T5: DocTypes recargados en Frappe API
- [ ] T6: Cache limpiado, servicios reiniciados
- [ ] T7: Tests creación exitosos (PO, GLE, sin errores)
- [ ] T8: Validación final (todos campos hidden=1)

---

## 📊 Reporte Final

Crear: `c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_012_ocultar-__newname-todos-doctypes.md`

Incluir:
1. **Problema Identificado** — Campo `__newname` visible/requerido en 7 doctypes
2. **Doctypes Afectados** — Lista completa con SEQUENCE
3. **Cambios Realizados** — SQL updates para name + __newname
4. **Validación BD** — Estado final de campos (todos hidden=1)
5. **Tests Creación** — Salida PO, GLE, etc. (sin errores)
6. **Status Final** — ✅ Campos ocultos/automáticos en TODOS

---

## 🔐 Acceso SSH

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47
```

**DB:** `_0646d69b639ad0ff` (10.124.0.7 desde backend)

---

## ⚠️ CRÍTICO

**Resultado esperado:** Usuario abre formulario de cualquier DocType (PO, GLE, HP, etc.) → NO ve campo `__newname` ni `name` → genera automáticamente.

Afecta 7 doctypes. Fix aplica a todos de una sola vez.

