---
fecha: 2026-04-25
agente_id: "016"
descripcion: optimizar-naming-series-hash-doctypes-criticos
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\naming-series-fix-results.md"
dependencia: "015 (auditoría tabSeries — lista de DocTypes a migrar)"
---

# Optimizar Naming Series — Migrar DocTypes críticos a Hash/UUID

## Contexto para el agente

Proyecto CDTalleres. Stress test (prompt 014) identificó causa raíz del colapso: **contención en `tabSeries`** — ERPNext hace `SELECT ... FOR UPDATE` por cada documento creado, serializando todas las escrituras. Con 50+ usuarios concurrentes el sistema colapsa (row_lock_time_avg: 14,740ms).

La solución es cambiar los DocTypes de alto volumen de **naming series numérica** a **"hash"** (UUID-based). Hash genera el nombre sin tocar `tabSeries`, eliminando el lock completamente.

**El audit (015) ya está disponible en `c:\dev\cdtalleres\tabseries-audit-results.md`.** Lista de DocTypes a modificar ya conocida — no leer el archivo, usar los datos de abajo directamente.

### DocTypes a modificar — resultado confirmado del audit 015

| Prioridad | DocType | Naming actual | Registros | Observación |
|---|---|---|---|---|
| 🔴 Alta | **Orden de Trabajo 2** | `naming_series` (Orden-Trabajo-) | 33,760 | Inyectado en módulo HR de erpnext core |
| 🔴 Alta | **Historial Notificaciones** | `NOT.#######` | 92,286 | App `notification` custom |
| ⛔ NO tocar | Stock Ledger Entry | `MAT-SLE-.YYYY.-` | 325,317 | Core ERPNext — demasiado crítico |
| ⛔ NO tocar | GL Entry | `ACC-GLE-.YYYY.-` | 201,143 | Core ERPNext — requiere análisis contable |
| 🟢 Baja | Solicitud de Pagos | `SOL-PAG0-.#####` | 17,430 | Evaluar en fase 2 |

**ALERTA**: `tabWorkflow Action` tiene 2.79 millones de filas (480MB) — no tiene naming series pero indica acumulación de logs de workflow sin purgar. Documentar en el archivo de salida como deuda técnica. NO modificar en este prompt.

### ¿Qué cambia con Hash?

| Naming Series (actual) | Hash (objetivo) |
|---|---|
| Orden-Trabajo-43068 | a8f3c2d1e4b5 (formato corto) |
| Usa `SELECT ... FOR UPDATE` en tabSeries | No toca tabSeries |
| Serializa escrituras concurrentes | Paralelo sin bloqueo |
| Registro secuencial y legible | No secuencial |

**Trade-off**: IDs dejan de ser secuenciales. Para `Orden de Trabajo 2` e `Historial Notificaciones` (internos, no visibles al cliente en documentos fiscales) es aceptable.

### Sitio real

**IMPORTANTE**: El sitio se llama `CDTALLERES` (no `cdtalleres-copia.shalom.com.pe`). Usar este nombre en todos los comandos `bench --site`.

### Servidores

| Rol | IP | Credenciales |
|---|---|---|
| Frontend (ERPNext + bench) | 209.38.75.235 | root / .Overskull2026.m |
| DB | 165.232.130.222 | root / .Overskull2026.m |

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Genera o actualiza el archivo de salida inmediatamente con lo ejecutado
2. Documenta CADA tarea: resultado (✅/❌), output exacto, error completo si falló
3. Nunca termines sin el archivo de salida. Aunque sea parcial.
4. Si una tarea falla, documentarla y continuar con la siguiente.
5. **HACER BACKUP antes de cualquier modificación.**

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

### 0. Verificar nombre real del sitio

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
ls /home/erpnext/frappe-bench/sites/
'
```

**Esperado**: directorio `CDTALLERES`. Si el nombre es diferente, usar ese nombre en todos los comandos siguientes.

---

### 1. Backup de DocType configs actuales (los 2 a modificar)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DB=_0646d69b639ad0ff
mysql -u root -p".Overskull2026.m" "$DB" -e "
SELECT name, autoname, naming_rule
FROM \`tabDocType\`
WHERE name IN (\"Orden de Trabajo 2\", \"Historial Notificaciones\");
" 2>/dev/null
'
```

Guardar ese output en el archivo de salida como backup antes de modificar.

Notificar:
```bash
tg_notify "✅ *CDT 016 T1* — Backup naming configs de los 2 DocTypes registrado"
```

---

### 2a. Modificar: Orden de Trabajo 2 → hash

**Nota**: Este DocType está inyectado en el módulo HR de erpnext core. El cambio se hace vía DB directamente ya que `bench set_value` puede no persistir si hay un archivo JSON en la app que lo sobreescriba al migrar.

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

echo "=== ANTES ==="
sudo -u erpnext bench --site $SITE execute frappe.db.get_value \
  --args '["DocType", "Orden de Trabajo 2", ["autoname", "naming_rule"]]' 2>&1

echo "=== CAMBIANDO autoname a hash ==="
sudo -u erpnext bench --site $SITE execute frappe.db.set_value \
  --args '["DocType", "Orden de Trabajo 2", "autoname", "hash"]' 2>&1

echo "=== VERIFICAR ==="
sudo -u erpnext bench --site $SITE execute frappe.db.get_value \
  --args '["DocType", "Orden de Trabajo 2", "autoname"]' 2>&1

echo "=== BUSCAR JSON en erpnext para verificar si se sobreescribirá ==="
find $BENCH/apps/erpnext -name "orden_de_trabajo_2.json" -o \
     -name "orden de trabajo 2.json" 2>/dev/null | head -5

echo "=== LIMPIAR CACHÉ ==="
sudo -u erpnext bench --site $SITE clear-cache 2>&1 | tail -3
'
```

**Si el `find` encuentra un archivo JSON**: el agente debe editar ese JSON y cambiar `"autoname": "naming_series"` por `"autoname": "hash"` para que el cambio sobreviva a migraciones futuras. Documentar la ruta del archivo en el output.

Notificar:
```bash
tg_notify "✅ *CDT 016 T2a* — Orden de Trabajo 2 → autoname=hash"
```

---

### 2b. Modificar: Historial Notificaciones → hash

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

echo "=== ANTES ==="
sudo -u erpnext bench --site $SITE execute frappe.db.get_value \
  --args '["DocType", "Historial Notificaciones", ["autoname", "naming_rule"]]' 2>&1

echo "=== BUSCAR JSON en app notification ==="
find $BENCH/apps/notification -name "historial_notificaciones.json" \
     -o -name "historial notificaciones.json" 2>/dev/null

echo "=== CAMBIANDO autoname a hash ==="
sudo -u erpnext bench --site $SITE execute frappe.db.set_value \
  --args '["DocType", "Historial Notificaciones", "autoname", "hash"]' 2>&1

echo "=== VERIFICAR ==="
sudo -u erpnext bench --site $SITE execute frappe.db.get_value \
  --args '["DocType", "Historial Notificaciones", "autoname"]' 2>&1

echo "=== LIMPIAR CACHÉ ==="
sudo -u erpnext bench --site $SITE clear-cache 2>&1 | tail -3
'
```

**Si el `find` encuentra JSON**: editar ese JSON también (`"autoname": "hash"`). Es la app `notification` — código propio, sin riesgo de romper core.

Notificar:
```bash
tg_notify "✅ *CDT 016 T2b* — Historial Notificaciones → autoname=hash"
```

---

### 3. Verificar creación con hash — ambos DocTypes

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES

echo "=== TEST — Orden de Trabajo 2 ==="
sudo -u erpnext bench --site $SITE execute frappe.client.insert \
  --args '{"doctype": "Orden de Trabajo 2"}' 2>&1 | grep -E '"name"' | head -3
# Esperado: nombre tipo "a8f3c2d1e4b5" en lugar de "Orden-Trabajo-043069"

echo ""
echo "=== TEST — Historial Notificaciones ==="
sudo -u erpnext bench --site $SITE execute frappe.client.insert \
  --args '{"doctype": "Historial Notificaciones"}' 2>&1 | grep -E '"name"' | head -3
# Esperado: nombre tipo "b7d2e9f0c3a1" en lugar de "NOT0095738"
'
```

---

### 4. Verificar que tabSeries ya NO se incrementa

```bash
DB=_0646d69b639ad0ff

# Contadores ANTES
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 "
mysql -u root -p'.Overskull2026.m' $DB -e \"
SELECT name, current FROM tabSeries
WHERE name IN ('Orden-Trabajo-', 'NOT')
ORDER BY name;
\" 2>/dev/null
"

# Crear 5 docs de cada DocType modificado
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
BENCH=/home/erpnext/frappe-bench
SITE=CDTALLERES
for i in 1 2 3 4 5; do
  sudo -u erpnext bench --site $SITE execute frappe.client.insert \
    --args '"'"'{"doctype": "Orden de Trabajo 2"}'"'"' 2>&1 | grep '"'"'"name"'"'"' | head -1
done
for i in 1 2 3 4 5; do
  sudo -u erpnext bench --site $SITE execute frappe.client.insert \
    --args '"'"'{"doctype": "Historial Notificaciones"}'"'"' 2>&1 | grep '"'"'"name"'"'"' | head -1
done
'

# Contadores DESPUÉS — deben ser iguales
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 "
mysql -u root -p'.Overskull2026.m' $DB -e \"
SELECT name, current FROM tabSeries
WHERE name IN ('Orden-Trabajo-', 'NOT')
ORDER BY name;
\" 2>/dev/null
"
```

**Resultado esperado**: `Orden-Trabajo-` sigue en 43068, `NOT` sigue en 95737.

Notificar:
```bash
tg_notify "✅ *CDT 016 T4* — tabSeries NO incrementó. Fix verificado en ambos DocTypes."
```

---

### 5. Mini stress test de verificación — 50 usuarios, 3 minutos

Reset de contadores globales de InnoDB antes del test para medición limpia:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "FLUSH STATUS;" 2>/dev/null
echo "Contadores InnoDB reseteados"
'
```

Lanzar test:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
cd /opt/cdtalleres-stress
mkdir -p /opt/cdtalleres-stress/results_post_fix

echo "=== MINI STRESS TEST POST-FIX — 50 usuarios, 3 min ==="
locust \
  --locustfile locustfile.py \
  --host https://cdtalleres-copia.shalom.com.pe \
  --users 50 \
  --spawn-rate 10 \
  --run-time 3m \
  --headless \
  --csv /opt/cdtalleres-stress/results_post_fix/stress_postfix \
  2>&1 | tail -40

echo "=== RESULTADOS CSV ==="
cat /opt/cdtalleres-stress/results_post_fix/stress_postfix_stats.csv 2>/dev/null
'

# Métricas DB post-test
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
mysql -u root -p".Overskull2026.m" -e "
  SHOW GLOBAL STATUS LIKE \"Innodb_row_lock_waits\";
  SHOW GLOBAL STATUS LIKE \"Innodb_row_lock_time_avg\";
  SHOW GLOBAL STATUS LIKE \"Threads_connected\";
" 2>/dev/null
'
```

**Comparación objetivo**:

| Métrica | Antes del fix | Objetivo post-fix |
|---|---|---|
| `Innodb_row_lock_time_avg` | 14,740ms | < 100ms |
| Fail rate endpoints escritura | 95-100% | < 5% |
| Latencia p95 | 120s (timeout) | < 5s |
| Concurrencia de colapso | ~50 usuarios | > 100 usuarios |

Notificar:
```bash
# Si mejoró:
tg_notify "✅ *CDT 016 T5* — Mini stress post-fix: lock contention eliminado\nrow_lock_time_avg: [valor] ms\nFail rate: [X]%"
# Si no mejoró:
tg_notify "⚠️ *CDT 016 T5* — Mini stress post-fix: aún hay problemas\nVer: c:\\dev\\cdtalleres\\naming-series-fix-results.md"
```

---

### 6. Registrar deuda técnica — tabWorkflow Action y DocTypes core

```bash
echo "Documentar en archivo de salida (sin ejecutar cambios):"
echo "1. tabWorkflow Action: 2.79M filas / 480MB — purgar registros antiguos (prompt futuro)"
echo "2. Stock Ledger Entry (325k) y GL Entry (201k): core ERPNext — NO modificar autoname"
echo "   Alternativa futura: override antes del submit vía Server Script si escala"
```

No ejecutar nada. Solo documentar en el archivo de salida.

Notificar al terminar:
```bash
tg_notify "🏁 *CDT 016 TERMINÓ* — Naming series optimizado\nVer: c:\\dev\\cdtalleres\\naming-series-fix-results.md"
```

---

## Archivo de salida

```
c:\dev\cdtalleres\naming-series-fix-results.md
```

### Estructura obligatoria

```markdown
# Naming Series Fix CDTalleres — YYYY-MM-DD HH:MM

## DocTypes modificados (prioridad Alta)

| DocType | Naming anterior | Naming nuevo | Verificado | tabSeries dejó de incrementar |
|---|---|---|---|---|
| Orden de Trabajo 2 | naming_series (Orden-Trabajo-) | hash | ✅/❌ | ✅/❌ |
| Historial Notificaciones | NOT.####### | hash | ✅/❌ | ✅/❌ |

## Resultado mini stress test post-fix (50 usuarios, 3 min)

| Endpoint | Requests | Failures | Fail% | p50 | p95 | row_lock_time_avg |
|---|---|---|---|---|---|---|
| POST /Orden de Trabajo 2 | N | N | N% | Nms | Nms | Nms |
| POST /Purchase Order | N | N | N% | Nms | Nms | Nms |

**Comparación**: row_lock_time_avg antes: 14,740ms → después: [valor]ms

## DocTypes NO modificados — justificación

| DocType | Naming config | Registros | Motivo de exclusión | Estrategia futura |
|---|---|---|---|---|
| Stock Ledger Entry | MAT-SLE-.YYYY.- | 325,317 | Core ERPNext crítico | Evaluar Server Script override |
| GL Entry | ACC-GLE-.YYYY.- | 201,143 | Core ERPNext crítico | Evaluar Server Script override |
| Solicitud de Pagos | SOL-PAG0-.##### | 17,430 | Volumen bajo | Fase 2 |

## Deuda técnica detectada

- **tabWorkflow Action**: 2,790,159 filas / 480MB — acumulación sin purga. Crear prompt de limpieza.

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
