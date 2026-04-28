---
fecha: 2026-04-27
agente_id: "019"
descripcion: "restore-client-scripts-hide-newname-confirmado-autoname-prompt-obligatorio"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: restauracion
estado: completado
archivo_salida: "c:\jarcrow\Trabajo\CDTalleres\agentes\respuestas\2026-04-27_019_restore-client-scripts.md"
---

# RESTAURACIÓN — Client Scripts CDT-Hide-Newname* (autoname='Prompt' Obligatorio)

## 🎯 Contexto de Agente 018

Agente 018 descubrió conflicto arquitectónico CRÍTICO (línea 80 resultado):

> "autoname='hash' sobrescribe cualquier asignación doc.name en before_insert. Para que las secuencias de MariaDB funcionen mediante Server Scripts, el DocType debe tener autoname='Prompt'."

**Evidencia:**
- T7 resultado: Historial Pagos txt = 20 docs creados exitosamente (formato HPT-XXXXX) tras CAMBIAR de autoname='hash' a autoname='Prompt'
- Otros doctypes fallaron con autoname='hash' (dependencias de datos)

**Conclusión 018:** autoname='Prompt' es OBLIGATORIO para SEQUENCE funcionar.

**Problema:** autoname='Prompt' causa Frappe inyecte __newname como campo virtual en cliente.

**Solución:** Mantener autoname='Prompt' + Restaurar Client Scripts CDT-Hide-Newname que ocultan __newname

---

## 🗂️ Prefijos Correctos (Histórico Confirmado)

| DocType | Secuencia | Prefijo CORRECTO | Formato | Ejemplo |
|---|---|---|---|---|
| Purchase Order | seq_purchase_order | `OC-` | `OC-%06d` | `OC-008255` |
| Purchase Invoice | seq_purchase_invoice | `FC-` | `FC-%06d` | `FC-008057` |
| GL Entry | seq_gl_entry | `GLE-` | `GLE-%06d` | `GLE-400001` |
| Stock Ledger Entry | seq_stock_ledger | `SLE-` | `SLE-%06d` | `SLE-350001` |
| Historial Pagos txt | seq_historial_pagos_txt | `HP-` | `HP-%05d` | `HP-000112` |

**Nota:** Agente 018 reportó HPT-000211 para Historial Pagos txt → prefijo `HPT-` incorrecto, debe ser `HP-`. Server Scripts pueden haber sido modificados.

---

## 📋 Tareas Restauración

### T0 — Auditar estado REAL de BD: prefijos actuales + SEQUENCE values

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Prefijos en uso ACTUALMENTE en BD (últimos 5 docs por doctype) ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "

-- Purchase Order: prefijo real
SELECT '"'"'Purchase Order'"'"' as doctype, name, creation FROM tabPurchase_Order ORDER BY creation DESC LIMIT 5;

-- Purchase Invoice
SELECT '"'"'Purchase Invoice'"'"' as doctype, name, creation FROM tabPurchase_Invoice ORDER BY creation DESC LIMIT 5;

-- GL Entry
SELECT '"'"'GL Entry'"'"' as doctype, name, creation FROM tabGL_Entry ORDER BY creation DESC LIMIT 5;

-- Stock Ledger Entry
SELECT '"'"'Stock Ledger Entry'"'"' as doctype, name, creation FROM tabStock_Ledger_Entry ORDER BY creation DESC LIMIT 5;

-- Historial Pagos txt
SELECT '"'"'Historial Pagos txt'"'"' as doctype, name, creation FROM tabHistorial_Pagos_txt ORDER BY creation DESC LIMIT 5;

" 2>&1

echo ""
echo "=== Estado actual SEQUENCEs (next value a generar) ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT sequence_name, NEXT_VALUE as proximo_id, INCREMENT
FROM information_schema.SEQUENCES
WHERE sequence_name IN (
  '"'"'seq_purchase_order'"'"',
  '"'"'seq_purchase_invoice'"'"',
  '"'"'seq_gl_entry'"'"',
  '"'"'seq_stock_ledger'"'"',
  '"'"'seq_historial_pagos_txt'"'"'
)
ORDER BY sequence_name;
" 2>&1

echo ""
echo "=== Conteo total docs por doctype ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  '"'"'Purchase Order'"'"' as doctype, COUNT(*) as total, LEFT(MAX(name),5) as prefijo_max FROM tabPurchase_Order
UNION ALL
SELECT '"'"'Purchase Invoice'"'"', COUNT(*), LEFT(MAX(name),5) FROM tabPurchase_Invoice
UNION ALL
SELECT '"'"'GL Entry'"'"', COUNT(*), LEFT(MAX(name),5) FROM tabGL_Entry
UNION ALL
SELECT '"'"'Stock Ledger Entry'"'"', COUNT(*), LEFT(MAX(name),5) FROM tabStock_Ledger_Entry
UNION ALL
SELECT '"'"'Historial Pagos txt'"'"', COUNT(*), LEFT(MAX(name),5) FROM tabHistorial_Pagos_txt;
" 2>&1

'
```

**Decisión basada en T0:**
- Si BD tiene mayoría de docs con prefijo histórico (OC-, FC-, HP-) → Server Scripts estaban correctos, 018 usó prefijo diferente solo en test
- Si BD tiene docs con prefijo diferente (PO-, PI-, HPT-) → ese ES el prefijo en uso → **NO CAMBIAR** (mantener consistencia)
- **REGLA:** Nunca cambiar prefijo si ya hay datos en producción con el prefijo actual. Solo corregir hacia adelante si historial vacío.

---

### T1 — Confirmar autoname='Prompt' en 5 doctypes (SIN CAMBIAR)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Verificar autoname=Prompt ACTUAL (estado correcto per 018) ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name as doctype,
  autoname,
  naming_rule,
  CASE WHEN autoname='"'"'Prompt'"'"' THEN '"'"'✅ PROMPT'"'"' ELSE '"'"'❌ NO PROMPT'"'"' END as estado
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

echo ""
echo "Expected: Todos = autoname='Prompt' (cambio hecho por 018 es OBLIGATORIO)"

'
```

**Crítico:** NO CAMBIAR autoname a 'hash' — agente 018 confirmó que sobrescribe Server Script.

---

### T2 — Verificar Server Scripts: código + prefijos correctos

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Leer Server Scripts before_insert (CDT-*-Seq) ===" 
cd /home/erpnext/frappe-bench

bench --site CDTALLERES console << '"'"'EOF'"'"'
scripts = frappe.get_list("Server Script",
    filters={"event": "before_insert", "disabled": 0},
    fields=["name", "doc_type", "script"]
)
for s in scripts:
    if any(dt in s.doc_type for dt in ["Purchase Order", "Purchase Invoice", "GL Entry", "Stock Ledger Entry", "Historial Pagos"]):
        print(f"\n=== {s.name} ({s.doc_type}) ===")
        print(s.script[:300])
EOF

'
```

**Verificar que scripts usen prefijos:**
- Purchase Order → `OC-` (no PO-)
- Purchase Invoice → `FC-` (no PI-)  
- GL Entry → `GLE-`
- Stock Ledger Entry → `SLE-`
- Historial Pagos txt → `HP-` (no HPT-)

**Si prefijos incorrectos → Corrección en T4b.**

---

### T3 — Verificar Client Scripts CDT-Hide-Newname

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Buscar Client Scripts CDT-Hide-Newname EN BD ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name,
  dt,
  disabled,
  CHAR_LENGTH(script) as script_size,
  modified
FROM tabClient_Script
WHERE name LIKE '"'"'CDT-Hide-Newname%'"'"'
ORDER BY dt;
" 2>&1

echo ""
echo "=== Conteo ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT COUNT(*) as count_scripts FROM tabClient_Script WHERE name LIKE '"'"'CDT-Hide-Newname%'"'"';
" 2>&1

'
```

**Esperado:** 
- 5 scripts: CDT-Hide-Newname-{PO, PI, GLE, SLE, HPT}
- Todos disabled=0 (activos)
- Si count=0 → fueron deletreados durante 018

---

### T4a — Restaurar Client Scripts CDT-Hide-Newname (SI count=0)

```bash
echo "=== Test navegador (verificar visibilidad __newname) ===" 
echo "URL: https://cdtalleres.shalom.com.pe"
echo ""
echo "Pasos:"
echo "1. Login: usuario@cdtalleres.local"
echo "2. Nuevo → Purchase Order"
echo "3. DevTools → Console"
echo "4. Ejecutar: document.querySelector('[data-fieldname=\"__newname\"]')"
echo "   - null = OCULTO ✅"
echo "   - HTMLElement = VISIBLE ❌"
echo "5. Si VISIBLE: significa Client Scripts no ejecutan"
```

---

### T4b — Verificar prefijos en Server Scripts (SOLO REPORTAR, NO CAMBIAR)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

cd /home/erpnext/frappe-bench

bench --site CDTALLERES console << '"'"'EOF'"'"'
# SOLO LEER — reportar prefijo que usa cada Server Script
scripts = frappe.get_list("Server Script",
    filters={"event": "before_insert", "disabled": 0},
    fields=["name", "doc_type", "script"]
)

print("=== Prefijos en Server Scripts vs Prefijos en BD ===")
for s in scripts:
    if any(dt in s.doc_type for dt in [
        "Purchase Order", "Purchase Invoice", "GL Entry", 
        "Stock Ledger Entry", "Historial Pagos"
    ]):
        # Detectar prefijo que genera el script
        import re
        prefijos = re.findall(r"['\"]([A-Z]{2,4}-)['\"]", s.script or "")
        print(f"  {s.doc_type}: {prefijos}")
EOF

'
```

**IMPORTANTE:** NO cambiar prefijos aquí. T0 ya mostró los prefijos reales en BD.
- Si Server Script prefijo == BD prefijo → ✅ consistente
- Si Server Script prefijo != BD prefijo → reportar discrepancia, esperar decisión explícita del usuario antes de cambiar

---

### T4c — Restaurar 5 Client Scripts (SI T3 mostró count=0)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

cd /home/erpnext/frappe-bench

bench --site CDTALLERES console << '"'"'EOF'"'"'
import json

# Template Client Script: hide __newname on form load/refresh
CLIENT_SCRIPT_TEMPLATE = {
    "doctype": "Client Script",
    "dt": "{DOCTYPE}",
    "script": """
frappe.ui.form.on('{DOCTYPE}', {{
    onload: function(frm) {{
        hide_newname_field(frm);
    }},
    refresh: function(frm) {{
        hide_newname_field(frm);
    }}
}});

function hide_newname_field(frm) {{
    if (frm.fields_dict['__newname']) {{
        frm.fields_dict['__newname'].$wrapper.hide();
    }}
    // Backup: hide via DOM si field object no existe
    const el = document.querySelector('[data-fieldname="__newname"]');
    if (el) {{
        el.style.display = 'none';
    }}
}}
""",
    "enabled": 1,
    "disabled": 0
}

DOCTYPES_TARGET = [
    ("Purchase Order", "CDT-Hide-Newname-PO"),
    ("Purchase Invoice", "CDT-Hide-Newname-PI"),
    ("GL Entry", "CDT-Hide-Newname-GLE"),
    ("Stock Ledger Entry", "CDT-Hide-Newname-SLE"),
    ("Historial Pagos txt", "CDT-Hide-Newname-HPT")
]

for doctype_name, script_name in DOCTYPES_TARGET:
    try:
        # Intenta obtener script existente
        script = frappe.get_doc("Client Script", script_name)
        script.disabled = 0
        script.save(ignore_permissions=True)
        print(f"✅ {script_name} RE-HABILITADO")
    except:
        # Script no existe → crear nuevo
        script_data = CLIENT_SCRIPT_TEMPLATE.copy()
        script_data["dt"] = doctype_name
        script_data["name"] = script_name
        script = frappe.get_doc(script_data)
        script.insert(ignore_permissions=True)
        print(f"✅ {script_name} CREADO (nuevo)")

frappe.db.commit()
print("")
print("✅ 5 Client Scripts restaurados/creados")

EOF

'
```

---

### T5 — Cache bust: forzar reload formularios (Nginx + Frappe)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Clear cache Frappe ===" 
cd /home/erpnext/frappe-bench
bench --site CDTALLERES clear-cache
bench --site CDTALLERES clear-website-cache

echo ""
echo "=== Reiniciar Frappe (gunicorn) ===" 
sudo systemctl restart frappe-bench

echo ""
echo "=== Esperar 5s ===" 
sleep 5

echo ""
echo "=== Verificar Gunicorn activo ===" 
sudo systemctl status frappe-bench | grep -i active

'
```

---

### T6 — Validar Client Scripts en 5 doctypes

```bash
echo "=== Test E2E navegador: 5 doctypes post-cache-bust ===" 
echo "URL: https://cdtalleres.shalom.com.pe"
echo ""
echo "IMPORTANTE: Abrir en navegador INCÓGNITO (localStorage limpio)"
echo ""
echo "Repetir para cada doctype:"
echo ""
echo "1. Purchase Order"
echo "   → Nuevo → Purchase Order"
echo "   → DevTools Console: document.querySelector('[data-fieldname=\"__newname\"]')"
echo "   → Esperado: null (OCULTO)"
echo ""
echo "2. Purchase Invoice"
echo "   → Mismo test"
echo ""
echo "3. GL Entry"
echo "   → Mismo test"
echo ""
echo "4. Stock Ledger Entry"
echo "   → Mismo test"
echo ""
echo "5. Historial Pagos txt"
echo "   → Mismo test"
echo ""
echo "✅ CRITERIO ÉXITO: Todos 5 = querySelector devuelve null"
echo "❌ CRITERIO FALLA: Alguno devuelve HTMLElement (visible)"
```

---

### T7 — Crear documento final: validar nombres secuenciales + sin __newname

```bash
echo "=== Crear 1 documento en cada doctype: validar nombre correcto ===" 
echo ""
echo "Desde navegador:"
echo "1. Purchase Order → nuevo → guardar"
echo "   Nombre esperado: OC-XXXXXX (secuencial, NOT hash, NOT PO-)"
echo ""
echo "2. Repetir para Invoice, GL Entry, SLE, HPT"
echo ""
echo "3. Verificar:"
echo "   - Formulario cargó sin errores"
echo "   - __newname NO visible"
echo "   - Nombre guardado = secuencial (no hash)"
```

---

## 📊 Reporte Obligatorio

Crear: `c:\jarcrow\Trabajo\CDTalleres\agentes\respuestas\2026-04-27_019_restore-client-scripts.md`

```markdown
# Restauración — Client Scripts CDT-Hide-Newname

## CONTEXTO (de Agente 018)
Agente 018 confirmó: **autoname='Prompt' es OBLIGATORIO para SEQUENCE funcionar**
- autoname='hash' → Server Script no puede asignar doc.name
- autoname='Prompt' → Server Script asigna nombres secuenciales
- **Requisito:** Mantener autoname='Prompt' en 5 doctypes

## T1: Verificar autoname='Prompt' activo
Todos 5 doctypes = autoname='Prompt': [SI/NO]
Cambio estado?: [NO CAMBIAR, es obligatorio]

## T2: Estado actual Client Scripts CDT-Hide-Newname
Scripts encontrados: [count de 5]
Status: [todos disabled=0 / algunos disabled=1 / count=0 deletreados]

## T3: Test navegador (__newname visible?)
document.querySelector('[data-fieldname="__newname"]') = [null/HTMLElement]
Interpretación: [OCULTO/VISIBLE]

## T4: Restaurar Client Scripts (si count=0)
Scripts creados: [count]

## T5: Cache bust
frappe clear-cache: ✅
Gunicorn restart: ✅
Status: [active]

## T6: Test 5 doctypes post-restore
| DocType | __newname Visible | Nombre Secuencial | Status |
|---------|--------|--------|---------|
| Purchase Order | [NO/SI] | OC-XXXXXX | [✅/❌] |
| Purchase Invoice | [NO/SI] | FC-XXXXXX | [✅/❌] |
| GL Entry | [NO/SI] | GLE-XXXXXX | [✅/❌] |
| Stock Ledger Entry | [NO/SI] | SLE-XXXXXX | [✅/❌] |
| Historial Pagos txt | [NO/SI] | HP-XXXXX | [✅/❌] |

## CONCLUSIÓN

✅ **RESTAURACIÓN EXITOSA:** [SI/NO]

Validaciones pasadas:
- [✅/❌] autoname='Prompt' en todos 5 doctypes
- [✅/❌] Client Scripts CDT-Hide-Newname activos
- [✅/❌] __newname NO visible en formularios
- [✅/❌] Nombres generados secuenciales (no hash)

**Estado final:** [LISTO PRODUCCIÓN / REQUIERE AJUSTES]

Si algún doctype aún muestra __newname → Crear prompt 020 (debug JS).
```

---

## ⚠️ INSTRUCCIONES CRÍTICAS

1. **T1:** Verificar si scripts existen + estado disabled
2. **T2:** Revisar JSONs por referencias (opcional, pero confirma metadata)
3. **T3:** Manual navegador — validar desde browser (verdad única)
4. **T4:** Restaurar SOLO si T1 mostró scripts deletreados o disabled=1
5. **T5:** Validar count=5 + disabled=0 en todos
6. **T6:** Cache bust obligatorio post-restore (formularios cachean metadata)
7. **T7-T8:** Test navegador en INCÓGNITO (localStorage limpio)
8. **Si T7 muestra aún visible después de todo:** Crear prompt 020 con debug JS avanzado (revisar script source, execution trace)

---

## 🎯 Resultado Esperado

**CASO A (Scripts existían, solo deshabilitados):**
```
T1: ❌ DISABLED
T4: RE-HABILITADOS
T5: ✅ disabled=0
T7: __newname OCULTO ✅
→ FIN
```

**CASO B (Scripts deletreados completamente):**
```
T1: ❌ NO ENCONTRADOS
T4: CREADOS (nuevos)
T5: ✅ count=5, disabled=0
T7: __newname OCULTO ✅
→ FIN
```

**CASO C (Scripts OK pero JS no ejecuta):**
```
T1: ✅ Existen, disabled=0
T5: ✅ count=5
T7: ❌ __newname AÚN VISIBLE
→ Crear prompt 020 (debug JS, revisar payload script, ejecutar manualmente en console)
```
