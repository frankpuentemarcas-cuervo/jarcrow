---
fecha: 2026-04-25
agente_id: "017"
descripcion: documentar-sistema-completo-cdtalleres-desde-codigo
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\docs\\documentacion-cdtalleres.md"
dependencia: ""
---

# Documentación Completa del Sistema CDTalleres — Desde Código Fuente

## Contexto para el agente

Sistema ERPNext v13.9.2 / Frappe v13.9.1 para talleres — cliente CDTalleres / Shalom.

La documentación se genera **desde el código fuente de las apps y el sitio**, no por introspección de UI. Esto garantiza que se capturen todas las reglas de negocio, validaciones, hooks, y personalizaciones aunque no estén visibles en la interfaz.

### Rutas críticas

```
Bench:    /home/erpnext/frappe-bench
Apps:     /home/erpnext/frappe-bench/apps/
Site:     /home/erpnext/frappe-bench/sites/CDTALLERES/
```

### Apps instaladas

| App | Versión | Tipo |
|---|---|---|
| frappe | 13.9.1 | Core framework |
| erpnext | 13.9.2 | ERP core |
| notification | 0.0.1 | Custom (Overskull) |
| scanpda | 0.0.1 | Custom (Overskull) |

### Servidores

| Rol | IP | Credenciales |
|---|---|---|
| Frontend/App (bench + código) | 209.38.75.235 | root / .Overskull2026.m |
| DB (MariaDB) | 165.232.130.222 | root / .Overskull2026.m |

**NOTA**: Todo el código fuente de las apps está en el servidor Frontend (209.38.75.235). El servidor DB solo se usa para consultas de datos.

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear o actualizar `c:\dev\cdtalleres\docs\documentacion-cdtalleres.md` inmediatamente después de cada tarea
2. Documentar CADA tarea: resultado (✅/❌), output exacto, error completo si falló
3. Nunca terminar sin el archivo de salida. Aunque sea parcial.
4. Si una tarea falla, documentarla y continuar con la siguiente.
5. **SOLO LECTURA** — no modificar ningún archivo del servidor.

## 📲 Notificaciones Telegram — obligatorio después de CADA tarea

```bash
TBOT_TOKEN="8610126794:AAFcmZUxmq9swtkOMH7Ez-vbLFOvTelLFOs"
TBOT_CHAT="1412266627"
tg_notify() {
  curl -s -X POST "https://api.telegram.org/bot${TBOT_TOKEN}/sendMessage" \
    -d chat_id="${TBOT_CHAT}" \
    -d parse_mode="Markdown" \
    -d text="$1" > /dev/null
}
```

---

## Tareas a ejecutar

### 1. Estructura de apps custom — inventario inicial

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
APPS=/home/erpnext/frappe-bench/apps

echo "=== APPS INSTALADAS ==="
ls -la $APPS/

echo ""
echo "=== APP: notification — estructura ==="
find $APPS/notification -type f -name "*.py" -o -name "*.json" -o -name "*.js" | \
  grep -v "__pycache__" | grep -v ".pyc" | sort

echo ""
echo "=== APP: scanpda — estructura ==="
find $APPS/scanpda -type f -name "*.py" -o -name "*.json" -o -name "*.js" | \
  grep -v "__pycache__" | grep -v ".pyc" | sort
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T1* — Estructura de apps custom mapeada"
```

---

### 2. DocTypes custom — archivos JSON de definición

Los DocTypes en Frappe se definen en archivos `.json` dentro de cada app. Estos contienen TODOS los metadatos: campos, validaciones, permisos, workflows.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
APPS=/home/erpnext/frappe-bench/apps

echo "=== DOCTYPES JSON — app: notification ==="
find $APPS/notification -name "*.json" -path "*/doctype/*" | sort | while read f; do
  echo ""
  echo "--- FILE: $f ---"
  cat "$f"
done

echo ""
echo "=== DOCTYPES JSON — app: scanpda ==="
find $APPS/scanpda -name "*.json" -path "*/doctype/*" | sort | while read f; do
  echo ""
  echo "--- FILE: $f ---"
  cat "$f"
done
'
```

**IMPORTANTE**: Copiar el output COMPLETO de cada JSON al archivo de salida. Estos contienen la definición completa de campos, naming, permisos, y metadatos del DocType.

Notificar:
```bash
tg_notify "✅ *CDT 017 T2* — JSON de DocTypes custom extraídos"
```

---

### 3. Controllers Python — reglas de negocio server-side

Los controllers son los archivos `.py` que contienen hooks `validate`, `before_save`, `after_save`, `before_submit`, `on_submit`, `on_cancel`, etc. Aquí vive toda la lógica de negocio.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
APPS=/home/erpnext/frappe-bench/apps

echo "=== CONTROLLERS PYTHON — app: notification ==="
find $APPS/notification -name "*.py" -path "*/doctype/*" | \
  grep -v "__init__" | grep -v "test_" | sort | while read f; do
  echo ""
  echo "=========================================="
  echo "FILE: $f"
  echo "=========================================="
  cat "$f"
done

echo ""
echo "=== CONTROLLERS PYTHON — app: scanpda ==="
find $APPS/scanpda -name "*.py" -path "*/doctype/*" | \
  grep -v "__init__" | grep -v "test_" | sort | while read f; do
  echo ""
  echo "=========================================="
  echo "FILE: $f"
  echo "=========================================="
  cat "$f"
done
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T3* — Controllers Python (reglas de negocio) extraídos"
```

---

### 4. Client Scripts en código fuente — archivos JS por DocType

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
APPS=/home/erpnext/frappe-bench/apps

echo "=== CLIENT SCRIPTS JS — app: notification ==="
find $APPS/notification -name "*.js" -path "*/doctype/*" | sort | while read f; do
  echo ""
  echo "=========================================="
  echo "FILE: $f"
  echo "=========================================="
  cat "$f"
done

echo ""
echo "=== CLIENT SCRIPTS JS — app: scanpda ==="
find $APPS/scanpda -name "*.js" -path "*/doctype/*" | sort | while read f; do
  echo ""
  echo "=========================================="
  echo "FILE: $f"
  echo "=========================================="
  cat "$f"
done

echo ""
echo "=== ARCHIVOS JS RAÍZ (hooks globales) ==="
find $APPS/notification -name "*.js" -not -path "*/doctype/*" -not -path "*/node_modules/*" | sort | while read f; do
  echo "--- $f ---"; cat "$f"; echo ""
done
find $APPS/scanpda -name "*.js" -not -path "*/doctype/*" -not -path "*/node_modules/*" | sort | while read f; do
  echo "--- $f ---"; cat "$f"; echo ""
done
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T4* — Client Scripts JS extraídos"
```

---

### 5. hooks.py — todos los hooks registrados por las apps

`hooks.py` es el archivo central de cada app. Define qué funciones se ejecutan en cada evento del sistema (doc events, scheduled tasks, fixtures, etc.).

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
APPS=/home/erpnext/frappe-bench/apps

echo "=== hooks.py — app: notification ==="
cat $APPS/notification/notification/hooks.py 2>/dev/null || \
cat $APPS/notification/hooks.py 2>/dev/null || echo "hooks.py no encontrado"

echo ""
echo "=== hooks.py — app: scanpda ==="
cat $APPS/scanpda/scanpda/hooks.py 2>/dev/null || \
cat $APPS/scanpda/hooks.py 2>/dev/null || echo "hooks.py no encontrado"
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T5* — hooks.py de apps custom extraídos"
```

---

### 6. Fixtures del sitio — customizaciones exportadas

Las customizaciones aplicadas vía UI de ERPNext (Custom Fields, Property Setters, Client Scripts de DB, Server Scripts de DB, Workflows, Print Formats) se almacenan en el sitio como fixtures o directamente en MariaDB. Extraer desde ambas fuentes.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
SITE=/home/erpnext/frappe-bench/sites/CDTALLERES

echo "=== FIXTURES del sitio ==="
ls -la $SITE/ 2>/dev/null

echo ""
echo "=== site_config.json ==="
cat $SITE/site_config.json 2>/dev/null

echo ""
echo "=== Fixtures exportados (si existen) ==="
ls -la $SITE/fixtures/ 2>/dev/null || echo "No hay carpeta fixtures"
find $SITE -name "*.json" -not -path "*/private/*" -not -path "*/backups/*" | sort | while read f; do
  echo "--- $f ---"
  wc -l "$f"
done
'
```

```bash
# Extraer fixtures de apps (si están definidos en hooks.py fixtures = [...])
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
APPS=/home/erpnext/frappe-bench/apps

echo "=== Fixtures en apps ==="
for app in notification scanpda; do
  FIXTURES_DIR=$APPS/$app/$app/fixtures
  if [ -d "$FIXTURES_DIR" ]; then
    echo "--- App: $app --- fixtures encontrados ---"
    ls -la "$FIXTURES_DIR/"
    for f in "$FIXTURES_DIR"/*.json; do
      [ -f "$f" ] && echo "== $f ==" && cat "$f"
    done
  else
    echo "App $app: sin carpeta fixtures"
  fi
done
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T6* — Fixtures y site_config extraídos"
```

---

### 7. Custom Fields en DB — personalizaciones de DocTypes core

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench

sudo -u erpnext bench --site CDTALLERES execute frappe.db.sql --args '"'"'["
  SELECT
    cf.dt AS doctype,
    cf.fieldname,
    cf.label,
    cf.fieldtype,
    cf.reqd,
    cf.default,
    cf.options,
    cf.insert_after,
    cf.depends_on,
    cf.mandatory_depends_on,
    cf.read_only_depends_on,
    cf.description,
    cf.unique
  FROM \`tabCustom Field\` cf
  ORDER BY cf.dt, cf.label
", as_dict=1]'"'"' 2>&1 | python3 -c "
import json, sys
data = sys.stdin.read()
lines = data.strip().split(\"\n\")
start = next((i for i,l in enumerate(lines) if l.strip().startswith(\"[\")), None)
if start is not None:
    rows = json.loads(\"\n\".join(lines[start:]))
    cur_dt = None
    for r in rows:
        dt = r.get(\"doctype\",\"?\")
        if dt != cur_dt:
            print(f\"\n### Custom Fields en: {dt}\")
            print(\"| Fieldname | Label | Tipo | Req | Default | Options | Depends on |\")
            print(\"|---|---|---|---|---|---|---|\")
            cur_dt = dt
        print(f\"| {r.get(\"fieldname\",\"\")} | {r.get(\"label\",\"\")} | {r.get(\"fieldtype\",\"\")} | {'Sí' if r.get(\"reqd\") else ''} | {r.get(\"default\") or \"\"} | {str(r.get(\"options\") or \"\")[:50]} | {r.get(\"depends_on\") or \"\"} |\")
else:
    print(data[:3000])
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T7* — Custom Fields de DocTypes core extraídos"
```

---

### 8. Property Setters — cambios de propiedades en DocTypes core

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
sudo -u erpnext bench --site CDTALLERES execute frappe.db.sql --args '"'"'["
  SELECT
    ps.doc_type AS doctype,
    ps.field_name,
    ps.property,
    ps.value,
    ps.property_type
  FROM \`tabProperty Setter\` ps
  ORDER BY ps.doc_type, ps.field_name
", as_dict=1]'"'"' 2>&1 | python3 -c "
import json, sys
data = sys.stdin.read()
lines = data.strip().split(\"\n\")
start = next((i for i,l in enumerate(lines) if l.strip().startswith(\"[\")), None)
if start is not None:
    rows = json.loads(\"\n\".join(lines[start:]))
    print(\"| DocType | Campo | Propiedad | Valor |\")
    print(\"|---|---|---|---|\")
    for r in rows:
        val = str(r.get(\"value\") or \"\")[:80]
        print(f\"| {r.get(\"doctype\",\"\")} | {r.get(\"field_name\",\"\")} | {r.get(\"property\",\"\")} | {val} |\")
else:
    print(data[:2000])
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T8* — Property Setters documentados"
```

---

### 9. Workflows en DB — estados y transiciones completas

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT w.name, w.document_type, w.workflow_state_field, w.is_active
FROM tabWorkflow w WHERE w.is_active = 1;
" 2>/dev/null

mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT ws.parent AS workflow, ws.state, ws.doc_status, ws.allow_edit, ws.is_optional_state
FROM \`tabWorkflow Document State\` ws ORDER BY ws.parent, ws.idx;
" 2>/dev/null

mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT wt.parent AS workflow, wt.state AS desde, wt.action, wt.next_state AS hacia,
       wt.allowed AS rol, wt.allow_self_approval, wt.condition
FROM \`tabWorkflow Transition\` wt ORDER BY wt.parent, wt.idx;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T9* — Workflows extraídos"
```

---

### 10. Server Scripts y Client Scripts en DB (creados desde UI)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff

echo "=== SERVER SCRIPTS ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT ss.name, ss.reference_doctype, ss.doctype_event, ss.enabled, ss.script
FROM \`tabServer Script\` ss WHERE ss.enabled = 1 ORDER BY ss.reference_doctype;
" 2>/dev/null

echo ""
echo "=== CLIENT SCRIPTS (desde UI/DB) ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT cs.name, cs.dt AS doctype, cs.view, cs.enabled, cs.script
FROM \`tabClient Script\` cs WHERE cs.enabled = 1 ORDER BY cs.dt;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T10* — Server Scripts y Client Scripts en DB extraídos"
```

---

### 11. Print Formats custom — templates HTML/Jinja

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
APPS=/home/erpnext/frappe-bench/apps

echo "=== PRINT FORMATS en código (apps) ==="
find $APPS/notification $APPS/scanpda -name "*.html" -o -name "*.jinja" 2>/dev/null | sort | while read f; do
  echo "=========================================="
  echo "FILE: $f"
  echo "=========================================="
  cat "$f"
done

echo ""
echo "=== PRINT FORMATS JSON en apps ==="
find $APPS/notification $APPS/scanpda -name "*.json" -path "*/print_format/*" 2>/dev/null | sort | while read f; do
  echo "--- $f ---"; cat "$f"; echo ""
done
'
```

```bash
# Print Formats custom en DB (creados desde UI)
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT pf.name, pf.doc_type, pf.default_print_format, pf.print_format_type,
       CHAR_LENGTH(pf.html) AS html_len, LEFT(pf.html, 1000) AS html_preview
FROM \`tabPrint Format\` pf
WHERE pf.custom_format = 1
ORDER BY pf.doc_type;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T11* — Print Formats extraídos"
```

---

### 12. Scheduled Tasks — en hooks.py y en DB

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
APPS=/home/erpnext/frappe-bench/apps

echo "=== SCHEDULED TASKS en hooks.py (notification) ==="
grep -A 50 "scheduler_events" $APPS/notification/notification/hooks.py 2>/dev/null || echo "sin scheduler_events"

echo ""
echo "=== SCHEDULED TASKS en hooks.py (scanpda) ==="
grep -A 50 "scheduler_events" $APPS/scanpda/scanpda/hooks.py 2>/dev/null || echo "sin scheduler_events"

echo ""
echo "=== Funciones de scheduled tasks — código completo ==="
grep -r "def.*daily\|def.*weekly\|def.*hourly\|def.*monthly\|@frappe.whitelist" \
  $APPS/notification $APPS/scanpda 2>/dev/null | grep -v ".pyc"
'
```

```bash
# Scheduled Jobs en DB
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT sj.name, sj.method, sj.frequency, sj.cron_format, sj.stopped
FROM \`tabScheduled Job Type\` sj
WHERE sj.stopped = 0
ORDER BY sj.frequency;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T12* — Scheduled Tasks documentadas"
```

---

### 13. APIs expuestas — métodos @whitelist

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
APPS=/home/erpnext/frappe-bench/apps

echo "=== MÉTODOS WHITELIST (APIs) — notification ==="
grep -rn "@frappe.whitelist\|frappe.whitelist()" $APPS/notification --include="*.py" | \
  grep -v ".pyc" | grep -v "__pycache__"

echo ""
echo "=== Código de cada API — notification ==="
grep -rl "@frappe.whitelist" $APPS/notification --include="*.py" 2>/dev/null | while read f; do
  echo "=========================================="
  echo "FILE: $f"
  echo "=========================================="
  cat "$f"
done

echo ""
echo "=== MÉTODOS WHITELIST (APIs) — scanpda ==="
grep -rn "@frappe.whitelist\|frappe.whitelist()" $APPS/scanpda --include="*.py" | \
  grep -v ".pyc" | grep -v "__pycache__"

echo ""
echo "=== Código de cada API — scanpda ==="
grep -rl "@frappe.whitelist" $APPS/scanpda --include="*.py" 2>/dev/null | while read f; do
  echo "=========================================="
  echo "FILE: $f"
  echo "=========================================="
  cat "$f"
done
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T13* — APIs whitelist documentadas"
```

---

### 14. Roles, permisos y usuarios del sistema

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff

echo "=== ROLES CUSTOM ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT name, desk_access, home_page
FROM tabRole
WHERE name NOT IN (
  \"Administrator\",\"Guest\",\"System Manager\",\"All\",
  \"Accounts Manager\",\"Accounts User\",\"Purchase Manager\",
  \"Purchase User\",\"Sales Manager\",\"Sales User\",
  \"Stock Manager\",\"Stock User\",\"HR Manager\",\"HR User\",
  \"Projects Manager\",\"Projects User\",\"Manufacturing Manager\",
  \"Manufacturing User\",\"Item Manager\",\"Auditor\",
  \"Report Manager\",\"Dashboard Manager\",\"Blogger\",
  \"Website Manager\",\"Inbox User\",\"Expense Approver\",
  \"Leave Approver\",\"Support Team\",\"Desk User\"
)
ORDER BY name;
" 2>/dev/null

echo ""
echo "=== PERMISOS de DocTypes custom ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT dp.parent AS doctype, dp.role, dp.permlevel,
       dp.read, dp.write, dp.create, dp.delete,
       dp.submit, dp.cancel, dp.amend, dp.report, dp.export
FROM \`tabDocPerm\` dp
INNER JOIN \`tabDocType\` dt ON dt.name = dp.parent AND dt.custom = 1
ORDER BY dp.parent, dp.role;
" 2>/dev/null

echo ""
echo "=== USUARIOS ACTIVOS (no Administrator/Guest) ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT u.name, u.full_name, u.email, u.enabled,
       GROUP_CONCAT(ur.role SEPARATOR ', ') AS roles
FROM tabUser u
LEFT JOIN \`tabHas Role\` ur ON ur.parent = u.name
WHERE u.name NOT IN (\"Administrator\",\"Guest\")
  AND u.enabled = 1
GROUP BY u.name
ORDER BY u.name;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T14* — Roles, permisos y usuarios documentados"
```

---

### 15. Naming Series — mapa completo

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff

mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT
  ts.name AS serie,
  ts.current AS contador,
  t.table_rows AS registros_estimados
FROM tabSeries ts
LEFT JOIN information_schema.TABLES t
  ON t.table_schema = \"$DB\"
  AND t.table_name = REPLACE(CONCAT(\"tab\", REGEXP_REPLACE(ts.name, \"[-.].*\", \"\")), \"tab\", \"tab\")
ORDER BY ts.current DESC
LIMIT 50;
" 2>/dev/null

# Cruzar con autoname de DocTypes
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT name AS doctype, autoname AS naming_config, custom, module
FROM \`tabDocType\`
WHERE autoname IS NOT NULL
  AND autoname NOT IN (\"hash\",\"UUID\",\"prompt\",\"\")
  AND autoname NOT LIKE \"field:%\"
  AND autoname NOT LIKE \"expr:%\"
ORDER BY custom DESC, module;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T15* — Naming Series documentadas"
```

---

### 16. Webhooks, Email Templates y Notification Rules en DB

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff

echo "=== WEBHOOKS ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT name, webhook_doctype, webhook_docevent, request_url, enabled
FROM tabWebhook ORDER BY webhook_doctype;
" 2>/dev/null

echo ""
echo "=== NOTIFICATION RULES ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT name, document_type, event, condition, subject, enabled
FROM tabNotification WHERE enabled = 1 ORDER BY document_type;
" 2>/dev/null

echo ""
echo "=== EMAIL TEMPLATES ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT name, subject, CHAR_LENGTH(response) AS len
FROM \`tabEmail Template\` ORDER BY name;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T16* — Webhooks y notificaciones documentados"
```

---

### 17. Configuración del sitio y settings clave

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
SITE=/home/erpnext/frappe-bench/sites/CDTALLERES

echo "=== site_config.json ==="
cat $SITE/site_config.json

echo ""
echo "=== common_site_config.json ==="
cat /home/erpnext/frappe-bench/sites/common_site_config.json 2>/dev/null || echo "no existe"
'

sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff

echo "=== SYSTEM SETTINGS ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT field, value FROM tabSingles WHERE doctype = \"System Settings\"
  AND value IS NOT NULL AND value != \"\" AND value != \"0\"
ORDER BY field;" 2>/dev/null

echo ""
echo "=== ACCOUNTS SETTINGS ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT field, value FROM tabSingles WHERE doctype = \"Accounts Settings\"
  AND value IS NOT NULL AND value != \"\"
ORDER BY field;" 2>/dev/null

echo ""
echo "=== STOCK SETTINGS ==="
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT field, value FROM tabSingles WHERE doctype = \"Stock Settings\"
  AND value IS NOT NULL AND value != \"\"
ORDER BY field;" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 017 T17* — Configuración del sitio documentada"
```

---

### 18. Consolidar y generar documento final

Con el output de T1-T17, construir el documento completo en `c:\dev\cdtalleres\docs\documentacion-cdtalleres.md`.

Notificar al terminar:
```bash
tg_notify "🏁 *CDT 017 TERMINÓ* — Documentación completa CDTalleres desde código fuente\nVer: c:\\dev\\cdtalleres\\docs\\documentacion-cdtalleres.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\docs\documentacion-cdtalleres.md
```

### Estructura obligatoria del documento final

```markdown
# Documentación del Sistema CDTalleres
> Generado: YYYY-MM-DD | Site: CDTALLERES | ERPNext 13.9.2 / Frappe 13.9.1

---

## 1. Resumen ejecutivo del sistema

- Stack: ERPNext 13.9.2, Frappe 13.9.1, MariaDB 10.4.21
- Sitio: CDTALLERES
- Bench: /home/erpnext/frappe-bench
- Apps custom: notification v0.0.1, scanpda v0.0.1
- DocTypes custom: N
- Custom Fields en DocTypes core: N
- Workflows activos: N
- Server Scripts en código: N | en DB: N
- Client Scripts en código: N | en DB: N
- APIs whitelist: N endpoints
- Scheduled Tasks: N

---

## 2. Apps Custom

### 2.1 App: notification

**Ruta**: /home/erpnext/frappe-bench/apps/notification/
**Versión**: 0.0.1
**Propósito**: [descripción inferida del código]

#### hooks.py — eventos registrados

[tabla de doc_events, scheduler_events, fixtures]

### 2.2 App: scanpda

**Ruta**: /home/erpnext/frappe-bench/apps/scanpda/
**Versión**: 0.0.1
**Propósito**: [descripción inferida del código]

---

## 3. DocTypes Custom

### 3.1 [Nombre DocType] — app: [notification|scanpda]

**Archivo**: apps/[app]/[app]/[modulo]/doctype/[nombre]/[nombre].json
**Naming**: [autoname config]
**Submittable**: Sí/No
**Is Table** (child): Sí/No

#### Campos

| Fieldname | Label | Tipo | Req | Default | Options | Depends on |
|---|---|---|---|---|---|---|
| ... | | | | | | |

#### Reglas de negocio — Controller Python

**Archivo**: apps/[app]/...controller.py

```python
# código completo del controller
```

**Hooks implementados**:
- `validate`: [descripción de qué valida]
- `before_save`: [descripción]
- `after_submit`: [descripción]

#### Client Script — JS

```javascript
// código completo
```

**Eventos manejados**:
- `frm.add_custom_button(...)`: [descripción]
- `frm.fields_dict[...].df.options`: [descripción]

---

## 4. Personalizaciones de DocTypes Core (Custom Fields)

### [DocType core — ej: Purchase Order]

| Fieldname | Label | Tipo | Req | Insert after | Depends on | Descripción |
|---|---|---|---|---|---|---|
| ... | | | | | | |

---

## 5. Property Setters

| DocType | Campo | Propiedad modificada | Valor |
|---|---|---|---|
| ... | | | |

---

## 6. Workflows

### [Nombre Workflow] → DocType: [nombre]

**Campo de estado**: [field]

#### Diagrama de estados

```
[Borrador] --Aprobar (Rol X)--> [Aprobado] --Rechazar (Rol Y)--> [Rechazado]
                                     |
                               Enviar (Rol Z)
                                     |
                               [Enviado]
```

#### Estados

| Estado | Doc Status | Puede editar |
|---|---|---|
| | | |

#### Transiciones

| Desde | Acción | Hacia | Rol | Condición |
|---|---|---|---|---|
| | | | | |

---

## 7. Server Scripts (en código y en DB)

### 7.1 Desde código fuente (apps)

[código completo de cada función hook en los controllers]

### 7.2 Desde DB (creados en UI)

| Nombre | DocType | Evento | Habilitado |
|---|---|---|---|
| | | | |

```python
# Script completo
```

---

## 8. Client Scripts (en código y en DB)

### 8.1 Desde código fuente (apps)

```javascript
// código completo por DocType
```

### 8.2 Desde DB (creados en UI)

| Nombre | DocType | Vista | Habilitado |
|---|---|---|---|
| | | | |

```javascript
// Script completo
```

---

## 9. APIs Expuestas (@whitelist)

| Método | Archivo | Autenticación | Descripción |
|---|---|---|---|
| [app].[modulo].[función] | apps/... | Sí/allow_guest | [qué hace] |

```python
# código completo de cada API
```

---

## 10. Scheduled Tasks

| Función | Frecuencia | App | Descripción |
|---|---|---|---|
| [app.modulo.funcion] | daily/weekly/cron | notification | [qué hace] |

---

## 11. Print Formats Custom

| Nombre | DocType | Por defecto | Tipo |
|---|---|---|---|
| | | | |

```html
<!-- template completo o preview -->
```

---

## 12. Roles y Permisos

### Roles custom

| Rol | Acceso Desk | Home Page |
|---|---|---|
| | | |

### Permisos por DocType custom

| DocType | Rol | Leer | Escribir | Crear | Eliminar | Enviar | Cancelar |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

### Usuarios activos

| Usuario | Email | Roles |
|---|---|---|
| | | |

---

## 13. Naming Series

| Serie | Contador | DocType | Naming config | Custom | Módulo |
|---|---|---|---|---|---|
| Orden-Trabajo- | 42921 | Orden de Trabajo 2 | Orden-Trabajo-.#### | Sí | [mod] |

**Candidatos a migrar a Hash** (alto volumen + custom):
- [lista]

---

## 14. Webhooks y Notificaciones

| Nombre | DocType | Evento | URL/Destino | Condición |
|---|---|---|---|---|
| | | | | |

---

## 15. Configuración del Sitio

### site_config.json

```json
{ ... }
```

### Settings críticos del sistema

| Setting | Valor |
|---|---|
| | |

---

## 16. Notas técnicas y hallazgos

[Observaciones del agente sobre:
- Código con riesgo de error
- Configuraciones inusuales
- Dependencias entre apps
- Inconsistencias detectadas
- Patrones repetidos que sugieren refactoring]

## Bloqueos y errores de ejecución
[OBLIGATORIO — vacío si todo fue bien]
```
