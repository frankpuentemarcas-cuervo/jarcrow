---
fecha: 2026-04-27
agente_id: "007"
descripcion: "fix-duplicateentryerror-solicitud-pagos-historial"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion
estado: completado
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_007_fix-solicitud-pagos-errores.md"
---

# Fix: DuplicateEntryError HP-00001 + Solicitud de Pagos (Contexto Completo)

## 🎯 Objetivo

Dos bugs CRÍTICOS en CDTALLERES servidor identificados por agente anterior:

1. **DuplicateEntryError "HP-00001"** → Autoname en DocType perdió counter
2. **Solicitud de Pagos panel vacío** → User sistema-solicitud-pagos@shalom.com.pe sin contexto correcto

El agente anterior NO tiene contexto completo. Tú tienes todo el histórico. **Ubica exactamente dónde están los errores y corrige EN EL SERVIDOR CORRECTO.**

---

## 📊 Contexto Completo

### Estado Actual (2026-04-27)

**CDTALLERES (ERPNext v15):**
- Servidor: 209.38.75.235 (frontend) + 164.92.94.47 (backend) + 165.232.130.222 (DB)
- Stack: 3 servidores separados (red privada 10.124.0.x)
- Usuario nuevo: sistema-solicitud-pagos@shalom.com.pe ✅ Creado
- API keys: 42571ea328dcc8a / eb15c1852486fd8 ✅ Generadas
- Bug JS: historial_pagos_txt.js línea 57 ✅ PARCIALMENTE FIXED

**RRHH (Laravel P-SERVICE):**
- Servidor: 157.245.187.72 (puerto 2324)
- .env actualizado: TOKEN_KEY_CDTALLERES y TOKEN_SECRET_CDTALLERES ✅
- Laravel cache limpiado ✅
- Apache reiniciado ✅

### Errores Pendientes

**Error 1: DuplicateEntryError "HP-00001"**
```
Doctype: Historial Pagos TXT
Síntoma: Click en "Generar TXT" (desde Solicitud de Pagos)
Error: DuplicateEntryError — intentar crear HP-00001 cuando YA EXISTE
Causa raíz: Contador de secuencia en autoname perdido
```

**Error 2: Panel Solicitud de Pagos Vacío**
```
Doctypes afectados:
  - Solicitud de Pagos (comprador: ACCGLE / MATSLE)
  - Historial Pagos TXT
Síntoma: Usuario sistema-solicitud-pagos@shalom.com.pe ve lista vacía
Causa probable: 
  a) Permisos DocType incorrectos
  b) Roles mal asignados
  c) Formulario no renderiza datos (verificar console browser)
```

---

## 🔧 Tareas a Ejecutar (EN ORDEN)

### T1 — Conectar a CDTALLERES backend y verificar estado

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Bench env info ==="
cd /home/erpnext/frappe-bench
bench --version

echo "=== Active site ==="
ls -la sites/

echo "=== Conectar a MariaDB (IP privada 10.124.0.7) ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT COUNT(*) as total_records FROM tabHistorial_Pagos_txt;
SELECT name FROM tabHistorial_Pagos_txt LIMIT 1;
" 2>&1

echo "=== Doctype: Historial Pagos TXT ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  dt.name,
  dt.autoname,
  dt.name_case
FROM tabDocType dt
WHERE dt.name = '"'"'Historial Pagos TXT'"'"';
" 2>&1

echo "=== tabSeries para Historial Pagos TXT (si existe) ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT * FROM tabSeries WHERE name LIKE '"'"'HP%'"'"';
" 2>&1

echo "=== SEQUENCES MariaDB (verificar si existe) ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_schema = '"'"'_0646d69b639ad0ff'"'"'
LIKE '"'"'%hist%'"'"';
" 2>&1

'
```

**Esperado:**
- Contador serie = HP-00001 o superior
- Si `tabSeries` vacío → usar SEQUENCE MariaDB
- Si no existe SEQUENCE → crear

---

### T2 — Verificar permisos usuario sistema-solicitud-pagos

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Usuario en ERPNext ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name,
  full_name,
  email,
  enabled,
  user_type
FROM tabUser
WHERE email = '"'"'sistema-solicitud-pagos@shalom.com.pe'"'"';
" 2>&1

echo "=== Roles asignados ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT role FROM tabHas_Role
WHERE parent = '"'"'sistema-solicitud-pagos@shalom.com.pe'"'"';
" 2>&1

echo "=== Permisos DocType: Solicitud de Pagos ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  role,
  read,
  write,
  create,
  delete
FROM tabDocPerm
WHERE parent = '"'"'Solicitud de Pagos'"'"'
ORDER BY role;
" 2>&1

echo "=== Permisos DocType: Historial Pagos TXT ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  role,
  read,
  write,
  create,
  delete
FROM tabDocPerm
WHERE parent = '"'"'Historial Pagos TXT'"'"'
ORDER BY role;
" 2>&1

'
```

**Esperado:**
- Usuario enabled = 1
- Roles incluyen "Concepto Solicitud de Pagos"
- DocPerm: read=1, write=1 para doctypes relevantes

---

### T3 — Fix DuplicateEntryError (Resetear autoname counter)

**Opción A: Si usa tabSeries (legacy)**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Verificar current counter en tabSeries ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT name, current FROM tabSeries
WHERE name LIKE '"'"'HP%'"'"';
" 2>&1

echo "=== Actualizar counter (siguiente valor disponible) ==="
# Primero obtener máximo actual
MAX_HP=$(mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT MAX(SUBSTRING(name, 4)) as max_num FROM tabHistorial_Pagos_txt;" 2>&1 | tail -1)

echo "Max HP actual: $MAX_HP"
NEXT_HP=$((${MAX_HP:-0} + 1))

mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
UPDATE tabSeries 
SET current = $NEXT_HP 
WHERE name = '"'"'HP'"'"';
" 2>&1

echo "✅ Counter actualizado a: $NEXT_HP"

'
```

**Opción B: Si usa MariaDB SEQUENCE**

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Verificar SEQUENCE para HP ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" -e "
SELECT sequence_name, current_value
FROM information_schema.sequences
WHERE sequence_schema = '"'"'_0646d69b639ad0ff'"'"'
AND sequence_name LIKE '"'"'%hist%'"'"';
" 2>&1

echo "=== Si no existe, CREAR SEQUENCE ==="
# Primero obtener max actual
MAX_HP=$(mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT MAX(SUBSTRING(name, 4)) as max_num FROM tabHistorial_Pagos_txt;" 2>&1 | tail -1)

NEXT_HP=$((${MAX_HP:-0} + 1))

mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
CREATE SEQUENCE IF NOT EXISTS seq_historial_pagos_txt START WITH $NEXT_HP;
" 2>&1

echo "✅ SEQUENCE creada/actualizada"

'
```

---

### T4 — Verificar DocType autoname config

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Autoname pattern en Historial Pagos TXT ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name,
  autoname,
  name_case
FROM tabDocType 
WHERE name = '"'"'Historial Pagos TXT'"'"';
" 2>&1

echo "=== Si autoname = '"'"'Prompt'"'"', verificar Server Script ==="
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name,
  script_type,
  script
FROM tabServer_Script
WHERE doctype_or_page = '"'"'Historial Pagos TXT'"'"'
AND event = '"'"'Before Insert'"'"';
" 2>&1

'
```

**Si autoname = 'Prompt':**
- Debe haber Server Script Before Insert que genere ID con SEQUENCE
- Si no existe → CREAR

---

### T5 — Prueba funcional: Generar TXT desde Solicitud de Pagos

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

echo "=== Test de creación de Historial Pagos TXT ==="

# Obtener site name
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | head -1)

cd /home/erpnext/frappe-bench

# Crear documento de test
bench --site $SITE execute frappe.client.insert "
{
  '"'"'doctype'"'"': '"'"'Historial Pagos TXT'"'"',
  '"'"'solicitud_de_pagos'"'"': '"'"'SP-00001'"'"'  # Reemplazar por SP real
}
" 2>&1

echo "=== Si falla: revisar error en frappe.log ==="
tail -50 /home/erpnext/frappe-bench/logs/frappe.log | grep -i "historial\|duplicate"

'
```

---

### T6 — Limpiar cache y reiniciar servicios

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '

cd /home/erpnext/frappe-bench

echo "=== Limpiar cache Frappe ==="
bench clear-cache 2>&1

echo "=== Reiniciar Gunicorn ==="
supervisorctl restart frappe-bench:* 2>&1

echo "=== Esperar 5s ==="
sleep 5

echo "=== Verificar status ==="
supervisorctl status 2>&1

'
```

---

## 📋 Checklist Final

- [ ] T1: Estado pre-fix verificado (contador actual, SEQUENCE status)
- [ ] T2: Usuario sistema-solicitud-pagos tiene permisos completos
- [ ] T3: Counter/SEQUENCE actualizado a siguiente valor disponible
- [ ] T4: Autoname config correcto (tabSeries o SEQUENCE)
- [ ] T5: Test de creación exitosa (HP-00002, HP-00003, etc.)
- [ ] T6: Cache limpiado, servicios reiniciados
- [ ] ✅ Panel Solicitud de Pagos visible para usuario
- [ ] ✅ Click "Generar TXT" → crea Historial sin DuplicateEntryError

---

## 📲 Reporte Final

Crear archivo: `c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_007_fix-solicitud-pagos-errores.md`

Incluir:
1. **Estado Pre-Fix** — Contador actual, SEQUENCE status, permisos
2. **Cambios Realizados** — Qué se modificó (tabla, valores antes/después)
3. **Prueba Funcional** — Output de test de creación
4. **Status Final** — ✅/❌ para cada item checklist
5. **Próximos Pasos** — Si quedó pendiente algo

---

## 🔐 Credenciales Disponibles

| Sistema | IP | Usuario | Contraseña | Puerto |
|---|---|---|---|---|
| CDTALLERES (backend) | 164.92.94.47 | root | .Overskull2026.m | 22 |
| CDTALLERES (DB) | 165.232.130.222 | root | .Overskull2026.m | 3306 (remoto) |
| RRHH (frontend) | 157.245.187.72 | root | .Overskull2026.g | 2324 |

**IP Privada DB:** 10.124.0.7 (desde cualquier servidor en red privada)

---

## ⚠️ CRÍTICO

**NO TOQUES RRHH EN ESTE PROMPT.** Agente anterior ya actualizó .env y Apache.

**SOLO TRABAJA EN CDTALLERES:** Ubicar + arreglar counters, permisos, autname configs.

