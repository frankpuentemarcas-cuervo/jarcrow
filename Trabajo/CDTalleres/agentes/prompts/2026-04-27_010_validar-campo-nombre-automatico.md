---
fecha: 2026-04-27
agente_id: "010"
descripcion: "validar-campo-nombre-automatico-historial-pagos"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_010_validar-campo-nombre-automatico.md"
---

# Validación: Campo "nombre" Automático en Historial Pagos TXT

## 🎯 Objetivo

Validar que campo "nombre" (ID) en Historial Pagos TXT se genera **automáticamente** sin pedir input usuario.

**Contexto previo:**
- ✅ Prompt 008: Migración tabSeries → MariaDB SEQUENCE
- ✅ Prompt 009: Campo nombre debe ser readonly/hidden
- 🔜 Este prompt: Validar que todo funciona end-to-end

---

## 🔐 Acceso SSH (ACTUALIZADO - Sin Contraseña)

### Frontend (209.38.75.235)
```bash
ssh -i ~/.ssh/cdtalleres_frontend root@209.38.75.235
```

**Key:** `~/.ssh/cdtalleres_frontend` (ED25519)  
**Usuario:** `root`  
**Método:** SSH key (sin contraseña)

### Backend (164.92.94.47)
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47
```

**Usuario:** `root`  
**Contraseña:** `.Overskull2026.m`

### DB (165.232.130.222 / 10.124.0.7 privada)
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222
```

**Usuario:** `root`  
**Contraseña:** `.Overskull2026.m`  
**IP Privada:** `10.124.0.7` (desde backend/frontend en red privada)

---

## 📋 Tareas

### T1 — Conectar a Backend y verificar estado

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Verificar DocType config final ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name,
  autoname,
  allow_rename
FROM tabDocType 
WHERE name = '"'"'Historial Pagos txt'"'"';
" 2>&1

echo "=== Campo name config ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  fieldname,
  label,
  reqd,
  read_only,
  hidden
FROM tabDocField
WHERE parent = '"'"'Historial Pagos txt'"'"'
AND fieldname = '"'"'name'"'"';
" 2>&1

echo "=== SEQUENCE status ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_name = '"'"'seq_historial_pagos_txt'"'"';
" 2>&1

echo "=== Total HP en BD ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT COUNT(*) as total, MAX(SUBSTRING(name, 4)) as ultimo_numero
FROM tabHistorial_Pagos_txt;
" 2>&1

'
```

**Esperado:**
- `autoname = Prompt` ✅
- `allow_rename = 0` ✅
- Campo `name`: `reqd=0`, `read_only=1`, `hidden=1` ✅
- SEQUENCE activo, current_value > 112
- Total HP = 110+

---

### T2 — Verificar before_insert hook en Python

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Buscar before_insert en módulo ===" 
grep -A 8 "def before_insert" /home/erpnext/frappe-bench/apps/erpnext/erpnext/buying/doctype/historial_pagos_txt/historial_pagos_txt.py 2>&1

if [ $? -ne 0 ]; then
  echo "⚠️ before_insert NO encontrado — verificar si fue agregado"
fi

'
```

**Esperado:** Método `before_insert(self)` que genera ID con NEXTVAL(seq_historial_pagos_txt)

---

### T3 — Test de creación: Crear nuevo HP sin especificar nombre

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Test creación documento ===" 

bench --site $SITE console << "EOF"
import frappe

try:
    # Crear documento SIN especificar name
    doc = frappe.new_doc("Historial Pagos txt")
    
    # NO hacer: doc.name = "HP-00112" (debe ser auto-generado)
    
    # Campos mínimos requeridos
    doc.solicitud_de_pagos = "SP-TEST-AUTO"
    
    # Insert — before_insert() debe generar name
    doc.insert()
    
    print("✅ ÉXITO: Documento creado")
    print(f"   ID generado automáticamente: {doc.name}")
    print(f"   Docstatus: {doc.docstatus}")
    print(f"   Creation: {doc.creation}")
    
    # Validar formato HP-XXXXX
    if doc.name.startswith("HP-"):
        next_num = doc.name.split("-")[1]
        print(f"   ✅ Formato correcto: HP-{next_num}")
    else:
        print(f"   ❌ FORMATO INCORRECTO: {doc.name}")
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    frappe.log_error(f"Test creation error: {str(e)}", "HistorialPagosTXT")
    import traceback
    traceback.print_exc()
EOF

'
```

**Esperado:**
- ✅ Documento creado
- ✅ ID = HP-XXXXX (auto-generado, no user input)
- ✅ SIN errores

---

### T4 — Validar incremento SEQUENCE

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Verificar SEQUENCE incrementó ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_name = '"'"'seq_historial_pagos_txt'"'"';
" 2>&1

echo "=== Últimos 5 HP creados ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, creation FROM tabHistorial_Pagos_txt 
ORDER BY creation DESC LIMIT 5;
" 2>&1

'
```

**Esperado:**
- SEQUENCE current_value incrementado (vs. T1)
- Últimos HP incluyen nuevos creados en T3

---

### T5 — Prueba desde UI Frappe (si es posible)

**Opción A: Vía SSH en Backend (sin UI)**

Ya probado en T3 con bench console.

**Opción B: Vía Frontend Web (visual)**

Si tienes acceso a https://cdtalleres-copia.shalom.com.pe:

1. Login como `sistema-solicitud-pagos@shalom.com.pe`
2. Ir a Historial Pagos TXT → Nuevo
3. **Verificar:** Campo "nombre" NO aparece / está vacío (no pide input)
4. Llenar campos requeridos (ej. Solicitud de Pagos)
5. Guardar
6. **Resultado:** Nuevo HP-XXXXX generado automáticamente

---

### T6 — Revisar logs para confirmar no hay errores

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Últimos logs de Frappe ===" 
tail -100 /home/erpnext/frappe-bench/logs/frappe.log | grep -i "historial\|before_insert\|seq_historial" | tail -20

echo "=== Buscar errores ===" 
tail -50 /home/erpnext/frappe-bench/logs/frappe.log | grep -i "error\|exception\|traceback" | tail -10

'
```

**Esperado:** No hay errores de before_insert, SEQUENCE, o autoname.

---

### T7 — Validación Final

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Resumen Estado Final ===" 

echo "1. DocType Config:"
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT autoname, allow_rename FROM tabDocType WHERE name = '"'"'Historial Pagos txt'"'"';
" 2>&1 | tail -1

echo ""
echo "2. Campo name:"
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT CONCAT('"'"'readonly='"'"', read_only, '"'"' hidden='"'"', hidden, '"'"' reqd='"'"', reqd)
FROM tabDocField 
WHERE parent = '"'"'Historial Pagos txt'"'"' AND fieldname = '"'"'name'"'"';
" 2>&1 | tail -1

echo ""
echo "3. SEQUENCE:"
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" -e "
SELECT CONCAT('"'"'current_value='"'"', current_value) FROM information_schema.sequences
WHERE sequence_name = '"'"'seq_historial_pagos_txt'"'"';
" 2>&1 | tail -1

echo ""
echo "4. Total registros:"
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT CONCAT('"'"'Total HP='"'"', COUNT(*)) FROM tabHistorial_Pagos_txt;
" 2>&1 | tail -1

echo ""
echo "5. Servicios:"
supervisorctl status 2>&1 | grep -E "frappe-bench|worker" | head -3

'
```

---

## 📋 Checklist

- [ ] T1: DocType config verificado (autoname=Prompt, allow_rename=0, name field readonly+hidden)
- [ ] T2: before_insert hook presente en módulo Python
- [ ] T3: Test creación exitoso (HP auto-generado SIN input usuario)
- [ ] T4: SEQUENCE incrementó correctamente
- [ ] T5: Prueba UI exitosa (si aplica)
- [ ] T6: Logs sin errores
- [ ] T7: Validación final completa

---

## 📊 Reporte Final

Crear: `c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_010_validar-campo-nombre-automatico.md`

Incluir:
1. **Estado DocType** — autoname, allow_rename, campo name config
2. **Test Creación** — Output bench console (HP auto-generado)
3. **Validación BD** — SEQUENCE status, total HP, últimos IDs
4. **Status Final** — ✅/❌ campo nombre completamente automático
5. **Impacto** — Performance SEQUENCE vs tabSeries (locks eliminados)

---

## 🔐 Credenciales & Acceso

| Sistema | IP | Usuario | Método | Puerto |
|---|---|---|---|---|
| **Frontend** | 209.38.75.235 | root | SSH key `~/.ssh/cdtalleres_frontend` | 22 |
| **Backend** | 164.92.94.47 | root | SSH password `.Overskull2026.m` | 22 |
| **DB (Pública)** | 165.232.130.222 | root | SSH password `.Overskull2026.m` | 22 |
| **DB (Privada)** | 10.124.0.7 | root | SSH password `.Overskull2026.m` | 3306 |

**DB:** `_0646d69b639ad0ff`

---

## ⚠️ CRÍTICO

**Resultado esperado:** Usuario NO ve campo "nombre" en formulario Historial Pagos TXT. Se genera automáticamente con SEQUENCE lock-free.

**Si falla:** Revisar logs `/home/erpnext/frappe-bench/logs/frappe.log` para errores de before_insert.

