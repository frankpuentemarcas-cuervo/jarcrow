---
fecha: 2026-04-25
agente_id: "009"
descripcion: desactivar-crons-verificar-scheduler
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\crons-scheduler-results.md"
dependencia: "008 (sitio operativo con SSL)"
---

# Desactivar Crons del SO + Verificar Frappe Scheduler — CDTalleres

## Contexto para el agente

Proyecto CDTalleres (ERPNext v13.9.2 / Frappe 13.9.1 para Shalom / Overskull). El sitio está operativo en https://cdtalleres-copia.shalom.com.pe. Arquitectura 3 servidores:

| Servidor | IP | Rol |
|---|---|---|
| Frontend/App | 209.38.75.235 | Nginx + Gunicorn + Redis — Frappe corre aquí |
| Backend | 164.92.94.47 | Workers adicionales |
| DB | 165.232.130.222 | MariaDB |

**Objetivo**:
1. Desactivar crontabs del sistema operativo en los 3 servidores (evitar interferencias con Frappe scheduler)
2. Verificar que el Frappe scheduler solo corre en Frontend/App
3. Confirmar que certbot autorenovación SSL está activo en Frontend/App

### Credenciales SSH

| Servidor | Usuario | Password |
|---|---|---|
| 209.38.75.235 | root | .Overskull2026.m |
| 164.92.94.47 | root | .Overskull2026.m |
| 165.232.130.222 | root | .Overskull2026.m |

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

Generar o actualizar el archivo de salida después de CADA tarea completada o fallida.

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

## ⚠️ REGLA DE SEGURIDAD

- NO eliminar crontabs — solo comentar las líneas con `#` para poder revertir
- NO detener el Frappe scheduler si está corriendo correctamente
- Hacer backup de crontab antes de modificar: `crontab -l > /root/crontab.bak.FECHA`

---

## Tareas a ejecutar

### 1. Auditar y desactivar crons — SERVIDOR DB (165.232.130.222)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
DATE=$(date +%Y%m%d_%H%M)

echo "=== CRONTAB ROOT ==="
crontab -l 2>/dev/null || echo "sin crontab"

echo "=== BACKUP ==="
crontab -l 2>/dev/null > /root/crontab.bak.$DATE && echo "backup: /root/crontab.bak.$DATE" || echo "sin crontab que respaldar"

echo "=== CRONS EN /etc/cron.d/ ==="
ls -la /etc/cron.d/ 2>/dev/null
cat /etc/cron.d/* 2>/dev/null

echo "=== CRONS ACTIVOS (systemd timers) ==="
systemctl list-timers --all 2>/dev/null | head -20

echo "=== COMENTAR crontab si tiene entradas ==="
crontab -l 2>/dev/null | sed "s/^[^#]/#&/" | crontab - 2>/dev/null && echo "crontab comentado" || echo "sin cambios"

echo "=== CRONTAB DESPUÉS ==="
crontab -l 2>/dev/null || echo "vacío"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T1* — Crons DB (165.232.130.222) auditados y desactivados"
```

---

### 2. Auditar y desactivar crons — SERVIDOR BACKEND (164.92.94.47)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
DATE=$(date +%Y%m%d_%H%M)

echo "=== CRONTAB ROOT ==="
crontab -l 2>/dev/null || echo "sin crontab"

echo "=== BACKUP ==="
crontab -l 2>/dev/null > /root/crontab.bak.$DATE && echo "backup: /root/crontab.bak.$DATE" || echo "sin crontab"

echo "=== CRONS EN /etc/cron.d/ ==="
ls -la /etc/cron.d/ 2>/dev/null
cat /etc/cron.d/* 2>/dev/null

echo "=== SYSTEMD TIMERS ==="
systemctl list-timers --all 2>/dev/null | head -20

echo "=== COMENTAR crontab ==="
crontab -l 2>/dev/null | sed "s/^[^#]/#&/" | crontab - 2>/dev/null && echo "comentado" || echo "sin cambios"

echo "=== CRONTAB DESPUÉS ==="
crontab -l 2>/dev/null || echo "vacío"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T2* — Crons Backend (164.92.94.47) auditados y desactivados"
```

---

### 3. Auditar crons + verificar Frappe scheduler — SERVIDOR FRONTEND/APP (209.38.75.235)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
DATE=$(date +%Y%m%d_%H%M)
BENCH=/home/erpnext/frappe-bench

echo "=== CRONTAB ROOT ==="
crontab -l 2>/dev/null || echo "sin crontab root"

echo "=== CRONTAB ERPNEXT USER ==="
crontab -u erpnext -l 2>/dev/null || echo "sin crontab erpnext"

echo "=== BACKUP CRONTABS ==="
crontab -l 2>/dev/null > /root/crontab.bak.$DATE 2>/dev/null
crontab -u erpnext -l 2>/dev/null > /root/crontab-erpnext.bak.$DATE 2>/dev/null
echo "backups creados"

echo "=== CRONS /etc/cron.d/ ==="
ls -la /etc/cron.d/
cat /etc/cron.d/* 2>/dev/null

echo "=== SYSTEMD TIMERS ==="
systemctl list-timers --all 2>/dev/null | head -20

echo "=== CERTBOT TIMER (NO desactivar) ==="
systemctl status certbot.timer 2>/dev/null | head -5
systemctl is-active certbot.timer 2>/dev/null

echo "=== FRAPPE SCHEDULER STATUS ==="
supervisorctl status 2>/dev/null
# Buscar específicamente el scheduler
supervisorctl status | grep -i "sched" 2>/dev/null

echo "=== COMENTAR crontab root (excepto certbot) ==="
crontab -l 2>/dev/null | sed "/certbot/! s/^[^#]/#&/" | crontab - 2>/dev/null && echo "root crontab comentado (certbot intacto)" || echo "sin cambios"

echo "=== CRONTAB ROOT DESPUÉS ==="
crontab -l 2>/dev/null || echo "vacío"

echo "=== FRAPPE SCHEDULER LOGS (últimas 10 líneas) ==="
tail -10 $BENCH/logs/schedule.log 2>/dev/null || echo "no hay schedule.log"
'
```

Notificar:
```bash
tg_notify "✅ *CDT T3* — Frontend crons auditados\nFrappe scheduler: [estado]\nCertbot timer: [estado]"
```

---

### 4. Verificación final — estado de crons en los 3 servidores

```bash
for IP in 209.38.75.235 164.92.94.47 165.232.130.222; do
  echo "=== $IP ==="
  sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@$IP \
    'echo "crontab:"; crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" | wc -l; echo "lineas activas"' 2>/dev/null
done
```

Notificar al terminar:
```bash
tg_notify "🏁 *CDT 009 TERMINÓ* — Crons desactivados en 3 servidores\nVer: c:\\dev\\cdtalleres\\crons-scheduler-results.md"
```

---

## Archivo de salida

**Crear o actualizar después de CADA tarea:**
```
c:\dev\cdtalleres\crons-scheduler-results.md
```

### Estructura obligatoria

```markdown
# Crons + Scheduler CDTalleres — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| 1. Crons DB desactivados | ✅/❌ | entradas comentadas: N |
| 2. Crons Backend desactivados | ✅/❌ | entradas comentadas: N |
| 3. Crons Frontend auditados | ✅/❌ | certbot intacto: sí/no |
| 4. Verificación final | ✅/❌ | |

## Crontabs encontrados antes de cambios

### DB (165.232.130.222)
[contenido]

### Backend (164.92.94.47)
[contenido]

### Frontend (209.38.75.235) — root
[contenido]

### Frontend (209.38.75.235) — usuario erpnext
[contenido]

## Frappe Scheduler

- Estado en supervisor: [running/stopped]
- Certbot timer activo: ✅/❌
- Últimas líneas schedule.log: [contenido]

## Crons activos restantes (líneas no comentadas)

| Servidor | Líneas activas |
|---|---|
| DB | N |
| Backend | N |
| Frontend | N (solo certbot si aplica) |

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
