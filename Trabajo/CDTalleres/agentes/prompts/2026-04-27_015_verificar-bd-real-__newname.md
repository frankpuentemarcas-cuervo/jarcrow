---
fecha: 2026-04-27
agente_id: "015"
descripcion: "verificar-bd-real-dedicada-__newname-todos-doctypes"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion-diagnostico
estado: completado
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_015_verificar-bd-real-__newname.md"
---

# VERIFICAR BD REAL DEDICADA — `__newname` Sigue Visible

## 🎯 Hipótesis Crítica

Agentes 011-014 ejecutaron queries desde **backend (164.92.94.47)** usando `mysql -h 10.124.0.7`. Hasta hace poco DB dedicada (165.232.130.222 / 10.124.0.7) NO era accesible por SSH. Posible que:

1. Backend tenga mysql local respondiendo a queries (no llegaron a DB real)
2. App apunte a BD distinta a la que modificaron agentes
3. BD dedicada (real producción) NUNCA fue tocada
4. "Server-side limpio" reportado por 014 NO refleja BD real

**Si BD real conserva `__newname` original → explica por qué usuario sigue viéndolo.**

---

## 🔐 ACCESO SSH — TODOS CON LLAVE PÚBLICA

```bash
# Frontend
ssh -i ~/.ssh/cdtalleres_frontend root@209.38.75.235

# Backend
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47

# DB dedicada (recientemente accesible)
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222
```

**Key local:** `~/.ssh/cdtalleres_frontend` (ED25519)
**DB:** `_0646d69b639ad0ff`
**Pass MariaDB:** `.Overskull2026.m`

---

## 📋 Tareas de Verificación

### T1 — Confirmar qué BD usa app REALMENTE

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== site_config.json del site ===" 
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | grep -v common_site | head -1)
echo "SITE: $SITE"
cat /home/erpnext/frappe-bench/sites/$SITE/site_config.json 2>&1

echo ""
echo "=== common_site_config.json ===" 
cat /home/erpnext/frappe-bench/sites/common_site_config.json 2>&1

'
```

**Esperado:** Ver `db_host`, `db_name`, `db_password` reales que usa app.

---

### T2 — Verificar si backend tiene mysql LOCAL respondiendo

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Procesos mysql/mariadb en backend ===" 
ps aux | grep -i "mysql\|mariadb" | grep -v grep 2>&1

echo ""
echo "=== Puerto 3306 en backend ===" 
ss -tlnp | grep 3306 2>&1 || netstat -tlnp | grep 3306 2>&1

echo ""
echo "=== Resolver 10.124.0.7 ===" 
getent hosts 10.124.0.7 2>&1
ping -c 2 10.124.0.7 2>&1

'
```

**Esperado:** Confirmar si backend tiene mysql escuchando localmente o solo conecta remoto.

---

### T3 — Conexión DIRECTA a DB dedicada (sin pasar por backend)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222 '

echo "=== Hostname DB ===" 
hostname

echo ""
echo "=== Bases disponibles ===" 
mysql -u root -p".Overskull2026.m" -e "SHOW DATABASES;" 2>&1

echo ""
echo "=== Confirmar DB _0646d69b639ad0ff ===" 
mysql -u root -p".Overskull2026.m" -e "USE _0646d69b639ad0ff; SHOW TABLES LIKE '"'"'tabDocField'"'"';" 2>&1

'
```

**Esperado:** Confirmar DB existe en server dedicada, hostname = ERP-CD-TALLERES.

---

### T4 — Estado REAL de `__newname` en BD dedicada

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222 '

echo "=== Buscar __newname en tabDocField (BD REAL) ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  parent as doctype,
  fieldname,
  fieldtype,
  reqd,
  hidden,
  read_only,
  modified
FROM tabDocField
WHERE fieldname = '"'"'__newname'"'"'
ORDER BY parent;
" 2>&1

echo ""
echo "=== Buscar __newname en tabCustom_Field (BD REAL) ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  dt as doctype,
  fieldname,
  fieldtype,
  reqd,
  hidden,
  read_only,
  modified
FROM tabCustom_Field
WHERE fieldname = '"'"'__newname'"'"' OR fieldname LIKE '"'"'%newname%'"'"'
ORDER BY dt;
" 2>&1

echo ""
echo "=== Buscar __newname en tabProperty_Setter (BD REAL) ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  doc_type,
  field_name,
  property,
  value,
  modified
FROM tabProperty_Setter
WHERE field_name = '"'"'__newname'"'"' OR field_name LIKE '"'"'%newname%'"'"'
ORDER BY doc_type;
" 2>&1

echo ""
echo "=== Conteo total ocurrencias __newname ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  '"'"'tabDocField'"'"' as tabla,
  COUNT(*) as ocurrencias
FROM tabDocField WHERE fieldname = '"'"'__newname'"'"'
UNION ALL
SELECT 
  '"'"'tabCustom_Field'"'"',
  COUNT(*)
FROM tabCustom_Field WHERE fieldname = '"'"'__newname'"'"'
UNION ALL
SELECT 
  '"'"'tabProperty_Setter'"'"',
  COUNT(*)
FROM tabProperty_Setter WHERE field_name = '"'"'__newname'"'"';
" 2>&1

'
```

**Esperado:** Si BD dedicada tiene `__newname` con `hidden=0` o `reqd=1` → confirma agentes 011-013 NUNCA tocaron BD real.

---

### T5 — Comparar 7 doctypes objetivo (estado actual BD dedicada)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222 '

echo "=== Estado de 7 doctypes en BD REAL ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  parent as doctype,
  fieldname,
  reqd,
  hidden,
  read_only
FROM tabDocField
WHERE parent IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Historial Pagos txt'"'"'
)
AND fieldname IN ('"'"'__newname'"'"', '"'"'name'"'"')
ORDER BY parent, fieldname;
" 2>&1

'
```

**Esperado:** Si campos `__newname` aparecen aquí con `hidden=0` → BD real NO fue modificada por agentes anteriores.

---

### T6 — Verificar autoname y JSONs (BD dedicada)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222 '

echo "=== Autoname configurado en 7 doctypes (BD REAL) ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name as doctype,
  autoname,
  naming_rule,
  allow_rename
FROM tabDocType
WHERE name IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Orden de Trabajo 2'"'"',
  '"'"'Historial Notificaciones'"'"',
  '"'"'Historial Pagos txt'"'"'
)
ORDER BY name;
" 2>&1

'
```

---

### T7 — Frontend: verificar a qué backend apunta

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@209.38.75.235 '

echo "=== Hostname frontend ===" 
hostname

echo ""
echo "=== Config Nginx (upstream backend) ===" 
grep -r "proxy_pass\|upstream\|server " /etc/nginx/sites-enabled/ 2>&1 | head -30

echo ""
echo "=== Test conectividad backend desde frontend ===" 
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://10.124.0.9 2>&1 || echo "No conecta a 10.124.0.9"

'
```

**Esperado:** Confirmar frontend apunta a backend correcto (10.124.0.9).

---

### T8 — Comparar conteo: backend vs DB dedicada

```bash
echo "=== DESDE BACKEND (lo que vieron agentes 011-014) ===" 
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT COUNT(*) as count_backend
FROM tabDocField
WHERE fieldname = '"'"'__newname'"'"';
" 2>&1
'

echo ""
echo "=== DESDE DB DEDICADA DIRECTA ===" 
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT COUNT(*) as count_db_real
FROM tabDocField
WHERE fieldname = '"'"'__newname'"'"';
" 2>&1
'
```

**Esperado:** Ambos counts deben ser IGUAL si conectan a misma BD. Si difieren → confirma BD distintas.

---

### T9 — Verificar JSON files en backend (post 013)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Buscar __newname en JSONs (estado actual) ===" 
grep -rln "__newname" /home/erpnext/frappe-bench/apps/ --include="*.json" 2>/dev/null | head -20

echo ""
echo "=== Backups creados por agente 013 ===" 
find /home/erpnext/frappe-bench/apps/ -name "*.bak.*" 2>/dev/null | head -10

'
```

---

### T10 — Test API real desde browser (sin auth, validar endpoint)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222 '

echo "=== Test API metadata Purchase Order ===" 
curl -s -k "https://cdtalleres-copia.shalom.com.pe/api/method/frappe.desk.form.load.getdoctype?doctype=Purchase Order" 2>&1 | python3 -c "
import json, sys
try:
    raw = sys.stdin.read()
    data = json.loads(raw)
    docs = data.get('"'"'message'"'"', {}).get('"'"'docs'"'"', [])
    found = False
    for doc in docs:
        if doc.get('"'"'doctype'"'"') == '"'"'DocType'"'"':
            for f in doc.get('"'"'fields'"'"', []):
                fn = f.get('"'"'fieldname'"'"', '"'"''"'"')
                if '"'"'newname'"'"' in fn.lower():
                    found = True
                    print(f'"'"'⚠️ EN API: {fn} | hidden={f.get(\"hidden\")} | reqd={f.get(\"reqd\")}'"'"')
    if not found:
        print('"'"'✅ API NO contiene __newname'"'"')
except Exception as e:
    print(f'"'"'Error: {e}'"'"')
    print(raw[:500])
" 2>&1

'
```

---

## 📊 Reporte Obligatorio

Crear: `c:\jarcrow\Trabajo\CDTalleres\agentes\respuestas\2026-04-27_015_verificar-bd-real-__newname.md`

**Estructura:**

```markdown
# Verificación BD Real — __newname

## T1: Config app (qué BD usa)
RESULTADO: [pegar site_config.json EXACTO]
db_host real: [valor]
db_name real: [valor]

## T2: Backend tiene mysql local?
RESULTADO: [pegar output ps/ss]
CONCLUSIÓN: backend [tiene/no tiene] mysql local

## T3: Conexión directa DB dedicada
RESULTADO: [pegar output]
hostname DB: [valor]
DB existe: [si/no]

## T4: __newname en BD dedicada
tabDocField count: [N]
tabCustom_Field count: [N]
tabProperty_Setter count: [N]
[pegar registros exactos]

## T5: Estado 7 doctypes en BD real
[pegar tabla completa]
hidden=0 en: [lista]
reqd=1 en: [lista]

## T6: Autoname doctypes
[pegar tabla]

## T7: Frontend → backend
[pegar config nginx]

## T8: Comparación backend vs DB dedicada
count desde backend: [N]
count desde DB directa: [N]
SON IGUALES: [si/no]

## T9: JSONs estado actual
[lista archivos con __newname]
backups: [count]

## T10: API response real
[output curl]

## CONCLUSIÓN

**¿BD que usaron agentes 011-014 = BD real producción?** [SI/NO]

**Estado __newname en BD REAL (165.232.130.222):**
- tabDocField: [hidden=X, reqd=Y]
- tabCustom_Field: [presente/ausente]
- API response: [contiene/no contiene]

**Causa raíz:** [identificar]

**Siguiente acción:** [Aplicar fix en BD real / Otra cosa]
```

---

## ⚠️ INSTRUCCIONES CRÍTICAS

1. **NO MODIFICAR NADA** en T1-T10 — solo investigar
2. **PEGAR OUTPUTS EXACTOS** — no resumir
3. **CONECTAR DIRECTO** a DB dedicada (165.232.130.222), NO via backend para T3-T6
4. **COMPARAR** counts T8 — clave para confirmar hipótesis
5. Si T8 muestra counts distintos → agentes anteriores trabajaron BD equivocada

---

## 🎯 Resultado Esperado

Una de dos:

**Escenario A:** Counts T8 iguales, BD real ya tiene `__newname` con `hidden=1`
→ Problema es cache cliente (lo que dijo 014). Solución: cache bust Nginx.

**Escenario B:** Counts T8 distintos O BD real tiene `__newname` con `hidden=0`
→ Agentes 011-013 NUNCA tocaron BD real. Solución: aplicar fix DIRECTO en BD dedicada.

Este prompt distingue ambos escenarios con evidencia.
