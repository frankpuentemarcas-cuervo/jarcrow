---
fecha: 2026-04-26
agente_id: "028"
descripcion: purgar-tabversion-27m-filas-doctype-historial-consulta
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\purga-tabversion-results.md"
dependencia: "CDT-TASK-027 ✅"
tarea_origen: CDT-TASK-028
---

# Purgar tabVersion — 27.7M filas + DocType historial consultable

## Contexto para el agente

Proyecto CDTalleres: ERPNext. El stress test final (prompt 027) reveló que `tabVersion` tiene **27.7 millones de registros**. Esta tabla almacena el historial de cambios (diff) de cada documento del sistema. Los INSERTs en ella estaban tomando **71 segundos** bajo carga, bloqueando los workers de Gunicorn.

**Problema crítico**: `tabVersion` no es solo historial técnico — los usuarios de CDTalleres usan la vista "Track Changes" en documentos para consultar qué cambios se hicieron. Si borramos directo, pierden esa funcionalidad para registros históricos.

**Solución**: 
1. Crear un **DocType personalizado** `CDT Historial Version` que funcione como archivo consultable desde el UI de ERPNext
2. Migrar los registros a purgar de `tabVersion` a ese DocType antes de borrarlos
3. Purgar `tabVersion` en lotes conservando solo los últimos 90 días
4. El DocType queda como bitácora permanente accesible desde ERPNext

### Estructura de tabVersion

```sql
-- tabVersion tiene estas columnas relevantes:
-- name (varchar PK)
-- creation (datetime)
-- modified (datetime)
-- owner (varchar)
-- ref_doctype (varchar) -- tipo de documento (ej: "Purchase Order")
-- docname (varchar)     -- nombre del documento (ej: "PUR-ORD-2024-00001")
-- data (longtext)       -- JSON con el diff de cambios
```

### Accesos

| Rol | IP Pública | IP Privada |
|---|---|---|
| Frontend | `209.38.75.235` | `10.124.0.10` |
| Backend | `164.92.94.47` | `10.124.0.9` |
| DB (MariaDB) | `165.232.130.222` | `10.124.0.7` |

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@[IP]
```

- DB name: `_0646d69b639ad0ff`
- Bench: `/home/erpnext/frappe-bench`
- Site: `cdtalleres-copia.shalom.com.pe`
- App custom CDTalleres: verificar con `ls /home/erpnext/frappe-bench/apps/`

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear `c:\dev\cdtalleres\purga-tabversion-results.md` y actualizar después de CADA tarea
2. Documentar resultado (✅/❌), filas afectadas, output completo
3. Si un paso falla → documentar → detener → notificar — NO continuar
4. Nunca terminar sin el archivo de salida

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

### T1 — Auditoría pre-purga

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Estructura tabVersion ==="
mysql -u root -p".Overskull2026.m" $DB -e "DESCRIBE tabVersion;" 2>/dev/null

echo "=== Conteo total ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT COUNT(*) AS total_filas FROM tabVersion;" 2>/dev/null

echo "=== Tamaño en MB ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name,
  ROUND((data_length + index_length)/1024/1024, 2) AS size_mb,
  table_rows AS estimated_rows
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name = '"'"'tabVersion'"'"';" 2>/dev/null

echo "=== Distribución por mes ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT DATE_FORMAT(creation, '"'"'%Y-%m'"'"') AS mes, COUNT(*) AS filas
FROM tabVersion
GROUP BY DATE_FORMAT(creation, '"'"'%Y-%m'"'"')
ORDER BY mes DESC
LIMIT 30;" 2>/dev/null

echo "=== Distribución por ref_doctype (top 15) ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT ref_doctype, COUNT(*) AS filas
FROM tabVersion
GROUP BY ref_doctype
ORDER BY filas DESC
LIMIT 15;" 2>/dev/null

echo "=== Cuántos registros > 90 días ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT COUNT(*) AS a_purgar
FROM tabVersion
WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY);" 2>/dev/null

echo "=== Registro más antiguo ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT MIN(creation) AS mas_antiguo, MAX(creation) AS mas_reciente
FROM tabVersion;" 2>/dev/null

echo "=== Apps instaladas en bench ==="
ls /home/erpnext/frappe-bench/apps/ 2>/dev/null || \
  sshpass -p '"'"'.Overskull2026.m'"'"' ssh -o StrictHostKeyChecking=no root@164.92.94.47 \
    "ls /home/erpnext/frappe-bench/apps/"
'
```

```bash
tg_notify "✅ *CDT 028 T1* — Auditoría tabVersion completada. Ver resultados antes de continuar."
```

---

### T2 — Crear DocType `CDT Historial Version`

El DocType almacena el historial archivado en un formato consultable desde ERPNext. Se crea vía bench console (Python) en el servidor frontend/backend donde está el bench.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
cd /home/erpnext/frappe-bench

echo "=== Verificar apps disponibles ==="
ls apps/

# Determinar app donde crear el DocType
# Si existe una app custom (ej: cdtalleres, customapp), usarla
# Si no, usar frappe directamente
APP_NAME=$(ls apps/ | grep -v "frappe\|erpnext\|hrms\|payments" | head -1)
echo "App custom detectada: $APP_NAME"
[ -z "$APP_NAME" ] && APP_NAME="frappe" && echo "Sin app custom — usando frappe"

echo "=== Crear DocType CDT Historial Version via bench console ==="
bench --site cdtalleres-copia.shalom.com.pe console << '"'"'PYEOF'"'"'
import frappe

# Verificar si ya existe
if frappe.db.exists("DocType", "CDT Historial Version"):
    print("DocType ya existe — verificando campos")
    dt = frappe.get_doc("DocType", "CDT Historial Version")
    print(f"Fields: {[f.fieldname for f in dt.fields]}")
else:
    print("Creando DocType CDT Historial Version...")
    
    dt = frappe.new_doc("DocType")
    dt.name = "CDT Historial Version"
    dt.module = "Custom"
    dt.custom = 1
    dt.is_submittable = 0
    dt.istable = 0
    dt.issingle = 0
    dt.track_changes = 0  # NO rastrear cambios de este mismo DocType
    dt.description = "Archivo histórico de versiones purgadas de tabVersion. Consulta de cambios en documentos."
    
    dt.fields = []
    
    # Campo: Tipo de Documento
    dt.append("fields", {
        "fieldname": "ref_doctype",
        "label": "Tipo de Documento",
        "fieldtype": "Data",
        "in_list_view": 1,
        "in_filter": 1,
        "search_index": 1,
        "reqd": 1,
        "read_only": 1
    })
    
    # Campo: Nombre del Documento
    dt.append("fields", {
        "fieldname": "docname",
        "label": "Documento",
        "fieldtype": "Data",
        "in_list_view": 1,
        "in_filter": 1,
        "search_index": 1,
        "reqd": 1,
        "read_only": 1
    })
    
    # Campo: Fecha de cambio
    dt.append("fields", {
        "fieldname": "fecha_version",
        "label": "Fecha de Cambio",
        "fieldtype": "Datetime",
        "in_list_view": 1,
        "in_filter": 1,
        "reqd": 1,
        "read_only": 1
    })
    
    # Campo: Modificado por
    dt.append("fields", {
        "fieldname": "modified_by_user",
        "label": "Modificado Por",
        "fieldtype": "Data",
        "in_list_view": 1,
        "in_filter": 1,
        "read_only": 1
    })
    
    # Campo: ID original en tabVersion
    dt.append("fields", {
        "fieldname": "version_id",
        "label": "ID Version Original",
        "fieldtype": "Data",
        "read_only": 1
    })
    
    # Campo: Datos del cambio (JSON diff)
    dt.append("fields", {
        "fieldname": "datos_cambio",
        "label": "Datos del Cambio",
        "fieldtype": "Long Text",
        "read_only": 1
    })
    
    dt.insert(ignore_permissions=True)
    frappe.db.commit()
    print("✅ DocType CDT Historial Version creado exitosamente")

frappe.destroy()
PYEOF
'
```

**Si bench console falla** (error de sitio), intentar con:
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
cd /home/erpnext/frappe-bench
# Listar sitios disponibles
ls sites/
bench --site [SITE_CORRECTO] console << '"'"'PYEOF'"'"'
print(frappe.get_list("DocType", filters={"name": "CDT Historial Version"}))
PYEOF
'
```

```bash
tg_notify "✅ *CDT 028 T2* — DocType CDT Historial Version creado."
```

---

### T3 — Migrar registros > 90 días de tabVersion al DocType

Insertar en `tabCDT Historial Version` (nombre tabla = `tab` + DocType name sin espacios → `tabCDT Historial Version`) los registros que se van a purgar.

**NOTA**: En Frappe los DocTypes con espacios generan tabla con el mismo nombre con espacios. Verificar nombre exacto de tabla antes de INSERT.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Verificar nombre exacto de la tabla del DocType ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SHOW TABLES LIKE '"'"'tabCDT%'"'"';" 2>/dev/null

# La tabla debería ser: tabCDT Historial Version
# Verificar que existe
TABLE_EXISTS=$(mysql -u root -p".Overskull2026.m" $DB -se "
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema='"'"'_0646d69b639ad0ff'"'"'
AND table_name='"'"'tabCDT Historial Version'"'"';" 2>/dev/null)
echo "Tabla existe: $TABLE_EXISTS (debe ser 1)"

if [ "$TABLE_EXISTS" = "1" ]; then
  echo "=== Conteo a migrar ==="
  A_MIGRAR=$(mysql -u root -p".Overskull2026.m" $DB -se "
    SELECT COUNT(*) FROM tabVersion
    WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY);" 2>/dev/null)
  echo "Registros a migrar: $A_MIGRAR"

  echo "=== Migración en lotes de 5000 ==="
  LOTE=5000
  ITER=0
  MIGRADOS=1
  while [ $MIGRADOS -gt 0 ]; do
    MIGRADOS=$(mysql -u root -p".Overskull2026.m" $DB -se "
INSERT INTO \`tabCDT Historial Version\`
  (name, creation, modified, owner, ref_doctype, docname,
   fecha_version, modified_by_user, version_id, datos_cambio)
SELECT
  UUID() AS name,
  NOW() AS creation,
  NOW() AS modified,
  '"'"'Administrator'"'"' AS owner,
  ref_doctype,
  docname,
  creation AS fecha_version,
  owner AS modified_by_user,
  name AS version_id,
  data AS datos_cambio
FROM tabVersion
WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY)
LIMIT ${LOTE};
SELECT ROW_COUNT();" 2>/dev/null | tail -1)
    MIGRADOS=${MIGRADOS:-0}
    ITER=$((ITER + 1))
    echo "Lote $ITER: $MIGRADOS insertados"
    [ $MIGRADOS -gt 0 ] && sleep 2
  done

  echo "=== Total migrado al DocType ==="
  mysql -u root -p".Overskull2026.m" $DB -e "
  SELECT COUNT(*) AS total_historial FROM \`tabCDT Historial Version\`;" 2>/dev/null
else
  echo "❌ Tabla no encontrada — verificar T2 antes de continuar"
fi
'
```

```bash
tg_notify "✅ *CDT 028 T3* — Migración a DocType completada."
```

---

### T4 — Purgar tabVersion en lotes (DELETE)

Solo purgar DESPUÉS de confirmar que la migración (T3) completó correctamente.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

# Verificar conteo DocType vs tabVersion a purgar
HISTORIAL=$(mysql -u root -p".Overskull2026.m" $DB -se "
  SELECT COUNT(*) FROM \`tabCDT Historial Version\`;" 2>/dev/null)
A_PURGAR=$(mysql -u root -p".Overskull2026.m" $DB -se "
  SELECT COUNT(*) FROM tabVersion
  WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY);" 2>/dev/null)

echo "Registros en DocType historial: $HISTORIAL"
echo "Registros a purgar en tabVersion: $A_PURGAR"

if [ "$HISTORIAL" -ge "$A_PURGAR" ]; then
  echo "✅ Migración verificada — procediendo con purga"
  
  LOTE=10000
  DELETED=1
  ITER=0
  while [ $DELETED -gt 0 ]; do
    DELETED=$(mysql -u root -p".Overskull2026.m" $DB -se "
DELETE FROM tabVersion
WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY)
LIMIT ${LOTE};
SELECT ROW_COUNT();" 2>/dev/null | tail -1)
    DELETED=${DELETED:-0}
    ITER=$((ITER + 1))
    RESTANTES=$(mysql -u root -p".Overskull2026.m" $DB -se "
      SELECT COUNT(*) FROM tabVersion
      WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY);" 2>/dev/null)
    echo "Lote $ITER: $DELETED borradas | restantes > 90d: ${RESTANTES:-?}"
    [ $DELETED -gt 0 ] && sleep 1
  done

  echo "=== Purga completada en $ITER lotes ==="
  echo "=== Total tabVersion actual ==="
  mysql -u root -p".Overskull2026.m" $DB -e "
  SELECT COUNT(*) AS total_actual FROM tabVersion;" 2>/dev/null
else
  echo "❌ ABORT — DocType tiene $HISTORIAL registros pero hay $A_PURGAR a purgar"
  echo "Diferencia: $((A_PURGAR - HISTORIAL)) registros sin migrar"
  echo "Re-ejecutar T3 antes de continuar"
fi
'
```

```bash
tg_notify "✅ *CDT 028 T4* — Purga tabVersion completada."
```

---

### T5 — OPTIMIZE TABLE para reclamar espacio

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Tamaño ANTES de OPTIMIZE ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name, ROUND((data_length + index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name IN ('"'"'tabVersion'"'"', '"'"'tabCDT Historial Version'"'"');" 2>/dev/null

echo "=== OPTIMIZE TABLE tabVersion (puede tardar varios minutos) ==="
mysql -u root -p".Overskull2026.m" $DB -e "OPTIMIZE TABLE tabVersion;" 2>/dev/null

echo "=== Tamaño DESPUÉS de OPTIMIZE ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name, ROUND((data_length + index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name IN ('"'"'tabVersion'"'"', '"'"'tabCDT Historial Version'"'"');" 2>/dev/null

echo "=== Top 10 tablas más grandes post-purga ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name, ROUND((data_length + index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
ORDER BY size_mb DESC LIMIT 10;" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 028 T5* — OPTIMIZE TABLE ejecutado."
```

---

### T6 — Configurar permisos del DocType y verificar UI

El DocType debe ser visible en ERPNext para que los usuarios puedan consultarlo.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
cd /home/erpnext/frappe-bench

bench --site cdtalleres-copia.shalom.com.pe console << '"'"'PYEOF'"'"'
import frappe

doctype_name = "CDT Historial Version"

# Agregar permisos para roles relevantes
roles_con_acceso = ["System Manager", "Accounts User", "Purchase User", "Stock User"]

dt = frappe.get_doc("DocType", doctype_name)

# Limpiar permisos existentes y re-asignar
dt.permissions = []

for role in roles_con_acceso:
    dt.append("permissions", {
        "role": role,
        "read": 1,
        "write": 0,
        "create": 0,
        "delete": 0,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "export": 1,
        "print": 1,
        "email": 0
    })

dt.save(ignore_permissions=True)
frappe.db.commit()
print(f"✅ Permisos configurados para: {roles_con_acceso}")

# Verificar conteo final
count = frappe.db.count(doctype_name)
print(f"Registros en {doctype_name}: {count}")

# Verificar acceso a uno de muestra
sample = frappe.get_list(
    doctype_name,
    fields=["name", "ref_doctype", "docname", "fecha_version", "modified_by_user"],
    limit=5,
    order_by="fecha_version desc"
)
print("Muestra de registros:")
for r in sample:
    print(f"  {r['ref_doctype']} | {r['docname']} | {r['fecha_version']} | {r['modified_by_user']}")

frappe.destroy()
PYEOF
'
```

Verificar en el UI:
1. Login en `https://cdtalleres-copia.shalom.com.pe` como Administrator
2. Buscar "CDT Historial Version" en la barra de búsqueda
3. Confirmar que aparece la lista con registros históricos
4. Probar filtros por `ref_doctype` y `docname`

```bash
tg_notify "✅ *CDT 028 T6* — Permisos DocType configurados. UI verificado."
```

---

### T7 — Verificar impacto en rendimiento

Confirmar que los INSERTs en `tabVersion` ya no son el cuello de botella.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Verificar tabVersion post-purga ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT
  COUNT(*) AS filas_restantes,
  MIN(creation) AS mas_antiguo,
  MAX(creation) AS mas_reciente
FROM tabVersion;" 2>/dev/null

echo "=== Test INSERT velocidad en tabVersion ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SET @start = NOW(6);
INSERT INTO tabVersion (name, creation, modified, owner, ref_doctype, docname, data)
VALUES (UUID(), NOW(), NOW(), '"'"'test'"'"', '"'"'Purchase Order'"'"', '"'"'TEST-PERF-001'"'"', '"'"'{}'"'"');
SET @end = NOW(6);
SELECT TIMESTAMPDIFF(MICROSECOND, @start, @end)/1000 AS insert_ms;
DELETE FROM tabVersion WHERE docname = '"'"'TEST-PERF-001'"'"';
" 2>/dev/null

echo "=== Comparación tamaños tabla ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name,
  ROUND((data_length + index_length)/1024/1024,2) AS size_mb,
  table_rows AS estimated_rows
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name IN ('"'"'tabVersion'"'"', '"'"'tabCDT Historial Version'"'"', '"'"'tabWorkflow Action'"'"')
ORDER BY size_mb DESC;" 2>/dev/null
'
```

```bash
tg_notify "🏁 *CDT 028 TERMINÓ* — tabVersion purgada + DocType activo\nVer: c:\\dev\\cdtalleres\\purga-tabversion-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\purga-tabversion-results.md
```

### Estructura obligatoria

```markdown
# Purga tabVersion + DocType CDTalleres — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T1. Auditoría pre-purga | ✅/❌ | filas: 27.7M, tamaño: XMB, más antigua: |
| T2. DocType CDT Historial Version creado | ✅/❌ | tabla: tabCDT Historial Version |
| T3. Migración > 90 días al DocType | ✅/❌ | registros migrados: X |
| T4. Purga tabVersion | ✅/❌ | lotes: X, borradas: X |
| T5. OPTIMIZE TABLE | ✅/❌ | antes: XMB → después: XMB |
| T6. Permisos UI configurados | ✅/❌ | roles: System Manager, Accounts User, ... |
| T7. Impacto rendimiento verificado | ✅/❌ | INSERT tabVersion: Xms (antes 71,000ms) |

## Resultados

| Métrica | Antes | Después |
|---|---|---|
| Filas tabVersion | 27,700,000 | X |
| Tamaño tabVersion | XMB | XMB |
| INSERT tabVersion (ms) | ~71,000ms | Xms |
| Registros archivados en DocType | 0 | X |

## DocType CDT Historial Version

- Acceso: ERPNext → buscar "CDT Historial Version"
- Roles con acceso: System Manager, Accounts User, Purchase User, Stock User
- Campos: Tipo Doc, Documento, Fecha Cambio, Modificado Por, Datos del Cambio
- Registros: X (historial de más de 90 días)

## Bloqueos y errores

[vacío si todo OK]
```
