---
fecha: 2026-04-27
agente_id: "016"
descripcion: "cambiar-autoname-prompt-hash-eliminar-__newname-inyectado-js"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion-fix
estado: completado
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_016_cambiar-autoname-hash-fix-newname.md"
---

# Fix Definitivo: Cambiar `autoname='Prompt'` → `autoname='hash'`

## 🎯 Causa Raíz REAL (confirmada por diagnóstico 014+015)

`__newname` **NO existe como campo persistido** en ninguna parte:
- ❌ NO en tabDocField
- ❌ NO en tabCustom_Field
- ❌ NO en tabProperty_Setter
- ❌ NO en JSON files
- ❌ NO en frappe meta
- ❌ NO en editor DocType
- ❌ NO en Customize Form

**Es campo VIRTUAL inyectado por JavaScript de Frappe core** cuando `autoname='Prompt'`. Frappe lo agrega al vuelo en `form/layout.js` para capturar ID que usuario debe escribir.

**Solución:** Cambiar `autoname` de `'Prompt'` a `'hash'`. Hash genera ID random temporal. Hook `before_insert()` (ya existente desde agentes 008-013) reasigna `name` desde SEQUENCE MariaDB.

---

## 🔐 ACCESO SSH — TODOS CON LLAVE PÚBLICA

```bash
# Frontend
ssh -i ~/.ssh/cdtalleres_frontend root@209.38.75.235

# Backend
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47

# DB dedicada
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222
```

**DB:** `_0646d69b639ad0ff` (10.124.0.7 desde backend, o local en DB server)
**Pass MariaDB:** `.Overskull2026.m` (root) / `f1Z6583dZNustHQC` (user app)

---

## 📊 DocTypes Afectados (5)

| DocType | Autoname Actual | Autoname Nuevo | SEQUENCE |
|---|---|---|---|
| Purchase Order | Prompt | hash | seq_purchase_order |
| Purchase Invoice | Prompt | hash | seq_purchase_invoice |
| GL Entry | Prompt | hash | seq_gl_entry |
| Stock Ledger Entry | Prompt | hash | seq_stock_ledger |
| Historial Pagos txt | Prompt | hash | seq_historial_pagos_txt |

**NO afectados** (autoname distinto, ya OK):
- Orden de Trabajo 2 (naming_series:)
- Historial Notificaciones (NOT.#######)

---

## 📋 Tareas

### T1 — Backup estado actual

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== BACKUP estado actual autoname ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name as doctype,
  autoname,
  naming_rule,
  allow_rename,
  modified
FROM tabDocType
WHERE name IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
)
ORDER BY name;
" 2>&1

'
```

**Esperado:** 5 doctypes con `autoname='Prompt'`

---

### T2 — Verificar hooks `before_insert()` existen

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

# Site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | grep -v common_site | head -1)

cd /home/erpnext/frappe-bench

echo "=== Server Scripts before_insert (CDT-*-Seq) ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name,
  reference_doctype,
  doctype_event,
  disabled,
  LEFT(script, 200) as script_preview
FROM tabServer_Script
WHERE name LIKE '"'"'CDT-%-Seq'"'"'
ORDER BY name;
" 2>&1

'
```

**Esperado:** 5 server scripts (CDT-PO-Seq, CDT-PI-Seq, CDT-GLE-Seq, CDT-SLE-Seq, CDT-HPT-Seq) tipo `before_insert`, NO disabled.

---

### T3 — Validar que SEQUENCE existe y funciona

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Verificar SEQUENCEs ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SHOW CREATE SEQUENCE seq_purchase_order;
SHOW CREATE SEQUENCE seq_purchase_invoice;
SHOW CREATE SEQUENCE seq_gl_entry;
SHOW CREATE SEQUENCE seq_stock_ledger;
SHOW CREATE SEQUENCE seq_historial_pagos_txt;
" 2>&1 | head -50

echo ""
echo "=== Próximos valores (sin consumir) ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT NEXT VALUE FOR seq_purchase_order as next_po;
SELECT NEXT VALUE FOR seq_purchase_invoice as next_pi;
SELECT NEXT VALUE FOR seq_gl_entry as next_gle;
SELECT NEXT VALUE FOR seq_stock_ledger as next_sle;
SELECT NEXT VALUE FOR seq_historial_pagos_txt as next_hpt;
" 2>&1

'
```

**Esperado:** 5 sequences existen, NEXT VALUE retorna número incremental.

**⚠️ IMPORTANTE:** Después de T3, siguiente T4 debe usar `bench migrate` o ajustar para que ese número consumido no se pierda en testing.

---

### T4 — Cambiar `autoname='Prompt'` → `autoname=''` (vacío) en BD

**Por qué vacío y no 'hash':** Si `autoname=''`, Frappe llama a método `autoname()` Python del controller, que NO existe en estos doctypes core. Pero como NO es 'Prompt', NO inyecta `__newname`. Hook `before_insert` se dispara y asigna `name` desde SEQUENCE.

**Alternativa más segura:** `autoname='hash'` (Frappe genera hash temporal de 10 chars, hook lo reemplaza).

**Aplicar 'hash':**

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Cambiar autoname Prompt → hash ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
UPDATE tabDocType
SET autoname = '"'"'hash'"'"',
    modified = NOW(),
    modified_by = '"'"'Administrator'"'"'
WHERE name IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
)
AND autoname = '"'"'Prompt'"'"';
" 2>&1

echo ""
echo "=== Verificar cambio ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, autoname, modified
FROM tabDocType
WHERE name IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
);
" 2>&1

'
```

**Esperado:** 5 rows updated, todas con `autoname='hash'`.

---

### T5 — Validar hook `before_insert` reasigna `name` correctamente

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

# Site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | grep -v common_site | head -1)

cd /home/erpnext/frappe-bench

echo "=== Ver script completo CDT-PO-Seq ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT script
FROM tabServer_Script
WHERE name = '"'"'CDT-PO-Seq'"'"'
\\G
" 2>&1

'
```

**Esperado:** Ver script Python completo. Debe contener algo como:
```python
import frappe
result = frappe.db.sql("SELECT NEXT VALUE FOR seq_purchase_order")[0][0]
doc.name = f"PO-{result:05d}"
```

Si script asigna `doc.name` correctamente, hash se sobrescribirá con SEQUENCE.

---

### T6 — Limpiar cache + reload

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

cd /home/erpnext/frappe-bench

# Site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | grep -v common_site | head -1)

echo "=== Reload doctypes ===" 
bench --site $SITE console << "PYEOF"
import frappe
for dt in ["Purchase Order", "Purchase Invoice", "GL Entry", "Stock Ledger Entry", "Historial Pagos txt"]:
    try:
        frappe.get_meta(dt, force=True)
        print(f"OK {dt}: autoname = {frappe.get_meta(dt).autoname}")
    except Exception as e:
        print(f"FAIL {dt}: {e}")
PYEOF

echo ""
echo "=== Clear cache ===" 
bench clear-cache 2>&1

echo ""
echo "=== Restart services ===" 
supervisorctl restart all 2>&1 | head -5

sleep 3

echo ""
echo "=== Status ===" 
supervisorctl status 2>&1 | head -10

'
```

---

### T7 — Test creación: Purchase Order

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

# Site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | grep -v common_site | head -1)

cd /home/erpnext/frappe-bench

echo "=== Test crear Purchase Order ===" 
bench --site $SITE console << "PYEOF"
import frappe

# Verificar autoname
meta = frappe.get_meta("Purchase Order")
print(f"autoname: {meta.autoname}")

# Test creación
try:
    doc = frappe.new_doc("Purchase Order")
    doc.supplier = "Test Supplier 016"
    doc.schedule_date = frappe.utils.today()
    doc.transaction_date = frappe.utils.today()
    doc.insert(ignore_permissions=True)
    
    print(f"OK creado: {doc.name}")
    print(f"   formato esperado: PO-XXXXX (no hash)")
    
    # Cleanup
    frappe.delete_doc("Purchase Order", doc.name, force=True)
    print(f"   cleanup: doc eliminado")
    
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
PYEOF

'
```

**Esperado:** `doc.name` = `PO-00XXX` (no hash de 10 chars, no error de `__newname`).

Si `doc.name` es hash → hook `CDT-PO-Seq` no se ejecutó → revisar T5.

---

### T8 — Test API metadata (verificar __newname YA NO inyectado)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

# Site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | grep -v common_site | head -1)

cd /home/erpnext/frappe-bench

echo "=== Verificar meta cliente NO contiene __newname ===" 
bench --site $SITE console << "PYEOF"
import frappe

for dt in ["Purchase Order", "Purchase Invoice", "GL Entry", "Stock Ledger Entry", "Historial Pagos txt"]:
    meta = frappe.get_meta(dt)
    client_dict = meta.as_dict()
    
    has_newname = False
    for f in client_dict.get("fields", []):
        if "newname" in f.get("fieldname", "").lower():
            has_newname = True
            break
    
    status = "STILL HAS __newname" if has_newname else "clean"
    print(f"{dt}: autoname={client_dict.get('"'"'autoname'"'"')} | {status}")
PYEOF

'
```

**Esperado:** 5 doctypes con `autoname=hash`, todos `clean`.

---

### T9 — Salvaguarda: Client Script oculta `__newname` si aparece

Aunque T4 elimina inyección JS, agregamos **defensa adicional**: Client Script que se ejecuta al cargar formulario y oculta `__newname` si Frappe lo renderiza por cualquier razón (caso edge, plugin, tema custom, futura update Frappe).

**Crear 1 Client Script por cada uno de los 5 doctypes** (Frappe Client Script vincula a 1 doctype):

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

# Site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | grep -v common_site | head -1)

cd /home/erpnext/frappe-bench

echo "=== Crear Client Scripts ocultar __newname ===" 

bench --site $SITE console << "PYEOF"
import frappe

doctypes = [
    "Purchase Order",
    "Purchase Invoice",
    "GL Entry",
    "Stock Ledger Entry",
    "Historial Pagos txt"
]

script_template = """
frappe.ui.form.on('"'"'{DOCTYPE}'"'"', {{
    onload: function(frm) {{
        // Ocultar __newname si Frappe lo inyecta
        if (frm.fields_dict && frm.fields_dict['"'"'__newname'"'"']) {{
            frm.fields_dict['"'"'__newname'"'"'].df.hidden = 1;
            frm.fields_dict['"'"'__newname'"'"'].df.reqd = 0;
            frm.fields_dict['"'"'__newname'"'"'].df.read_only = 1;
            frm.refresh_field('"'"'__newname'"'"');
        }}
        // Defensa adicional: ocultar via DOM
        setTimeout(function() {{
            $('"'"'[data-fieldname="__newname"]'"'"').hide();
            $('"'"'.frappe-control[data-fieldname="__newname"]'"'"').hide();
        }}, 100);
    }},
    refresh: function(frm) {{
        if (frm.fields_dict && frm.fields_dict['"'"'__newname'"'"']) {{
            frm.fields_dict['"'"'__newname'"'"'].df.hidden = 1;
            frm.refresh_field('"'"'__newname'"'"');
        }}
        $('"'"'[data-fieldname="__newname"]'"'"').hide();
    }}
}});
"""

for dt in doctypes:
    script_name = f"CDT-Hide-Newname-{dt.replace('"'"' '"'"', '"'"'-'"'"')}"
    
    # Eliminar si ya existe (idempotente)
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name, force=True)
        print(f"removed previo: {script_name}")
    
    # Crear nuevo
    cs = frappe.new_doc("Client Script")
    cs.name = script_name
    cs.dt = dt
    cs.view = "Form"
    cs.enabled = 1
    cs.script = script_template.format(DOCTYPE=dt)
    cs.insert(ignore_permissions=True)
    
    print(f"OK created: {script_name}")

frappe.db.commit()
print("\\nTodos client scripts creados")
PYEOF

'
```

---

### T10 — Verificar Client Scripts creados

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Listar Client Scripts CDT-Hide-Newname-* ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name,
  dt as doctype,
  view,
  enabled,
  modified
FROM tabClient_Script
WHERE name LIKE '"'"'CDT-Hide-Newname-%'"'"'
ORDER BY dt;
" 2>&1

'
```

**Esperado:** 5 client scripts, `enabled=1`, view=`Form`.

---

### T11 — Validación final BD

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222 '

echo "=== Estado final autoname BD dedicada ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name as doctype,
  autoname,
  modified
FROM tabDocType
WHERE name IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"',
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"'
)
ORDER BY name;
" 2>&1

echo ""
echo "=== Client Scripts protección ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, dt, enabled
FROM tabClient_Script
WHERE name LIKE '"'"'CDT-Hide-Newname-%'"'"';
" 2>&1

'
```

**Esperado:**
- 5 doctypes (PO, PI, GLE, SLE, HPT) → `autoname=hash`
- 2 doctypes (OT2, HN) → autoname original (no tocados)
- 5 Client Scripts CDT-Hide-Newname-* enabled

---

## 📋 Checklist

- [ ] T1: Backup estado autoname (5 con 'Prompt')
- [ ] T2: Verificado 5 server scripts CDT-*-Seq existen, no disabled
- [ ] T3: Validadas 5 SEQUENCEs con NEXT VALUE
- [ ] T4: UPDATE tabDocType `autoname='hash'` (5 rows)
- [ ] T5: Confirmado scripts asignan `doc.name` desde SEQUENCE
- [ ] T6: Reload doctypes, clear-cache, restart services
- [ ] T7: Test creación PO genera `name='PO-XXXXX'` (no hash)
- [ ] T8: Meta cliente sin `__newname` (5 doctypes)
- [ ] T9: Client Scripts CDT-Hide-Newname-* creados (5 doctypes)
- [ ] T10: Verificado Client Scripts enabled=1, view=Form
- [ ] T11: Validación final BD dedicada (165.232.130.222)

---

## 📊 Reporte Obligatorio

Crear: `c:\jarcrow\Trabajo\CDTalleres\agentes\respuestas\2026-04-27_016_cambiar-autoname-hash-fix-newname.md`

**Estructura:**

```markdown
# Fix autoname Prompt → hash

## T1: Backup estado actual
[output]
autoname=Prompt en: [lista 5 doctypes]

## T2: Server Scripts before_insert
[output exacto, 5 scripts]
Disabled: [si/no]

## T3: SEQUENCEs validas
[output]
Próximos valores: PO=N, PI=N, GLE=N, SLE=N, HPT=N

## T4: UPDATE autoname=hash
Rows affected: [N]
Verificación: [output]

## T5: Script CDT-PO-Seq (sample)
[script Python completo]
Asigna doc.name correctamente: [si/no]

## T6: Reload + cache + restart
[output supervisorctl status]

## T7: Test creación PO
doc.name resultante: [valor]
Formato esperado: PO-XXXXX
RESULTADO: [si cumple / no cumple]

## T8: Meta cliente sin __newname
[output 5 doctypes]
Todos clean: [si/no]

## T9: Client Scripts CDT-Hide-Newname-* creados
[output creación 5 scripts]

## T10: Verificación Client Scripts
[output BD con 5 entries]
Todos enabled=1: [si/no]

## T11: Validación BD dedicada
[output desde 165.232.130.222]

## CONCLUSIÓN
**autoname cambiado:** [5/5]
**before_insert reasigna nombre:** [si/no]
**__newname inyectado en cliente:** [si/no]
**Status final:** [resuelto/pendiente]

## Rollback (si necesario)
```sql
UPDATE tabDocType SET autoname='Prompt' WHERE name IN (...);
```
```

---

## ⚠️ Si T7 falla (doc.name termina como hash)

Significa que `before_insert` no se está ejecutando. Posibles causas:
1. Server Script `disabled=1` → habilitar
2. Server Script `doctype_event != 'before_insert'` → cambiar
3. Script falla silenciosamente → revisar log

**Diagnóstico rápido:**
```bash
tail -50 /home/erpnext/frappe-bench/logs/frappe.log | grep -i "error\|exception"
```

---

## 🔄 Plan Rollback

Si después de fix usuario reporta otro problema:

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
UPDATE tabDocType
SET autoname = '"'"'Prompt'"'"'
WHERE name IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
);
"
bench --site CDTALLERES clear-cache
supervisorctl restart all
'
```

---

## 🎯 Resultado Esperado

Usuario abre formulario nuevo Purchase Order:
- ✅ NO ve campo `__newname`
- ✅ NO se le pide ID manual
- ✅ Al guardar, ID se genera automáticamente: `PO-00XXX` (desde SEQUENCE)
- ✅ Sin error "campo requerido"
- ✅ Aplica a 5 doctypes (PO, PI, GLE, SLE, HPT)
