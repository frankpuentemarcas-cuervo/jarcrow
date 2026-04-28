---
fecha: 2026-04-25
agente_id: "006"
descripcion: separar-servicios-por-servidor
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: completado
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\separar-servicios-results.md"
dependencia: "003 (disco limpio) y 004 (MariaDB remoto configurado)"
---

# Separar Servicios por Servidor — CDTalleres

## Contexto para el agente

Proyecto CDTalleres (ERPNext v13.9.2 / Frappe 13.9.1 para Shalom / Overskull). Los 3 servidores son clones del mismo snapshot — todos tienen el stack completo corriendo. Hay que apagar los servicios que no corresponden a cada rol y dejar solo lo necesario.

### Arquitectura objetivo

| Servidor | IP | Rol | Servicios que DEBE tener | Servicios que APAGAR |
|---|---|---|---|---|
| Frontend/App | 209.38.75.235 | Nginx + proxy | Nginx, Supervisor (workers Frappe), Redis | MariaDB |
| Backend | 164.92.94.47 | Gunicorn workers | Supervisor (gunicorn), Redis | MariaDB, Nginx |
| DB | 165.232.130.222 | MariaDB | MariaDB | Nginx, Supervisor (workers) |

> **Nota**: En Frappe v13, Gunicorn corre vía Supervisor. El servidor Frontend/App (209.38.75.235) es el que recibirá tráfico web — Nginx ahí hará proxy a Gunicorn local. El servidor Backend (164.92.94.47) puede quedar como nodo de workers adicional en el futuro, pero por ahora el foco es levantar el sitio desde 209.38.75.235.

### Datos importantes
- **Bench path**: `/home/erpnext/frappe-bench`
- **Site**: `CDTALLERES`
- **Usuario bench**: `erpnext`
- **MariaDB**: ya configurado con acceso remoto desde 164.92.94.47 (prompt 004)

### Servidores

| Rol | IP | Usuario | Password |
|---|---|---|---|
| Frontend/App | 209.38.75.235 | root | .Overskull2026.m |
| Backend | 164.92.94.47 | root | .Overskull2026.m |
| DB | 165.232.130.222 | root | .Overskull2026.m |

---

## ⚠️ REGLA CRÍTICA — Reporte de bloqueos

**SIEMPRE, ante cualquier error, bloqueo o impedimento:**

1. Genera el archivo de salida con lo que tengas hasta ese momento
2. Documenta en `## Bloqueos y errores`: qué intentaste, error EXACTO, alternativas, qué se necesita
3. **Nunca termines sin generar el archivo de salida.** Aunque sea parcial.

---

## ⚠️ REGLA DE SEGURIDAD

- Antes de apagar cualquier servicio, verificar que el servicio homólogo en el servidor correcto está activo
- NO modificar archivos de configuración de Frappe en este prompt (eso es el siguiente paso)
- Si un `systemctl stop` falla, documentarlo y continuar con el siguiente

---

## Tareas a ejecutar

### SERVIDOR DB (165.232.130.222) — apagar Nginx y Supervisor

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222 '
echo "=== ESTADO ANTES ==="
systemctl is-active nginx mariadb supervisor redis-server

echo "=== APAGANDO servicios no necesarios ==="
systemctl stop nginx
systemctl disable nginx

systemctl stop supervisor
systemctl disable supervisor

echo "=== ESTADO DESPUÉS ==="
systemctl is-active nginx mariadb supervisor redis-server

echo "=== MARIADB CORRIENDO ==="
mysql -u root -e "SELECT 1;" 2>&1
ss -tlnp | grep 3306
'
```

### SERVIDOR BACKEND (164.92.94.47) — apagar MariaDB y Nginx

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== ESTADO ANTES ==="
systemctl is-active nginx mariadb supervisor redis-server

echo "=== APAGANDO servicios no necesarios ==="
systemctl stop nginx
systemctl disable nginx

systemctl stop mariadb
systemctl disable mariadb

echo "=== ESTADO DESPUÉS ==="
systemctl is-active nginx mariadb supervisor redis-server

echo "=== SUPERVISOR (workers) CORRIENDO ==="
supervisorctl status 2>/dev/null
'
```

### SERVIDOR FRONTEND/APP (209.38.75.235) — apagar solo MariaDB

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
echo "=== ESTADO ANTES ==="
systemctl is-active nginx mariadb supervisor redis-server

echo "=== APAGANDO MariaDB ==="
systemctl stop mariadb
systemctl disable mariadb

echo "=== ESTADO DESPUÉS ==="
systemctl is-active nginx mariadb supervisor redis-server

echo "=== NGINX CORRIENDO ==="
nginx -t 2>&1
ss -tlnp | grep -E "(80|443|8000)"

echo "=== SUPERVISOR/GUNICORN ==="
supervisorctl status 2>/dev/null

echo "=== REDIS ==="
redis-cli ping 2>/dev/null
'
```

### Verificación final — estado de los 3 servidores

```bash
for IP in 209.38.75.235 164.92.94.47 165.232.130.222; do
  echo "=== $IP ==="
  sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@$IP \
    'systemctl is-active nginx mariadb supervisor redis-server 2>/dev/null; ss -tlnp | grep -E "(80|443|3306|6379|8000)"'
done
```

---

## Archivo de salida

**Crear al terminar (aunque sea parcial):**
```
c:\dev\cdtalleres\separar-servicios-results.md
```

### Estructura obligatoria

```markdown
# Separación de Servicios CDTalleres — YYYY-MM-DD HH:MM

## Estado final por servidor

| Servidor | IP | Nginx | MariaDB | Supervisor | Redis |
|---|---|---|---|---|---|
| Frontend/App | 209.38.75.235 | ✅ activo | ❌ apagado | ✅ activo | ✅ activo |
| Backend | 164.92.94.47 | ❌ apagado | ❌ apagado | ✅ activo | ✅ activo |
| DB | 165.232.130.222 | ❌ apagado | ✅ activo | ❌ apagado | ? |

## Detalle por servidor
### Frontend/App (209.38.75.235)
[output de comandos]

### Backend (164.92.94.47)
[output de comandos]

### DB (165.232.130.222)
[output de comandos]

## Puertos escuchando por servidor
[ss -tlnp output de cada uno]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
> - Error exacto:
> - Alternativas intentadas:
> - Qué se necesita:
```
