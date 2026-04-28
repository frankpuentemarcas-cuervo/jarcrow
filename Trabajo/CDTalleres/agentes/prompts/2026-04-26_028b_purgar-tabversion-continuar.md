---
fecha: 2026-04-26
agente_id: "028b"
descripcion: purgar-tabversion-continuar-desde-t3
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\purga-tabversion-results.md"
dependencia: "028 T1✅ T2✅ T6✅"
tarea_origen: CDT-TASK-028
---

# Purgar tabVersion — Continuar desde T3 (estrategia revisada)

## Contexto para el agente

Continuación del prompt 028. T1, T2 y T6 ya completadas:
- `tabVersion`: 27,770,713 filas / **7.3 GB**
- DocType `CDT Historial Version` ya creado con permisos
- Filas con más de 30 días: ~22.2M (se usa 30 días en este prompt, no 90)

**Estrategia revisada**:
- La data histórica de `tabVersion` existe en los otros 2 servidores (producción y backup) — no se pierde
- **Objetivo inmediato**: purgar `tabVersion` con registros > 30 días para recuperar rendimiento AHORA
- **Migración al DocType**: tarea posterior separada, tomará los datos de los otros servidores cuando sea necesario
- **NO hacer INSERT masivo al DocType en este prompt** — solo DELETE + OPTIMIZE

### Accesos

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222
```

- DB: `165.232.130.222`
- DB name: `_0646d69b639ad0ff`
- Frontend: `209.38.75.235`
- Backend/bench: `164.92.94.47`
- Site: `cdtalleres-copia.shalom.com.pe`

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Actualizar `c:\dev\cdtalleres\purga-tabversion-results.md` después de CADA tarea
2. Documentar resultado (✅/❌), filas afectadas, output completo
3. Si un paso falla → documentar → detener → notificar — NO continuar
4. Nunca terminar sin el archivo de salida actualizado

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

### T3 — Purgar tabVersion > 30 días en lotes

Eliminar directamente sin migración previa. Los datos históricos están seguros en los otros servidores.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Estado actual tabVersion ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT COUNT(*) AS total,
  SUM(CASE WHEN creation < DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) AS a_purgar,
  SUM(CASE WHEN creation >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) AS a_conservar
FROM tabVersion;" 2>/dev/null

echo "=== Iniciando purga lotes 10000 (> 30 días) ==="
LOTE=10000
DELETED=1
ITER=0
while [ $DELETED -gt 0 ]; do
  DELETED=$(mysql -u root -p".Overskull2026.m" $DB -se "
DELETE FROM tabVersion
WHERE creation < DATE_SUB(NOW(), INTERVAL 30 DAY)
LIMIT ${LOTE};
SELECT ROW_COUNT();" 2>/dev/null | tail -1)
  DELETED=${DELETED:-0}
  ITER=$((ITER + 1))
  RESTANTES=$(mysql -u root -p".Overskull2026.m" $DB -se "
    SELECT COUNT(*) FROM tabVersion
    WHERE creation < DATE_SUB(NOW(), INTERVAL 30 DAY);" 2>/dev/null)
  echo "Lote $ITER: $DELETED borradas | restantes > 30d: ${RESTANTES:-?}"
  [ $DELETED -gt 0 ] && sleep 1
done

echo "=== Purga completada en $ITER lotes ==="
echo "=== Total tabVersion actual ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT COUNT(*) AS filas_restantes,
  MIN(creation) AS mas_antiguo,
  MAX(creation) AS mas_reciente
FROM tabVersion;" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 028b T3* — Purga tabVersion > 30 días completada."
```

---

### T4 — OPTIMIZE TABLE para reclamar espacio en disco

Con 7.3GB a recuperar, este paso es crítico. Puede tardar 10-20 minutos.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Tamaño ANTES de OPTIMIZE ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name, ROUND((data_length + index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name = '"'"'tabVersion'"'"';" 2>/dev/null

echo "=== Espacio disco antes ==="
df -h /var/lib/mysql 2>/dev/null

echo "=== OPTIMIZE TABLE tabVersion ==="
echo "Inicio: $(date)"
mysql -u root -p".Overskull2026.m" $DB -e "OPTIMIZE TABLE tabVersion;" 2>/dev/null
echo "Fin: $(date)"

echo "=== Tamaño DESPUÉS de OPTIMIZE ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name, ROUND((data_length + index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
  AND table_name = '"'"'tabVersion'"'"';" 2>/dev/null

echo "=== Espacio disco después ==="
df -h /var/lib/mysql 2>/dev/null

echo "=== Top 10 tablas más grandes post-purga ==="
mysql -u root -p".Overskull2026.m" -e "
SELECT table_name, ROUND((data_length + index_length)/1024/1024,2) AS size_mb
FROM information_schema.tables
WHERE table_schema = '"'"'_0646d69b639ad0ff'"'"'
ORDER BY size_mb DESC LIMIT 10;" 2>/dev/null
'
```

```bash
tg_notify "✅ *CDT 028b T4* — OPTIMIZE TABLE tabVersion completado."
```

---

### T5 — Verificar impacto en rendimiento (INSERT test)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB="_0646d69b639ad0ff"

echo "=== Test INSERT velocidad en tabVersion post-purga ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SET @start = NOW(6);
INSERT INTO tabVersion (name, creation, modified, owner, ref_doctype, docname, data)
VALUES (UUID(), NOW(), NOW(), '"'"'test'"'"', '"'"'Purchase Order'"'"', '"'"'TEST-PERF-028'"'"', '"'"'{}'"'"');
SET @end = NOW(6);
SELECT TIMESTAMPDIFF(MICROSECOND, @start, @end)/1000 AS insert_ms;
DELETE FROM tabVersion WHERE docname = '"'"'TEST-PERF-028'"'"';
" 2>/dev/null

echo "=== Estado final tabVersion ==="
mysql -u root -p".Overskull2026.m" $DB -e "
SELECT COUNT(*) AS filas_restantes,
  MIN(creation) AS mas_antiguo,
  MAX(creation) AS mas_reciente
FROM tabVersion;" 2>/dev/null

echo "=== InnoDB status (lock_waits) ==="
mysql -u root -p".Overskull2026.m" -e "
SHOW GLOBAL STATUS WHERE Variable_name IN (
  '"'"'Innodb_row_lock_waits'"'"',
  '"'"'Innodb_row_lock_time_avg'"'"',
  '"'"'Threads_connected'"'"'
);" 2>/dev/null
'
```

```bash
tg_notify "🏁 *CDT 028b TERMINÓ* — tabVersion purgada + rendimiento verificado\nVer: c:\\dev\\cdtalleres\\purga-tabversion-results.md"
```

---

## Archivo de salida

Actualizar `c:\dev\cdtalleres\purga-tabversion-results.md` con los resultados de T3, T4 y T5.

### Secciones a completar

```markdown
## Estado de tareas (actualizar)

| Tarea | Estado | Notas |
|---|---|---|
| T1. Auditoría pre-purga | ✅ | filas: 27.7M, tamaño: 7.3GB, >30d: ~22.2M |
| T2. DocType CDT Historial Version creado | ✅ | tabla: tabCDT Historial Version |
| T3. Purga tabVersion > 30 días | ✅/❌ | lotes: X, borradas: X |
| T4. OPTIMIZE TABLE | ✅/❌ | antes: 7,383MB → después: XMB |
| T5. Impacto rendimiento verificado | ✅/❌ | INSERT tabVersion: Xms (antes ~71,000ms) |
| T6. Permisos UI configurados | ✅ | roles: System Manager, Accounts User, ... |
| T7. Migración DocType | ⏳ Pendiente | tarea futura — datos en otros servidores |

## Resultados (actualizar)

| Métrica | Antes | Después |
|---|---|---|
| Filas tabVersion | 27,770,713 | X |
| Tamaño tabVersion | 7,383 MB | X MB |
| INSERT tabVersion (ms) | ~71,000ms | X ms |
| Espacio disco recuperado | 0 | X GB |

## Nota migración DocType

La migración de datos históricos al DocType `CDT Historial Version` queda pendiente.
Los datos están disponibles en los servidores de producción y backup.
Se realizará como tarea independiente sin urgencia de rendimiento.
```
