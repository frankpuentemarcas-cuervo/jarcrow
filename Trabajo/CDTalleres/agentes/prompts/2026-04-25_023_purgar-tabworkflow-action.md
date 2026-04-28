---
fecha: 2026-04-25
agente_id: "023"
descripcion: purgar-tabworkflow-action-2790000-filas
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\purga-workflow-results.md"
dependencia: "ninguna — independiente de red privada"
tarea_origen: CDT-TASK-023
---

# Purgar tabWorkflow Action — 2.79M filas / 480MB

## Contexto para el agente

Proyecto CDTalleres: La tabla `` `tabWorkflow Action` `` en MariaDB tiene 2,790,159 filas acumuladas (~480MB). Es historial de acciones de workflow que nunca se limpia automáticamente. No afecta la funcionalidad actual pero degrada:
- Backups (480MB extra en cada dump)
- Queries que hacen JOIN con esta tabla
- Tamaño total de la DB

**Objetivo**: Purgar registros antiguos (> 90 días) en lotes seguros. Conservar los últimos 90 días.

### Accesos

- DB: `165.232.130.222` — usuario `root` password `.Overskull2026.m`
- DB name: `_0646d69b639ad0ff`

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222
```

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear `c:\dev\cdtalleres\purga-workflow-results.md` y actualizar después de CADA tarea
2. Documentar resultado (✅/❌), filas afectadas, errores completos
3. Si un paso falla → documentar → detener purga → notificar
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

### T1 — Auditoría antes de purgar

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Estructura de la tabla ==="
mysql -u root -p".Overskull2026.m" $DB -e "DESCRIBE \`tabWorkflow Action\`;" 2>/dev/null

echo "=== Conteo total ==="
mysql -u root -p".Overskull2026.m" $DB -e "SELECT COUNT(*) AS total_filas FROM \`tabWorkflow Action\`;" 2>/dev/null

echo "=== Tamaño en MB ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT
  table_name,
  ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb,
  table_rows AS estimated_rows
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name = '"'"'tabWorkflow Action'"'"';" 2>/dev/null

echo "=== Distribución por fecha (columna creation) ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT
  DATE_FORMAT(creation, '"'"'%Y-%m'"'"') AS mes,
  COUNT(*) AS filas
FROM \`tabWorkflow Action\`
GROUP BY DATE_FORMAT(creation, '"'"'%Y-%m'"'"')
ORDER BY mes DESC
LIMIT 24;" 2>/dev/null

echo "=== Columnas con fechas disponibles ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name = '"'"'tabWorkflow Action'"'"'
  AND data_type IN ('"'"'datetime'"'"','"'"'date'"'"','"'"'timestamp'"'"');" 2>/dev/null

echo "=== Registros más antiguos ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT creation, name, workflow_state
FROM \`tabWorkflow Action\`
ORDER BY creation ASC
LIMIT 5;" 2>/dev/null

echo "=== Registros más recientes ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT creation, name, workflow_state
FROM \`tabWorkflow Action\`
ORDER BY creation DESC
LIMIT 5;" 2>/dev/null

echo "=== Cuántos registros tienen más de 90 días ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT COUNT(*) AS a_purgar
FROM \`tabWorkflow Action\`
WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY);" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 023 T1* — Auditoría tabWorkflow Action completada"
```

---

### T2 — Crear tabla de backup (registros > 90 días)

Antes de borrar, guardar copia de seguridad de los registros que se van a eliminar.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"
BACKUP_TABLE="tabWorkflow_Action_backup_20260425"

echo "=== Crear tabla backup ==="
mysql -u root -p".Overskull2026.m" $DB -e "
CREATE TABLE IF NOT EXISTS \`${BACKUP_TABLE}\`
SELECT * FROM \`tabWorkflow Action\`
WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY);" 2>&1

echo "=== Verificar backup ==="
mysql -u root -p".Overskull2026.m" $DB -e "SELECT COUNT(*) AS filas_backup FROM \`${BACKUP_TABLE}\`;" 2>/dev/null

echo "=== Tamaño backup ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT
  table_name,
  ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name = '"'"'${BACKUP_TABLE//\`/}'"'"';" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 023 T2* — Tabla backup creada: tabWorkflow_Action_backup_20260425"
```

---

### T3 — Purgar en lotes (DELETE por LIMIT 10000)

Borrar en lotes de 10,000 filas con pausa de 1 segundo entre lotes para no saturar DB.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"
LOTE=10000
TOTAL_ANTES=$(mysql -u root -p".Overskull2026.m" $DB -se "SELECT COUNT(*) FROM \`tabWorkflow Action\` WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY);" 2>/dev/null)
echo "Filas a purgar: $TOTAL_ANTES"
echo "Lote: $LOTE filas"
echo "Lotes estimados: $(( (TOTAL_ANTES + LOTE - 1) / LOTE ))"
echo "Iniciando purga..."

DELETED=1
ITERATIONS=0
while [ $DELETED -gt 0 ]; do
  DELETED=$(mysql -u root -p".Overskull2026.m" $DB -se "
DELETE FROM \`tabWorkflow Action\`
WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY)
LIMIT ${LOTE}; SELECT ROW_COUNT();" 2>/dev/null | tail -1)
  DELETED=${DELETED:-0}
  ITERATIONS=$((ITERATIONS + 1))
  RESTANTES=$(mysql -u root -p".Overskull2026.m" $DB -se "SELECT COUNT(*) FROM \`tabWorkflow Action\` WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY);" 2>/dev/null)
  echo "Lote $ITERATIONS: $DELETED borradas | restantes > 90d: ${RESTANTES:-?}"
  [ $DELETED -gt 0 ] && sleep 1
done

echo "=== Purga completada en $ITERATIONS lotes ==="
echo "=== Total actual ==="
mysql -u root -p".Overskull2026.m" $DB -e "SELECT COUNT(*) AS total_actual FROM \`tabWorkflow Action\`;" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 023 T3* — Purga por lotes completada"
```

---

### T4 — OPTIMIZE TABLE para reclamar espacio en disco

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Tamaño ANTES de OPTIMIZE ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name, ROUND((data_length + index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name = '"'"'tabWorkflow Action'"'"';" 2>/dev/null

echo "=== Ejecutando OPTIMIZE TABLE (puede tardar varios minutos) ==="
mysql -u root -p".Overskull2026.m" $DB -e "OPTIMIZE TABLE \`tabWorkflow Action\`;" 2>/dev/null

echo "=== Tamaño DESPUÉS de OPTIMIZE ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name, ROUND((data_length + index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name = '"'"'tabWorkflow Action'"'"';" 2>/dev/null

echo "=== Tamaño total DB antes/después ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT
  ROUND(SUM(data_length + index_length)/1024/1024,2) AS total_db_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"';" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 023 T4* — OPTIMIZE TABLE ejecutado"
```

---

### T5 — Verificar resultado final

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Estado final tabWorkflow Action ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT
  COUNT(*) AS filas_restantes,
  MIN(creation) AS registro_mas_antiguo,
  MAX(creation) AS registro_mas_reciente
FROM \`tabWorkflow Action\`;" 2>/dev/null

echo "=== Top 10 tablas más grandes en DB ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name, ROUND((data_length + index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
ORDER BY size_mb DESC
LIMIT 10;" 2>/dev/null

echo "=== Tabla backup existe ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT table_name, ROUND((data_length + index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name LIKE '"'"'tabWorkflow_Action_backup%'"'"';" 2>/dev/null
'
```

```bash
tg_notify "🏁 *CDT 023 TERMINÓ* — tabWorkflow Action purgada\nVer: c:\\dev\\cdtalleres\\purga-workflow-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\purga-workflow-results.md
```

### Estructura obligatoria

```markdown
# Purga tabWorkflow Action CDTalleres — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T1. Auditoría pre-purga | ✅/❌ | filas: 2.79M, tamaño: 480MB, más antigua: |
| T2. Backup creado | ✅/❌ | tabla: tabWorkflow_Action_backup_20260425, filas: |
| T3. Purga por lotes | ✅/❌ | lotes ejecutados: X, filas borradas: X |
| T4. OPTIMIZE TABLE | ✅/❌ | tamaño antes: Xmb, después: Xmb |
| T5. Verificación final | ✅/❌ | filas restantes: X |

## Resultados

| Métrica | Antes | Después |
|---|---|---|
| Filas tabWorkflow Action | 2,790,159 | X |
| Tamaño tabla | ~480MB | X MB |
| Registro más antiguo | X | X (90 días atrás) |

## Tabla backup

- Nombre: `tabWorkflow_Action_backup_20260425`
- Filas guardadas: X
- Acción: mantener 30 días, luego DROP

## Bloqueos y errores

[vacío si todo OK]
```
