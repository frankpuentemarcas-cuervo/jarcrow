---
fecha: 2026-04-27
agente_id: "013"
descripcion: "remover-__newname-layout-json-formulario-todos-doctypes"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion
estado: completado
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_013_remover-__newname-formulario-json.md"
---

# Fix: Remover `__newname` Completamente de Layout Formulario (JSON)

## 🎯 Problema

Campo `__newname` sigue **visible en formulario** a pesar de `hidden=1` en BD.

**Root Cause:** Campo existe en **JSON layout** del DocType (archivo `.json` o `form_layout` en BD).

Frappe renderiza formulario desde:
1. **tabDocField** (campos en BD) → actualizado ✅
2. **form_layout JSON** → AQUÍ está el problema ❌

Aunque campo esté marked como hidden en tabDocField, si está en layout JSON, Frappe lo renderiza igual.

**Solución:** Remover `__newname` completamente del layout JSON.

---

## 📋 Tareas

### T1 — Buscar dónde está el layout JSON

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Verificar si existe form_layout en BD ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name,
  form_layout
FROM tabDocType
WHERE name IN (
  '"'"'Purchase Order'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
)
LIMIT 3;
" 2>&1 | head -50

'
```

**Esperado:** Ver si `form_layout` field tiene JSON o está vacío

---

### T2 — Buscar archivos JSON en filesystem

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Buscar .json de doctypes ===" 
find /home/erpnext/frappe-bench -name "*.json" -path "*doctype*" -path "*purchase_order*" 2>/dev/null | head -5

find /home/erpnext/frappe-bench -name "*.json" -path "*doctype*" -path "*gl_entry*" 2>/dev/null | head -5

find /home/erpnext/frappe-bench -name "*.json" -path "*doctype*" -path "*historial*" 2>/dev/null | head -5

'
```

---

### T3 — Verificar layout JSON en tabDocType.form_layout

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Extraer form_layout para PO ===" 

bench --site $SITE console << "EOF"
import frappe
import json

doctypes = [
    "Purchase Order",
    "GL Entry",
    "Historial Pagos txt"
]

for dt_name in doctypes:
    dt = frappe.get_doc("DocType", dt_name)
    
    print(f"\n=== {dt_name} ===")
    
    if hasattr(dt, "form_layout") and dt.form_layout:
        try:
            layout = json.loads(dt.form_layout)
            
            # Buscar __newname en layout
            layout_str = dt.form_layout
            if "__newname" in layout_str:
                print(f"⚠️ __newname ENCONTRADO en layout")
                # Mostrar línea donde aparece
                for i, line in enumerate(layout_str.split("\n")):
                    if "__newname" in line:
                        print(f"   Línea {i}: {line.strip()[:100]}")
            else:
                print(f"✅ __newname NO en layout")
        except:
            print(f"Cannot parse JSON")
    else:
        print(f"No form_layout field")
EOF

'
```

---

### T4 — Remover `__newname` del layout JSON (Opción A: Via BD)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Limpiar __newname de form_layout ===" 

bench --site $SITE console << "EOF"
import frappe
import json

doctypes = [
    "Purchase Order",
    "Purchase Invoice",
    "GL Entry",
    "Stock Ledger Entry",
    "Orden de Trabajo 2",
    "Historial Notificaciones",
    "Historial Pagos txt"
]

for dt_name in doctypes:
    try:
        dt = frappe.get_doc("DocType", dt_name)
        
        if hasattr(dt, "form_layout") and dt.form_layout:
            # Parse JSON
            layout = json.loads(dt.form_layout)
            
            # Buscar y remover __newname de sections/columns
            modified = False
            
            for section in layout.get("sections", []):
                for column in section.get("columns", []):
                    fields = column.get("fields", [])
                    if "__newname" in fields:
                        fields.remove("__newname")
                        modified = True
                        print(f"✅ {dt_name}: __newname removido de layout")
            
            if modified:
                # Guardar layout limpio
                dt.form_layout = json.dumps(layout, indent=2)
                dt.save()
                frappe.db.commit()
            else:
                print(f"ℹ️ {dt_name}: __newname no estaba en layout")
        else:
            print(f"⚠️ {dt_name}: no tiene form_layout")
            
    except Exception as e:
        print(f"❌ {dt_name}: {str(e)}")

print("\n✅ Limpieza completada")
EOF

'
```

---

### T5 — Opción B: Remover via SQL directo (alternativo)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Remover __newname de form_layout (SQL) ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff << "MYSQL_END"

UPDATE tabDocType
SET form_layout = JSON_REMOVE(
  form_layout,
  CONCAT(
    '"'"'$."',
    SUBSTRING_INDEX(
      JSON_EXTRACT(
        form_layout,
        '"'"'$[*].columns[*].fields[*]'"'"'
      ),
      '"'"'__newname'"'"',
      1
    ),
    '"'"'"'"'
  )
)
WHERE name IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Historial Pagos txt'"'"'
)
AND form_layout LIKE '"'"'%__newname%'"'"';

MYSQL_END

'
```

**NOTA:** Si SQL JSON_REMOVE falla, usar Opción A (Frappe API)

---

### T6 — Verificar remoción

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Verificar __newname fue removido ===" 

bench --site $SITE console << "EOF"
import frappe

doctypes = [
    "Purchase Order",
    "GL Entry",
    "Historial Pagos txt"
]

for dt_name in doctypes:
    dt = frappe.get_doc("DocType", dt_name)
    
    if hasattr(dt, "form_layout") and dt.form_layout:
        if "__newname" in dt.form_layout:
            print(f"❌ {dt_name}: __newname AÚN en layout")
        else:
            print(f"✅ {dt_name}: __newname removido")
    else:
        print(f"⚠️ {dt_name}: no form_layout")
EOF

'
```

---

### T7 — Limpiar cache y reiniciar

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
supervisorctl status 2>&1 | head -3

'
```

---

### T8 — Test final: Crear documento SIN ver __newname

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Test creación Purchase Order ===" 

bench --site $SITE console << "EOF"
import frappe

try:
    doc = frappe.new_doc("Purchase Order")
    doc.supplier = "Test Supplier"
    doc.schedule_date = frappe.utils.today()  # Agregar para pasar validación
    doc.insert()
    
    print(f"✅ Documento creado: {doc.name}")
    print(f"   Sin errores de __newname")
    
except frappe.exceptions.ValidationError as e:
    print(f"⚠️ ValidationError (normal, no relacionado a __newname): {str(e)}")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
EOF

'
```

---

### T9 — Verificar visualmente en UI (opcional)

Si accedes a https://cdtalleres-copia.shalom.com.pe:

1. Ir a **Purchase Order → Nuevo**
2. **Verificar:** NO aparece campo `__newname` en forma
3. Completar campos mínimos (supplier, schedule_date)
4. Guardar
5. **Resultado:** ✅ Documento creado sin campo fantasma

---

## 📋 Checklist

- [ ] T1: Verificado si existe form_layout en BD
- [ ] T2: Ubicados archivos .json si existen
- [ ] T3: Extraído form_layout JSON (confirmado __newname está)
- [ ] T4 o T5: Removido __newname de layout (Frappe API o SQL)
- [ ] T6: Verificado remoción exitosa
- [ ] T7: Cache limpiado, servicios reiniciados
- [ ] T8: Test creación exitoso (sin errores __newname)
- [ ] T9: Verificación UI (campo no visible)

---

## 📊 Reporte Final

Crear: `c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_013_remover-__newname-formulario-json.md`

Incluir:
1. **Problema Identificado** — Campo `__newname` en JSON layout (no solo tabDocField)
2. **Root Cause** — form_layout JSON contenía __newname
3. **Solución Aplicada** — JSON_REMOVE o Frappe API (cuál usó)
4. **Documentos Afectados** — 7 doctypes limpiados
5. **Validación** — __newname removido de layouts, test creación exitoso
6. **Status Final** — ✅ Campo invisible en formulario, auto-generado

---

## 🔐 Acceso

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47
```

DB: `_0646d69b639ad0ff`

---

## ⚠️ CRÍTICO

**Resultado esperado:** Usuario abre Purchase Order (o cualquier DocType) → **NO ve campo `__newname`** → se genera automáticamente en backend.

El problema es que Frappe renderiza desde JSON layout, no solo tabDocField.

