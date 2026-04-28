---
fecha: 2026-04-27
agente_id: "009"
descripcion: "fix-historial-campo-nombre-readonly-automatico"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_009_fix-historial-campo-nombre-readonly.md"
---

# Fix: Campo "nombre" en Historial Pagos TXT — Debe ser ReadOnly + Automático

## 🎯 Problema

Usuario ve formulario Historial Pagos TXT con campo **"nombre" (ID) pidiendo input manual**.

**Esperado:** Campo auto-generado por SEQUENCE, no visible/editable en forma.

**Causa:** Campo `name` en formulario aparece como editable. Debe ser:
1. **ReadOnly** (usuario no puede editar)
2. **Hidden** (no visible en formulario durante creación)
3. **Auto-poblado** por `before_insert()` hook (SEQUENCE)

---

## 🔍 Diagnóstico

Problema común en Frappe cuando DocType tiene:
- `autoname = 'Prompt'` ✅ (configurado)
- `before_insert()` hook ✅ (código existe)
- **PERO:** Campo `name` en formulario está marcado como editable/requerido ❌

---

## 📋 Tareas

### T1 — Conectar y auditar DocType Historial Pagos TXT

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== DocType: Historial Pagos TXT ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  dt.name,
  dt.autoname,
  dt.allow_rename,
  dt.force_like_filter
FROM tabDocType dt
WHERE dt.name = '"'"'Historial Pagos txt'"'"';
" 2>&1

echo "=== Campo name en DocType ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  f.fieldname,
  f.fieldtype,
  f.label,
  f.reqd,
  f.read_only,
  f.hidden
FROM tabDocField f
WHERE f.parent = '"'"'Historial Pagos txt'"'"'
AND f.fieldname = '"'"'name'"'"';
" 2>&1

echo "=== Otros campos que podrían ser required ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  fieldname,
  label,
  reqd,
  read_only,
  hidden
FROM tabDocField
WHERE parent = '"'"'Historial Pagos txt'"'"'
ORDER BY idx;
" 2>&1

'
```

**Esperado:**
- `autoname = 'Prompt'`
- `allow_rename = 0` (no permitir renombrado)
- Campo `name`: `reqd=0`, `read_only=1`, `hidden=1` (o al menos uno de estos)

---

### T2 — Verificar DocType JSON en file system

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Buscar archivo DocType JSON ===" 
find /home/erpnext/frappe-bench -name "*historial*pagos*" -o -name "*historial_pagos*" 2>/dev/null | head -20

echo "=== Si existe archivo .json ===" 
ls -la /home/erpnext/frappe-bench/apps/*/*/doctype/historial_pagos_txt/ 2>/dev/null

'
```

**Esperado:** Encontrar:
- `historial_pagos_txt.json` (meta)
- `historial_pagos_txt.py` (lógica)

---

### T3 — Corregir DocType (vía Frappe API)

**Opción A: Vía Frappe CLI (recomendado)**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Actualizar DocType: disable allow_rename ===" 

bench --site $SITE console << "EOF"
import frappe

# Cargar DocType
dt = frappe.get_doc("DocType", "Historial Pagos txt")

# Setear propiedades
dt.allow_rename = 0  # No permitir renombrado
dt.quick_entry = 0   # No quick entry
dt.allow_on_submit = 0

# Encontrar campo name y hacerlo read_only
for field in dt.fields:
    if field.fieldname == "name":
        field.reqd = 0        # No requerido
        field.read_only = 1   # Read-only
        field.hidden = 1      # Hidden en forma
        print(f"Campo name: reqd={field.reqd}, read_only={field.read_only}, hidden={field.hidden}")
        break

# Guardar
dt.save()
frappe.db.commit()
print("✅ DocType actualizado")
EOF

'
```

**Opción B: Vía SQL directo (si Frappe API no responde)**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Actualizar DocType via SQL ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
UPDATE tabDocType 
SET allow_rename = 0, quick_entry = 0 
WHERE name = '"'"'Historial Pagos txt'"'"';
" 2>&1

echo "=== Actualizar campo name ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
UPDATE tabDocField 
SET reqd = 0, read_only = 1, hidden = 1
WHERE parent = '"'"'Historial Pagos txt'"'"'
AND fieldname = '"'"'name'"'"';
" 2>&1

echo "=== Verificar cambios ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  dt.allow_rename,
  df.reqd,
  df.read_only,
  df.hidden
FROM tabDocType dt
JOIN tabDocField df ON dt.name = df.parent
WHERE dt.name = '"'"'Historial Pagos txt'"'"'
AND df.fieldname = '"'"'name'"'"';
" 2>&1

'
```

---

### T4 — Actualizar módulo Python (si no tiene before_insert completo)

Verificar que `before_insert()` esté presente y correcto:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Verificar before_insert en Python ===" 
grep -A 10 "def before_insert" /home/erpnext/frappe-bench/apps/erpnext/erpnext/buying/doctype/historial_pagos_txt/historial_pagos_txt.py

echo "=== Si no existe, agregarlo ===" 
# Crear backup
cp /home/erpnext/frappe-bench/apps/erpnext/erpnext/buying/doctype/historial_pagos_txt/historial_pagos_txt.py \
   /tmp/historial_pagos_txt.py.backup.$(date +%s)

'
```

**Si falta `before_insert()`, agregarlo:**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

cat >> /home/erpnext/frappe-bench/apps/erpnext/erpnext/buying/doctype/historial_pagos_txt/historial_pagos_txt.py << '"'"'PYTHON_CODE'"'"'

def before_insert(self):
    """Generate name using SEQUENCE instead of naming_series"""
    if not self.name or self.name.startswith("New "):
        # Get next value from MariaDB SEQUENCE lock-free
        try:
            next_num = frappe.db.sql(
                "SELECT NEXTVAL(seq_historial_pagos_txt) AS next_val",
                as_dict=True
            )[0].get("next_val")
            self.name = f"HP-{next_num:05d}"
        except Exception as e:
            frappe.log_error(f"Error generating HP ID: {str(e)}", "HistorialPagosTXT")
            raise

PYTHON_CODE

'
```

---

### T5 — Limpiar cache Frappe y reiniciar servicios

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

cd /home/erpnext/frappe-bench

echo "=== Limpiar cache ===" 
bench clear-cache 2>&1

echo "=== Reiniciar servicios ===" 
supervisorctl restart all 2>&1

echo "=== Esperar 5s ===" 
sleep 5

echo "=== Status ===" 
supervisorctl status 2>&1

'
```

---

### T6 — Prueba Funcional: Crear nuevo documento

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Test creación documento ===" 

bench --site $SITE console << "EOF"
import frappe

try:
    # Crear documento sin especificar name
    doc = frappe.new_doc("Historial Pagos txt")
    # NO setear doc.name — debe auto-generarse
    doc.solicitud_de_pagos = "SP-TEST"  # O ID real
    doc.insert()
    
    print(f"✅ Documento creado exitosamente")
    print(f"   ID generado: {doc.name}")
    print(f"   Status: {doc.docstatus}")
    
    # Verificar formato
    if doc.name.startswith("HP-"):
        print(f"   ✅ Formato correcto (SEQUENCE)")
    else:
        print(f"   ⚠️ Formato inesperado: {doc.name}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    frappe.log_error(str(e), "HistorialPagosTXT - Create Test")
EOF

'
```

---

### T7 — Validar en BD

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Últimos HP creados ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, creation FROM tabHistorial_Pagos_txt 
ORDER BY creation DESC LIMIT 5;
" 2>&1

echo "=== Verificar SEQUENCE counter ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_name = '"'"'seq_historial_pagos_txt'"'"';
" 2>&1

echo "=== Verificar DocType config final ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT allow_rename FROM tabDocType WHERE name = '"'"'Historial Pagos txt'"'"';
" 2>&1

echo "=== Verificar campo name config ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT fieldname, reqd, read_only, hidden
FROM tabDocField
WHERE parent = '"'"'Historial Pagos txt'"'"'
AND fieldname = '"'"'name'"'"';
" 2>&1

'
```

---

## 📋 Checklist

- [ ] T1: DocType auditado (autoname, allow_rename, campo name)
- [ ] T2: Archivos DocType localizados
- [ ] T3: DocType actualizado (allow_rename=0, name field: readonly+hidden)
- [ ] T4: Python `before_insert()` verificado/agregado
- [ ] T5: Cache limpiado, servicios reiniciados
- [ ] T6: Prueba creación exitosa (ID auto-generado)
- [ ] T7: BD validada (HP generado, SEQUENCE incremented)

---

## 📊 Reporte Final

Crear: `c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_009_fix-historial-campo-nombre-readonly.md`

Incluir:
1. **Problema Identificado** — Campo name editable/requerido
2. **Cambios Realizados** — DocType config + Python hook
3. **Validación** — Última HP creada, SEQUENCE counter, config final
4. **Status** — ✅/❌ campo auto-generado en forma

---

## 🔐 Credenciales

| Sistema | IP | Usuario | Contraseña |
|---|---|---|---|
| Backend | 164.92.94.47 | root | .Overskull2026.m |
| DB (privada) | 10.124.0.7 | root | .Overskull2026.m |

DB: `_0646d69b639ad0ff`

---

## ⚠️ CRÍTICO

**Resultado esperado:** Usuario abre Historial Pagos TXT → campo nombre **NO visible / auto-generado**.

No debe pedir input manual.

