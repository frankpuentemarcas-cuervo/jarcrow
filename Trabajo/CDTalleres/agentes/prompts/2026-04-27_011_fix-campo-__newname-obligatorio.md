---
fecha: 2026-04-27
agente_id: "011"
descripcion: "fix-campo-__newname-obligatorio-historial"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_011_fix-campo-__newname-obligatorio.md"
---

# Fix: Campo `__newname` Obligatorio en Historial Pagos TXT

## 🎯 Problema

Usuario reporta: Al crear Historial Pagos TXT, campo `__newname` aparece **obligatorio**.

**Síntoma:**
- Forma Historial Pagos TXT muestra campo `__newname` con asterisco rojo (required)
- Impide guardar documento sin completar este campo
- Pero `__newname` debe ser auto-generado, no user input

**Root Cause:** Campo `__newname` es sistema Frappe (internal, para autoname=Prompt). Debe ser:
1. **Hidden** (no visible)
2. **ReadOnly** (no editable)
3. **Auto-poblado** por `before_insert()` hook
4. **NOT reqd=1** (nunca requerido)

---

## 🔍 Diagnóstico

`__newname` es campo interno de Frappe usado cuando `autoname='Prompt'`. Si aparece en forma como requerido, significa:

**Problema A:** Campo `__newname` tiene `reqd=1` en DocField  
**Problema B:** Campo `__newname` no tiene `hidden=1`  
**Problema C:** Campo no está mapeado correctamente en formulario

---

## 📋 Tareas

### T1 — Auditar DocType para campo __newname

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Buscar campo __newname ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  fieldname,
  fieldtype,
  label,
  reqd,
  read_only,
  hidden,
  depends_on
FROM tabDocField
WHERE parent = '"'"'Historial Pagos txt'"'"'
AND fieldname IN ('"'"'__newname'"'"', '"'"'name'"'"')
ORDER BY idx;
" 2>&1

echo "=== Todos los campos del DocType ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  idx,
  fieldname,
  fieldtype,
  reqd,
  hidden
FROM tabDocField
WHERE parent = '"'"'Historial Pagos txt'"'"'
ORDER BY idx;
" 2>&1

'
```

**Esperado:**
- `__newname`: `hidden=1`, `reqd=0`, `read_only=1`
- `name`: `hidden=1`, `reqd=0`, `read_only=1`

---

### T2 — Fijar campo __newname

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Actualizar __newname ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
UPDATE tabDocField 
SET reqd = 0, 
    read_only = 1, 
    hidden = 1,
    depends_on = NULL
WHERE parent = '"'"'Historial Pagos txt'"'"'
AND fieldname = '"'"'__newname'"'"';
" 2>&1

echo "=== Verificar cambio ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT fieldname, reqd, read_only, hidden
FROM tabDocField
WHERE parent = '"'"'Historial Pagos txt'"'"'
AND fieldname = '"'"'__newname'"'"';
" 2>&1

'
```

---

### T3 — Fijar campo name

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Actualizar name ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
UPDATE tabDocField 
SET reqd = 0, 
    read_only = 1, 
    hidden = 1
WHERE parent = '"'"'Historial Pagos txt'"'"'
AND fieldname = '"'"'name'"'"';
" 2>&1

echo "=== Verificar cambio ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT fieldname, reqd, read_only, hidden
FROM tabDocField
WHERE parent = '"'"'Historial Pagos txt'"'"'
AND fieldname IN ('"'"'name'"'"', '"'"'__newname'"'"');
" 2>&1

'
```

---

### T4 — Actualizar DocType vía Frappe API

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Recargar DocType en Frappe ===" 

bench --site $SITE console << "EOF"
import frappe

# Recargar DocType (evita cache stale)
frappe.get_meta("Historial Pagos txt", force=True)

print("✅ DocType reloaded")
EOF

'
```

---

### T5 — Limpiar cache completo

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

cd /home/erpnext/frappe-bench

echo "=== Limpiar cache ===" 
bench clear-cache 2>&1

echo "=== Limpiar cache Redis ===" 
redis-cli FLUSHALL 2>&1 || echo "Redis no disponible (ok si hay otra redis)"

echo "=== Reiniciar servicios ===" 
supervisorctl restart all 2>&1

echo "=== Esperar 5s ===" 
sleep 5

echo "=== Verificar status ===" 
supervisorctl status 2>&1 | head -5

'
```

---

### T6 — Test creación documento

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

# Obtener site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

echo "=== Test creación sin __newname ===" 

bench --site $SITE console << "EOF"
import frappe

try:
    # Crear documento VACÍO en __newname
    doc = frappe.new_doc("Historial Pagos txt")
    
    # NO setear __newname (debe ser auto-generado)
    # NO setear name (debe ser auto-generado por before_insert)
    
    # Campos mínimos
    doc.solicitud_de_pagos = "SP-TEST"
    
    # Insert
    doc.insert()
    
    print(f"✅ Documento creado exitosamente")
    print(f"   name (ID): {doc.name}")
    print(f"   __newname: {getattr(doc, '__newname', 'NOT SET')}")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
EOF

'
```

**Esperado:**
- ✅ Documento creado
- ✅ name = HP-XXXXX (auto-generado)
- ✅ SIN error de campo requerido

---

### T7 — Verificar formulario (opcional vía frontend)

Si tienes acceso web a https://cdtalleres-copia.shalom.com.pe:

1. Login
2. Ir a Historial Pagos TXT → Nuevo
3. **Verificar:** NO aparece campo `__newname` (hidden)
4. **Verificar:** NO aparece campo `nombre` requerido
5. Llenar campos mínimos
6. Guardar
7. **Resultado:** Documento creado con HP-XXXXX auto-generado

---

### T8 — Validación final

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Estado final campos críticos ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  fieldname,
  fieldtype,
  reqd,
  read_only,
  hidden
FROM tabDocField
WHERE parent = '"'"'Historial Pagos txt'"'"'
AND fieldname IN ('"'"'name'"'"', '"'"'__newname'"'"')
ORDER BY fieldname;
" 2>&1

echo ""
echo "=== Últimos HP creados ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name FROM tabHistorial_Pagos_txt 
ORDER BY creation DESC LIMIT 3;
" 2>&1

'
```

---

## 📋 Checklist

- [ ] T1: Auditado campo `__newname` (verificar reqd, hidden, read_only)
- [ ] T2: Campo `__newname` actualizado (reqd=0, hidden=1, read_only=1)
- [ ] T3: Campo `name` actualizado (reqd=0, hidden=1, read_only=1)
- [ ] T4: DocType reloaded en Frappe
- [ ] T5: Cache limpiado, servicios reiniciados
- [ ] T6: Test creación exitoso (SIN error campo requerido)
- [ ] T7: Verificación UI (opcional, si aplica)
- [ ] T8: Validación final (campos correcto, HP creados)

---

## 📊 Reporte Final

Crear: `c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_011_fix-campo-__newname-obligatorio.md`

Incluir:
1. **Problema Identificado** — Campo `__newname` obligatorio
2. **Root Cause** — Campo internal Frappe con reqd=1 / hidden=0
3. **Cambios Realizados** — Actualizar reqd=0, hidden=1, read_only=1
4. **Test Resultado** — Creación exitosa SIN input usuario
5. **Status Final** — ✅ Campos completamente automáticos

---

## 🔐 Acceso SSH

```bash
# Backend
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47

# DB (desde backend — red privada 10.124.0.7)
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff
```

---

## ⚠️ CRÍTICO

**Solución:** Campos `name` y `__newname` NUNCA deben ser requeridos. Frappe los genera automáticamente cuando `autoname='Prompt'`.

Resultado esperado: Usuario NO ve estos campos en formulario, se generan automáticamente.

