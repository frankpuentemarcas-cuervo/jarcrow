---
fecha: 2026-04-25
agente_id: "003"
descripcion: limpiar-disco-servidores
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: completado
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\disco-limpieza-results.md"
---

# Limpieza de Disco en los 3 Servidores CDTalleres

## Contexto para el agente

Proyecto CDTalleres (ERPNext v13.9.2 para Shalom / Overskull). Los 3 servidores VPS tienen disco al 87% de uso (67GB usados de ~77GB). Son clones del mismo snapshot. El disco lleno es el bloqueador más inmediato antes de cualquier otra operación.

### Servidores

| Rol | IP | Usuario | Password |
|---|---|---|---|
| Backend | 164.92.94.47 | root | .Overskull2026.m |
| DB | 165.232.130.222 | root | .Overskull2026.m |
| Frontend | 209.38.75.235 | root | .Overskull2026.m |

- **Ruta del bench**: `/home/erpnext/frappe-bench`
- **Site**: `CDTALLERES`

---

## ⚠️ REGLA CRÍTICA — Reporte de bloqueos

**SIEMPRE, ante cualquier error, bloqueo o impedimento:**

1. Genera el archivo de salida con lo que tengas hasta ese momento
2. Documenta el problema en la sección `## Bloqueos y errores` del archivo
3. Incluye: qué intentaste, el error EXACTO, alternativas probadas, qué se necesita

**Nunca termines sin generar el archivo de salida.** Aunque sea parcial.

---

## ⚠️ REGLA DE SEGURIDAD — NO borrar datos de negocio

**Está PROHIBIDO borrar:**
- Archivos en `sites/CDTALLERES/private/` (adjuntos y datos de usuarios)
- Archivos en `sites/CDTALLERES/public/` (assets subidos)
- Base de datos o backups recientes (últimos 3 días)
- Cualquier archivo `.sql.gz` generado en los últimos 3 días

**Solo se puede borrar:**
- Logs de supervisor, nginx, frappe más viejos de 7 días
- Backups más viejos de 3 días
- Archivos temporales en `/tmp`
- Cache de pip/npm

---

## Tareas a ejecutar

Ejecutar en **cada uno de los 3 servidores**. Usar `sshpass` para conexión:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@<IP> '<comando>'
```

### 1. Diagnóstico inicial de espacio

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@<IP> '
echo "=== ESPACIO TOTAL ==="
df -h /

echo "=== TOP 10 DIRECTORIOS MÁS PESADOS ==="
du -sh /home/erpnext/frappe-bench/logs/* 2>/dev/null | sort -rh | head -10
du -sh /home/erpnext/frappe-bench/sites/CDTALLERES/private/backups/* 2>/dev/null | sort -rh | head -10
du -sh /tmp/* 2>/dev/null | sort -rh | head -10
du -sh /var/log/* 2>/dev/null | sort -rh | head -10

echo "=== BACKUPS EXISTENTES ==="
ls -lh /home/erpnext/frappe-bench/sites/CDTALLERES/private/backups/ 2>/dev/null
'
```

### 2. Limpiar logs de Frappe/Supervisor (más de 7 días)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@<IP> '
echo "ANTES:" && df -h / | tail -1

# Logs de frappe bench
find /home/erpnext/frappe-bench/logs/ -name "*.log" -mtime +7 -delete 2>/dev/null
find /home/erpnext/frappe-bench/logs/ -name "*.log.*" -mtime +7 -delete 2>/dev/null

# Logs de nginx
find /var/log/nginx/ -name "*.log.*" -mtime +7 -delete 2>/dev/null

# Logs de supervisor
find /var/log/supervisor/ -name "*.log.*" -mtime +7 -delete 2>/dev/null

# Tmp
rm -rf /tmp/* 2>/dev/null

echo "DESPUÉS:" && df -h / | tail -1
'
```

### 3. Limpiar backups viejos (más de 3 días)

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@<IP> '
BACKUP_DIR="/home/erpnext/frappe-bench/sites/CDTALLERES/private/backups"

echo "Backups a borrar (más de 3 días):"
find "$BACKUP_DIR" -mtime +3 -type f 2>/dev/null

echo "Borrando..."
find "$BACKUP_DIR" -mtime +3 -type f -delete 2>/dev/null

echo "Backups restantes:"
ls -lh "$BACKUP_DIR" 2>/dev/null
'
```

### 4. Espacio final por servidor

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@<IP> 'df -h /'
```

---

## Archivo de salida

**Crear al terminar (aunque sea parcial):**
```
c:\dev\cdtalleres\disco-limpieza-results.md
```

### Estructura obligatoria

```markdown
# Limpieza de Disco CDTalleres — YYYY-MM-DD HH:MM

## Resumen de espacio

| Servidor | IP | Antes | Después | Liberado |
|---|---|---|---|---|
| Backend | 164.92.94.47 | 87% | ?% | ?GB |
| DB | 165.232.130.222 | 87% | ?% | ?GB |
| Frontend | 209.38.75.235 | 87% | ?% | ?GB |

## Detalle por servidor

### Backend (164.92.94.47)
[qué se borró, cuánto se liberó]

### DB (165.232.130.222)
[qué se borró, cuánto se liberó]

### Frontend (209.38.75.235)
[qué se borró, cuánto se liberó]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
> - Error exacto:
> - Alternativas intentadas:
> - Qué se necesita:
```
