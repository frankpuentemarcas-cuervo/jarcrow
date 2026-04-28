---
fecha: 2026-04-27
agente_id: "014"
descripcion: "diagnostico-profundo-__newname-todas-fuentes"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion-diagnostico
estado: completado
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_014_diagnostico-profundo-__newname.md"
---

# DIAGNÓSTICO PROFUNDO: ¿Por qué `__newname` SIGUE visible?

## 🔐 ACCESO SSH — USAR LLAVE PÚBLICA

**Frontend (209.38.75.235) — SSH KEY (sin contraseña):**

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@209.38.75.235
```

**Key location en máquina local:** `~/.ssh/cdtalleres_frontend` (ED25519)
**Public key fingerprint:** `SHA256:9UblAz+cfQSJLHeQj2FpjyhBjrh05bg3ua8EfI89d5g`

**Backend (164.92.94.47) — SSH password:**
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47
```

**DB (10.124.0.7 privada / 165.232.130.222 pública) — SSH password:**
```bash
# Desde backend (red privada):
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff

# Directo SSH:
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222
```

**⚠️ Frontend NO acepta password.** Usar SOLO llave pública `~/.ssh/cdtalleres_frontend`.

---

## 🎯 Contexto

Agentes 011, 012, 013 dijeron `__newname` removido. Usuario sigue viéndolo.

**Necesitamos REALMENTE encontrar de dónde viene.** No asumir, solo VERIFICAR cada fuente posible.

---

## 🔍 Hipótesis a Verificar

### H1: Custom Fields (tabCustom_Field)
Frappe permite agregar campos vía Custom Field SIN modificar DocType. Estos NO están en JSON ni tabDocField.

### H2: Property Setter (tabProperty_Setter)
Property Setters override propiedades de campos. Puede haber uno que mantenga `__newname` visible.

### H3: Browser Cache / LocalStorage
Frappe cachea metadata client-side. Aunque server esté limpio, browser ve versión vieja.

### H4: Asset Build (bench build)
Frappe compila JS/CSS. Cambios en JSON no se reflejan hasta rebuild.

### H5: Custom Form Layout (frappe.form.layout)
Form Builder de Frappe v15 puede tener layout custom en `tabCustom_HTML` o tablas similares.

### H6: Bench Migrate Pendiente
Cambios en JSON pueden requerir `bench migrate` para sincronizar con BD.

### H7: Doctype JSON readonly source
Si app es no-developer-mode, JSON file changes no toman efecto. Frappe usa BD como source.

### H8: No es __newname sino otro campo
Tal vez usuario ve campo similar pero llamado diferente (`name`, `__islocal`, etc.)

---

## 📋 Tareas de Diagnóstico (NO MODIFICAR — SOLO INVESTIGAR)

### T1 — Verificar Custom Fields

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Custom Fields para los 7 doctypes ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  dt as doctype,
  fieldname,
  fieldtype,
  label,
  reqd,
  hidden,
  read_only
FROM tabCustom_Field
WHERE dt IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Historial Pagos txt'"'"'
)
AND (fieldname LIKE '"'"'%newname%'"'"' OR fieldname LIKE '"'"'%name%'"'"')
ORDER BY dt;
" 2>&1

'
```

---

### T2 — Verificar Property Setters

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Property Setters relacionados a __newname o name ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  doc_type,
  field_name,
  property,
  value,
  property_type
FROM tabProperty_Setter
WHERE doc_type IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Historial Pagos txt'"'"'
)
AND (field_name = '"'"'__newname'"'"' OR field_name = '"'"'name'"'"' OR property LIKE '"'"'%newname%'"'"');
" 2>&1

echo ""
echo "=== TODOS los Property Setters de Purchase Order ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT field_name, property, value 
FROM tabProperty_Setter
WHERE doc_type = '"'"'Purchase Order'"'"'
LIMIT 30;
" 2>&1

'
```

---

### T3 — Verificar metadata real que envía Frappe al frontend

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Metadata real de Purchase Order ===" 

bench --site $SITE console << "PYEOF"
import frappe
import json

# Obtener meta como Frappe la envía al cliente
meta = frappe.get_meta("Purchase Order")

# Verificar todos los campos
all_fields = meta.fields
print(f"Total fields: {len(all_fields)}")

# Buscar __newname
for f in all_fields:
    if "newname" in f.fieldname.lower() or f.fieldname == "name":
        print(f"\n--- CAMPO ENCONTRADO ---")
        print(f"  fieldname: {f.fieldname}")
        print(f"  fieldtype: {f.fieldtype}")
        print(f"  hidden: {f.hidden}")
        print(f"  reqd: {f.reqd}")
        print(f"  read_only: {f.read_only}")
        print(f"  label: {f.label}")

# Verificar autoname
print(f"\nautoname: {meta.autoname}")
print(f"allow_rename: {meta.allow_rename}")
print(f"naming_rule: {getattr(meta, 'naming_rule', 'N/A')}")
PYEOF

'
```

---

### T4 — Verificar Client Scripts

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Client Scripts que mencionan __newname ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name,
  dt,
  view,
  enabled
FROM tabClient_Script
WHERE script LIKE '"'"'%newname%'"'"'
OR dt IN (
  '"'"'Purchase Order'"'"',
  '"'"'Historial Pagos txt'"'"'
);
" 2>&1

'
```

---

### T5 — Verificar Server Scripts

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Server Scripts ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name,
  doctype_event,
  reference_doctype,
  script_type,
  disabled
FROM tabServer_Script
WHERE reference_doctype IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Historial Pagos txt'"'"'
)
ORDER BY reference_doctype;
" 2>&1

'
```

---

### T6 — Verificar JSON files (estado actual post-013)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Buscar __newname en TODOS los JSON ===" 
grep -rln "__newname" /home/erpnext/frappe-bench/apps/ --include="*.json" 2>/dev/null

echo ""
echo "=== Verificar autoname en JSONs ===" 
grep -A 1 "\"autoname\"" /home/erpnext/frappe-bench/apps/erpnext/erpnext/buying/doctype/purchase_order/purchase_order.json | head -5

'
```

---

### T7 — Verificar estructura HTML del formulario (network response)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Simular qué envía Frappe al cliente al cargar form ===" 

bench --site $SITE console << "PYEOF"
import frappe
import json

# Esto es lo que el cliente recibe via /api/method/frappe.desk.form.load.getdoc
meta = frappe.get_meta("Purchase Order")
client_meta = meta.as_dict()

# Buscar campos relacionados a name en la respuesta cliente
for field in client_meta.get("fields", []):
    if "newname" in field.get("fieldname", "").lower():
        print(f"\n⚠️ __newname AÚN está en client meta:")
        print(json.dumps(field, indent=2, default=str))
        break
else:
    print("✅ __newname NO está en client meta enviado al frontend")

# También revisar autoname
print(f"\nautoname configurado: {client_meta.get('autoname')}")
print(f"naming_rule: {client_meta.get('naming_rule')}")
PYEOF

'
```

---

### T8 — Verificar si bench migrate actualizó BD desde JSON

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Estado developer_mode ===" 
cat sites/$SITE/site_config.json 2>/dev/null | grep -i "developer\|maintenance" | head -5

echo ""
echo "=== Estado del DocType en BD vs JSON ===" 

bench --site $SITE console << "PYEOF"
import frappe

# Verificar developer_mode
import frappe.utils
print(f"developer_mode: {frappe.conf.get('developer_mode')}")

# Verificar si DocType tiene cambios pendientes
dt = frappe.get_doc("DocType", "Purchase Order")
print(f"\nautoname en BD: {dt.autoname}")
print(f"Total fields en BD: {len(dt.fields)}")

# Buscar __newname
newname_fields = [f for f in dt.fields if f.fieldname == "__newname"]
print(f"\n__newname fields en BD: {len(newname_fields)}")
if newname_fields:
    f = newname_fields[0]
    print(f"  hidden: {f.hidden}")
    print(f"  reqd: {f.reqd}")
PYEOF

'
```

---

### T9 — Verificar HTML real del form (curl session)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Test directo: Obtener meta via API ===" 

# Simular llamada API que hace el browser
curl -s "https://cdtalleres-copia.shalom.com.pe/api/method/frappe.desk.form.load.getdoctype?doctype=Purchase Order" \
  -H "Cookie: sid=Guest" \
  -k 2>&1 | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    docs = data.get('message', {}).get('docs', [])
    for doc in docs:
        if doc.get('doctype') == 'DocType' and doc.get('name') == 'Purchase Order':
            print(f\"autoname: {doc.get('autoname')}\")
            for f in doc.get('fields', []):
                if 'newname' in f.get('fieldname', '').lower():
                    print(f\"⚠️ __newname EN API RESPONSE: {f}\")
                    break
            else:
                print('✅ __newname NO está en respuesta API')
except Exception as e:
    print(f'Error parsing: {e}')
" 2>&1 | head -20

'
```

---

### T10 — Verificar si el campo visualmente puede ser otro

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Listar TODOS los campos visibles en Purchase Order ===" 

bench --site $SITE console << "PYEOF"
import frappe

meta = frappe.get_meta("Purchase Order")

print("Campos NO ocultos en Purchase Order:")
print("-" * 80)
for f in meta.fields:
    if not f.hidden and f.fieldtype not in ("Section Break", "Column Break", "Tab Break"):
        marker = "🔴 REQ" if f.reqd else "  "
        ro = "🔒 RO" if f.read_only else "  "
        print(f"  {marker} {ro} {f.fieldname:30s} | {f.fieldtype:15s} | {f.label or 'NO_LABEL'}")
PYEOF

'
```

---

## 📊 Reporte de Diagnóstico

Crear: `c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_014_diagnostico-profundo-__newname.md`

**Estructura obligatoria:**

```markdown
# Diagnóstico __newname

## H1: Custom Fields
RESULTADO T1: [pegar output exacto]
HIPÓTESIS: ✅ Confirmada / ❌ Descartada
RAZÓN: [explicar]

## H2: Property Setters
RESULTADO T2: [pegar output exacto]
HIPÓTESIS: ✅/❌
RAZÓN: ...

## H3: Metadata real Frappe envía
RESULTADO T3: [output]
HIPÓTESIS: ✅/❌

## H4: Client Scripts
RESULTADO T4: ...

## H5: Server Scripts
RESULTADO T5: ...

## H6: JSON files
RESULTADO T6: ...

## H7: Client meta API response
RESULTADO T7: ...

## H8: Bench migrate / developer_mode
RESULTADO T8: ...

## H9: API response real
RESULTADO T9: ...

## H10: Campos visibles
RESULTADO T10: ...

## CONCLUSIÓN
**Fuente real de __newname:** [identificar]
**Solución propuesta:** [acción concreta]
```

---

## ⚠️ INSTRUCCIONES CRÍTICAS

1. **NO MODIFICAR NADA** — solo investigar
2. **Pegar OUTPUTS EXACTOS** de cada query — no resúmenes
3. **NO ASUMIR** que el problema fue resuelto — VERIFICAR cada hipótesis
4. **Si duda:** pegar más output, no menos

Si el problema persiste después de 011-013, significa que estamos atacando la fuente equivocada. Este prompt encuentra la fuente real.

---

## 🔐 Acceso (Recordatorio)

| Servidor | IP | Método |
|---|---|---|
| **Frontend** | 209.38.75.235 | `ssh -i ~/.ssh/cdtalleres_frontend root@209.38.75.235` (KEY) |
| **Backend** | 164.92.94.47 | `sshpass -p '.Overskull2026.m' ssh root@164.92.94.47` |
| **DB** | 165.232.130.222 / 10.124.0.7 | `sshpass -p '.Overskull2026.m' ssh root@165.232.130.222` |

**DB:** `_0646d69b639ad0ff` (10.124.0.7 desde backend — preferido)

**⚠️ Frontend SOLO acepta SSH key.** Si necesitas tocar Nginx/assets/static files, usar key.
