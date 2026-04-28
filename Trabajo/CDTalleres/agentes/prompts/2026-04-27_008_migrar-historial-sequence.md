---
fecha: 2026-04-27
agente_id: "008"
descripcion: "migrar-historial-pagos-txt-a-sequence"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion
estado: completado
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_008_migrar-historial-sequence.md"
---

# CORRECCIÓN URGENTE: Migrar Historial Pagos TXT de tabSeries → MariaDB SEQUENCE

## 🚨 PROBLEMA

Agente 007 reactivó `tabSeries` (legacy, lento) para Historial Pagos TXT.

**Línea problemática:**
```sql
UPDATE tabSeries SET current = 112 WHERE name = 'HP--FROZEN';
```

**Consecuencia:** Vuelve a saturar BD con SELECT FOR UPDATE en cada insert (mismo problema que GL Entry, Stock Ledger tenían antes).

**Historial de optimizaciones perdidas:**
- ✅ GL Entry: tabSeries → seq_gl_entry (lock_time: 14,000ms → 0ms)
- ✅ Stock Ledger: tabSeries → seq_stock_ledger (lock_waits: 29 → 0)
- ❌ Historial Pagos TXT: **VOLVIÓ A tabSeries** (REGRESIÓN)

---

## 🎯 Objetivo

Completar la migración de Historial Pagos TXT a MariaDB SEQUENCE sin perder registros existentes.

**Resultado esperado:**
- SEQUENCE `seq_historial_pagos_txt` activa (START 112)
- `tabSeries` registro `HP--FROZEN` eliminado
- Siguiente HP-00112 generado sin locks InnoDB

---

## 📋 Tareas a Ejecutar

### T1 — Conectar y auditar estado actual

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Verificar tabSeries HP ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT * FROM tabSeries WHERE name LIKE '"'"'HP%'"'"';
" 2>&1

echo "=== Verificar si SEQUENCE ya existe ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_schema = '"'"'_0646d69b639ad0ff'"'"'
AND sequence_name = '"'"'seq_historial_pagos_txt'"'"';
" 2>&1

echo "=== Último HP creado ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT MAX(SUBSTRING(name, 4)) as ultimo_numero FROM tabHistorial_Pagos_txt;
" 2>&1

'
```

**Esperado:**
- `HP--FROZEN` = 112 (actual después de fix 007)
- No existe `seq_historial_pagos_txt` aún
- Último HP en BD = HP-00111

---

### T2 — Crear SEQUENCE en MariaDB

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== CREAR SEQUENCE ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
CREATE SEQUENCE seq_historial_pagos_txt START WITH 112;
" 2>&1

echo "=== Verificar creación ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_schema = '"'"'_0646d69b639ad0ff'"'"'
AND sequence_name = '"'"'seq_historial_pagos_txt'"'"';
" 2>&1

'
```

**Verificar:** SEQUENCE activa, current_value = 112

---

### T3 — Cambiar DocType autoname a "Prompt"

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Cambiar autoname a Prompt ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
UPDATE tabDocType 
SET autoname = '"'"'Prompt'"'"'
WHERE name = '"'"'Historial Pagos txt'"'"';
" 2>&1

echo "=== Verificar cambio ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, autoname FROM tabDocType 
WHERE name = '"'"'Historial Pagos txt'"'"';
" 2>&1

'
```

---

### T4 — Crear Server Script Before Insert para generar ID

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Crear Server Script ===" 

# Script que genera HP-XXXXXX con NEXTVAL(sequence)
bench --site $SITE console << "EOF"
import frappe

script_content = """
def before_insert(doc, method):
    # Generar ID con SEQUENCE lock-free
    next_num = frappe.db.sql(
        "SELECT NEXTVAL(seq_historial_pagos_txt) AS next_val",
        as_dict=True
    )[0].get("next_val")
    doc.name = f"HP-{next_num:05d}"
"""

# Eliminar script anterior si existe
existing = frappe.get_value(
    "Server Script",
    {"doctype_or_page": "Historial Pagos txt", "event": "Before Insert"},
    ["name"]
)
if existing:
    frappe.delete_doc("Server Script", existing[0][0], force=True)

# Crear nuevo
doc = frappe.new_doc("Server Script")
doc.name = "HP - Generate ID with SEQUENCE"
doc.doctype_or_page = "Historial Pagos txt"
doc.event = "Before Insert"
doc.script = script_content
doc.insert(force=True)

frappe.db.commit()
print("✅ Server Script creado")
EOF

'
```

**Verificar en Frappe UI:**
- Setup → Server Script
- Buscar "HP - Generate ID with SEQUENCE"
- Doctype: Historial Pagos txt
- Event: Before Insert

---

### T5 — Eliminar tabSeries registro HP--FROZEN

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Eliminar tabSeries HP (ya no necesaria) ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
DELETE FROM tabSeries WHERE name LIKE '"'"'HP%'"'"';
" 2>&1

echo "=== Verificar eliminación ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT COUNT(*) FROM tabSeries WHERE name LIKE '"'"'HP%'"'"';
" 2>&1

'
```

**Esperado:** 0 registros (limpio)

---

### T6 — Limpiar cache y restart servicios

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

cd /home/erpnext/frappe-bench

echo "=== Limpiar cache ===" 
bench clear-cache 2>&1

echo "=== Reiniciar servicios ===" 
supervisorctl restart all 2>&1

echo "=== Esperar 5s ===" 
sleep 5

echo "=== Verificar status ===" 
supervisorctl status 2>&1

'
```

---

### T7 — Prueba: Crear nuevo Historial Pagos txt

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Test creación documento ===" 

bench --site $SITE console << "EOF"
import frappe

# Crear test doc
doc = frappe.new_doc("Historial Pagos txt")
doc.solicitud_de_pagos = "SP-00001"  # O el ID real que exista
try:
    doc.insert()
    print(f"✅ Documento creado: {doc.name}")
    print(f"   Type: {type(doc.name)}")
    # Verificar que sea HP-XXXXX
    if doc.name.startswith("HP-"):
        print(f"   ✅ ID formato correcto (SEQUENCE)")
    else:
        print(f"   ❌ ID formato incorrecto: {doc.name}")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    frappe.log_error(str(e), "HP Test Create")
EOF

echo "=== Verificar en BD ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, creation FROM tabHistorial_Pagos_txt 
ORDER BY creation DESC LIMIT 3;
" 2>&1

echo "=== Verificar SEQUENCE contador ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_name = '"'"'seq_historial_pagos_txt'"'"';
" 2>&1

'
```

**Esperado:**
- Documento creado: HP-00112 (o superior)
- SEQUENCE current_value = 113 (incrementado)
- Error: NINGUNO

---

### T8 — Validar proceso completo

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Total registros Historial ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT COUNT(*) as total FROM tabHistorial_Pagos_txt;
" 2>&1

echo "=== Últimos 5 HP creados ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, creation FROM tabHistorial_Pagos_txt 
ORDER BY creation DESC LIMIT 5;
" 2>&1

echo "=== Verificar NO exista tabSeries HP ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT COUNT(*) as tabseries_hp FROM tabSeries WHERE name LIKE '"'"'HP%'"'"';
" 2>&1

echo "=== Verificar DocType autoname ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, autoname FROM tabDocType WHERE name = '"'"'Historial Pagos txt'"'"';
" 2>&1

echo "=== Verificar Server Script ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, doctype_or_page, event FROM tabServer_Script
WHERE doctype_or_page = '"'"'Historial Pagos txt'"'"'
AND event = '"'"'Before Insert'"'"';
" 2>&1

'
```

---

## 📋 Checklist

- [ ] T1: Estado pre-migración auditado (tabSeries HP = 112)
- [ ] T2: SEQUENCE `seq_historial_pagos_txt` creada (START 112)
- [ ] T3: DocType autoname cambiado a "Prompt"
- [ ] T4: Server Script Before Insert creado
- [ ] T5: tabSeries HP eliminada (limpio)
- [ ] T6: Cache limpiado, servicios reiniciados
- [ ] T7: Prueba creación exitosa (HP-00112 o superior)
- [ ] T8: Validación final (SEQUENCE activa, tabSeries limpio, Server Script funcional)

---

## 📊 Reporte Final

Crear: `c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_008_migrar-historial-sequence.md`

Incluir:
1. **Estado Pre-Migración** — tabSeries status, SEQUENCE no existe
2. **Pasos Ejecutados** — T1-T8 con outputs completos
3. **Validación** — Total HP, últimos creados, SEQUENCE counter
4. **Status Final** — ✅/❌ para cada checklist item
5. **Impacto de Performance** — Antes (tabSeries locks) vs Después (SEQUENCE lock-free)

---

## 🔐 Credenciales

| Sistema | IP | Usuario | Contraseña |
|---|---|---|---|
| Backend CDTALLERES | 164.92.94.47 | root | .Overskull2026.m |
| DB (privada) | 10.124.0.7 | root | .Overskull2026.m |

DB: `_0646d69b639ad0ff`

---

## ⚠️ CRÍTICO

**NO dejar tabSeries activa.** Eso anula optimizaciones previas de GL Entry y Stock Ledger.

**Resultado esperado:** Historial Pagos TXT usa SEQUENCE lock-free como GL Entry y Stock Ledger.

