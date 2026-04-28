---
fecha: 2026-04-25
agente_id: "015"
descripcion: auditar-tabseries-doctypes-con-mas-registros
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: completado
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\tabseries-audit-results.md"
dependencia: "014 (stress test completado — causa raíz: tabSeries lock contention)"
---

# Auditar tabSeries — DocTypes con más registros

## Contexto para el agente

Proyecto CDTalleres stress test diagnóstico. El stress test (prompt 014) identificó la causa raíz del colapso: **contención de bloqueos en `tabSeries`**.

ERPNext usa la tabla `tabSeries` para generar nombres de documentos (naming series). Cada INSERT a un DocType que usa naming series hace `SELECT ... FOR UPDATE` sobre una fila de `tabSeries`, serializando todas las escrituras concurrentes. Con 50+ usuarios esto colapsa el sistema (row_lock_time_avg subió de 0 → 14,740ms en el test).

**Objetivo de este prompt**: Identificar qué DocTypes tienen más registros en producción (mayor volumen histórico) para priorizar cuáles necesitan migrar de naming series numérica a Hash/UUID.

### Servidores

| Rol | IP | Credenciales |
|---|---|---|
| Frontend (ERPNext) | 209.38.75.235 | root / .Overskull2026.m |
| DB | 165.232.130.222 | root / .Overskull2026.m |

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Genera o actualiza el archivo de salida inmediatamente con lo ejecutado
2. Documenta CADA tarea: resultado (✅/❌), output exacto, error completo si falló
3. Nunca termines sin el archivo de salida. Aunque sea parcial.
4. Si una tarea falla, documentarla y continuar con la siguiente.

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

### 1. Top 30 series en tabSeries (por contador actual)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "
USE \`cdtalleres-copia\`;
SELECT
  name AS serie,
  current AS contador_actual
FROM tabSeries
ORDER BY current DESC
LIMIT 30;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 015 T1* — Top 30 tabSeries capturado"
```

---

### 2. Identificar a qué DocType pertenece cada serie

Para cada serie del top 30, encontrar su DocType. ERPNext nombra las series con prefijos que coinciden con la configuración del DocType.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "
USE \`cdtalleres-copia\`;

-- Cruzar series con DocTypes que las usan (campo autoname LIKE serie%)
SELECT
  ts.name AS serie,
  ts.current AS contador,
  dt.name AS doctype,
  dt.autoname AS naming_config
FROM tabSeries ts
LEFT JOIN \`tabDocType\` dt ON dt.autoname LIKE CONCAT(SUBSTRING_INDEX(ts.name, '.', 1), '%')
ORDER BY ts.current DESC
LIMIT 30;
" 2>/dev/null
'
```

**NOTA**: Si el JOIN no produce resultados útiles (naming config puede ser `naming_series` genérico), continuar con la tarea 3 para cruzar por conteo real de documentos.

---

### 3. Conteo real de documentos en tablas con más volumen

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "
USE \`cdtalleres-copia\`;

-- Tablas con más filas (excluyendo tablas de sistema y logs)
SELECT
  table_name,
  table_rows AS filas_estimadas,
  ROUND(data_length / 1024 / 1024, 2) AS size_mb
FROM information_schema.TABLES
WHERE table_schema = \"cdtalleres-copia\"
  AND table_name LIKE \"tab%\"
  AND table_name NOT IN (
    \"tabSingles\", \"tabDefaultValue\", \"tabSeries\", \"tabPatch Log\",
    \"tabVersion\", \"tabError Log\", \"tabActivity Log\", \"tabAccess Log\",
    \"tabFile\", \"tabComment\", \"tabCommunication\"
  )
ORDER BY table_rows DESC
LIMIT 40;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 015 T3* — Conteo de documentos por DocType capturado"
```

---

### 4. Verificar cuáles de los DocTypes top usan naming series (no hash/UUID)

Para cada DocType del top 20 por volumen, verificar si usa naming series numérica (vulnerable al lock) o ya usa Hash.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=cdtalleres-copia.shalom.com.pe

# Obtener top DocTypes por volumen y su configuración de naming
cd $BENCH
sudo -u erpnext bench --site $SITE execute frappe.db.sql --args '"'"'["
  SELECT
    dt.name AS doctype,
    dt.autoname AS naming_config,
    dt.module,
    (SELECT COUNT(*) FROM information_schema.tables
     WHERE table_schema = DATABASE()
     AND table_name = CONCAT(\"tab\", dt.name)) AS tabla_existe
  FROM \`tabDocType\` dt
  WHERE dt.autoname IS NOT NULL
    AND dt.autoname NOT IN (\"hash\", \"UUID\", \"prompt\", \"field:\")
    AND dt.autoname NOT LIKE \"field:%\"
    AND dt.autoname NOT LIKE \"expr:%\"
  ORDER BY dt.name
  LIMIT 50
", as_dict=1]'"'"' 2>&1 | python3 -c "
import json, sys
data = sys.stdin.read()
try:
    result = json.loads(data.split(None, 1)[-1] if data.strip().startswith(\"{\") else data)
    if isinstance(result, list):
        for row in result[:50]:
            print(f\"{row.get(\"doctype\",\"?\")} | naming: {row.get(\"naming_config\",\"?\")} | mod: {row.get(\"module\",\"?\")}\" )
    else:
        print(data[:2000])
except Exception as e:
    print(data[:2000])
" 2>/dev/null || echo "revisar manualmente"
'
```

---

### 5. Consulta directa MariaDB — DocTypes con naming series numérica y alto volumen

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "
USE \`cdtalleres-copia\`;

-- DocTypes con autoname tipo serie (contiene guión o punto = naming series)
-- cruzados con su volumen de registros
SELECT
  dt.name AS doctype,
  dt.autoname AS naming_config,
  ts.current AS series_counter,
  t.table_rows AS registros_estimados
FROM \`tabDocType\` dt
LEFT JOIN tabSeries ts ON ts.name LIKE CONCAT(SUBSTRING_INDEX(dt.autoname, '.', 1), '%')
LEFT JOIN information_schema.TABLES t
  ON t.table_schema = \"cdtalleres-copia\"
  AND t.table_name = CONCAT(\"tab\", dt.name)
WHERE dt.autoname REGEXP '[A-Z].*[.-]'
  AND dt.autoname NOT IN (\"hash\", \"UUID\")
  AND dt.autoname NOT LIKE \"field:%\"
  AND t.table_rows > 1000
ORDER BY t.table_rows DESC
LIMIT 40;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 015 T5* — DocTypes con naming series + alto volumen identificados"
```

---

### 6. Verificar DocTypes custom de Overskull — naming series

Los DocTypes custom (módulo Overskull o CDTalleres) son los más fáciles de modificar ya que son código propio.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "
USE \`cdtalleres-copia\`;

-- DocTypes custom (no de ERPNext core) con naming series
SELECT
  dt.name AS doctype,
  dt.module,
  dt.autoname AS naming_config,
  t.table_rows AS registros_estimados
FROM \`tabDocType\` dt
LEFT JOIN information_schema.TABLES t
  ON t.table_schema = \"cdtalleres-copia\"
  AND t.table_name = CONCAT(\"tab\", dt.name)
WHERE dt.custom = 1
   OR dt.module NOT IN (
     \"Accounts\", \"Stock\", \"Buying\", \"Selling\", \"Manufacturing\",
     \"Projects\", \"HR\", \"Payroll\", \"CRM\", \"Support\", \"Core\",
     \"Frappe\", \"Email\", \"Contacts\", \"Setup\", \"Regional\", \"Desk\"
   )
ORDER BY t.table_rows DESC
LIMIT 30;
" 2>/dev/null
'
```

Notificar:
```bash
tg_notify "✅ *CDT 015 T6* — DocTypes custom identificados"
```

---

### 7. Generar tabla de priorización

Con todos los datos recopilados, construir manualmente la tabla de priorización en el archivo de salida:

Criterios de prioridad para cambiar a Hash/UUID:
- **Alta**: DocType custom + volumen >10k + en top 10 tabSeries → cambio inmediato
- **Media**: DocType ERPNext core + volumen >10k → evaluar (puede requerir override)
- **Baja**: DocType con volumen <1k → sin urgencia

Notificar al terminar:
```bash
tg_notify "🏁 *CDT 015 TERMINÓ* — Auditoría tabSeries completa\nVer: c:\\dev\\cdtalleres\\tabseries-audit-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\tabseries-audit-results.md
```

### Estructura obligatoria

```markdown
# Auditoría tabSeries CDTalleres — YYYY-MM-DD HH:MM

## Top 30 series en tabSeries

| Serie | Contador actual |
|---|---|
| Orden-Trabajo- | 42921 |
| ACC-GLE-2025- | 149252 |
| ... | ... |

## Conteo real de documentos por DocType

| DocType (tabla) | Filas estimadas | Size MB |
|---|---|---|
| tabOrden de Trabajo 2 | N | N |
| ... | ... | ... |

## DocTypes con naming series numérica + alto volumen

| DocType | Naming config | Series counter | Registros estimados | Es custom | Módulo |
|---|---|---|---|---|---|
| Orden de Trabajo 2 | Orden-Trabajo-.#### | 42921 | N | Sí/No | [módulo] |
| ... | | | | | |

## DocTypes custom de Overskull/CDTalleres

| DocType | Módulo | Naming config | Registros |
|---|---|---|---|
| ... | ... | ... | ... |

## Tabla de priorización — migración a Hash/UUID

| Prioridad | DocType | Motivo | Acción recomendada |
|---|---|---|---|
| 🔴 Alta | Orden de Trabajo 2 | Custom + 42k+ registros + mayor lock en test | Cambiar autoname a "hash" en DocType |
| 🟡 Media | [DocType] | Core + alto volumen | Override naming en Custom Script |
| 🟢 Baja | [DocType] | Volumen bajo | Sin urgencia |

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
