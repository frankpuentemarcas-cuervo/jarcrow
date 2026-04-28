---
fecha: 2026-04-25
agente_id: "001"
descripcion: verificar-conectividad
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: fallido
falla: "Agente no pudo conectar por SSH. Requirió sshpass. No generó archivo de salida."
archivo_salida: "c:\\dev\\cdtalleres\\server-audit-results.md"
---

# Verificación de Conectividad a Servidores CDTalleres

## Contexto para el agente

Soy parte del equipo de Overskull. Estamos investigando problemas de performance en un ERPNext de producción (proyecto CDTalleres para Shalom). Se han creado 3 servidores desde un snapshot del servidor original para dividir la carga y encontrar el cuello de botella. Necesito que verifiques la conectividad y el estado actual de cada servidor.

### Proyecto
- **Nombre**: CDTalleres (ERPNext v15)
- **Stack**: Frappe Framework, MariaDB, Redis, Gunicorn, Nginx
- **Situación actual**: 3 servidores clonados desde snapshot, aún sin separar servicios

### Servidores

| Rol | IP | Usuario | Password |
|---|---|---|---|
| Backend (Gunicorn/Workers) | 164.92.94.47 | root | .Overskull2026.m |
| Base de datos (MariaDB) | 165.232.130.222 | root | .Overskull2026.m |
| Frontend/App (Nginx) | 209.38.75.235 | root | .Overskull2026.m |

> **Nota**: Los 3 servidores fueron creados desde el MISMO snapshot. Inicialmente todos tienen TODOS los servicios (ERPNext completo). La separación se hará después.

---

## ⚠️ REGLA CRÍTICA — Reporte de bloqueos

**ANTES de pedir ayuda al usuario o detenerte, SIEMPRE:**

1. Genera el archivo de salida con lo que tengas hasta ese momento
2. Documenta el bloqueo en la sección `## Bloqueos y errores` del archivo
3. Incluye: qué intentaste, el error exacto, qué alternativas probaste, qué necesitas

**Nunca termines sin generar el archivo de salida.** Aunque sea parcial. Aunque hayas fallado en todo. El archivo debe existir.

---

## Método de conexión SSH

Los servidores usan **contraseña** (no llave SSH). Para conectar desde terminal:

### Opción A — sshpass (si está disponible)
```bash
# Instalar si no existe
sudo apt-get install -y sshpass   # Linux
brew install hudochenkov/sshpass/sshpass  # Mac

# Conectar
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@<IP>
```

### Opción B — ssh con entrada manual
```bash
ssh -o StrictHostKeyChecking=no root@<IP>
# Cuando pida contraseña: .Overskull2026.m
```

### Opción C — comandos remotos directos (sin sesión interactiva)
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@<IP> '<comando>'

# Ejemplo:
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 'uname -a && free -h && df -h'
```

**Si sshpass no está disponible**: documentar el error, intentar Opción B, si tampoco funciona documentarlo en el archivo de salida y continuar con los servidores restantes.

---

## Tareas a ejecutar

### 1. Verificar conectividad básica (ping)
```bash
ping -c 3 164.92.94.47
ping -c 3 165.232.130.222
ping -c 3 209.38.75.235
```
Documentar: responde / no responde / timeout.

### 2. Conectar a cada servidor y recopilar información

Para **cada uno de los 3 servidores**, ejecutar el siguiente bloque completo:

```bash
IP=<IP_DEL_SERVIDOR>
PASS='.Overskull2026.m'

sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$IP '
echo "=== SISTEMA ==="
uname -a
cat /etc/os-release | grep -E "^(NAME|VERSION)="
hostname

echo "=== RECURSOS ==="
nproc
free -h
df -h /

echo "=== CPU ==="
lscpu | grep -E "(Model name|CPU\(s\)|Thread)"

echo "=== SERVICIOS ACTIVOS ==="
systemctl list-units --type=service --state=running 2>/dev/null | grep -E "(nginx|supervisor|mariadb|mysql|redis|gunicorn|frappe)"

echo "=== PUERTOS ==="
ss -tlnp | grep -E "(80|443|3306|6379|8000|8080|9000)"

echo "=== BENCH ==="
find /home -name "apps.txt" 2>/dev/null | head -3
sudo -u frappe bash -c "cd /home/frappe/frappe-bench && bench version 2>/dev/null" 2>/dev/null

echo "=== MARIADB ==="
mysql -u root -e "SELECT @@version; SHOW GLOBAL STATUS LIKE '"'"'Threads_connected'"'"';" 2>/dev/null

echo "=== CARGA ==="
uptime
top -bn1 | head -15
'
```

Si el comando falla para un servidor, documentar el error exacto y continuar con el siguiente.

### 3. Verificar conectividad entre servidores

Desde servidor Backend (164.92.94.47), probar acceso al servidor DB:
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== CONECTIVIDAD A DB ==="
nc -zv 165.232.130.222 3306 2>&1
mysql -h 165.232.130.222 -u root -p'"'"'.Overskull2026.m'"'"' -e "SELECT 1;" 2>&1
'
```

---

## Archivo de salida

**El agente DEBE crear este archivo al terminar, aunque sea con resultados parciales:**
```
c:\dev\cdtalleres\server-audit-results.md
```

### Estructura obligatoria del archivo

```markdown
# Auditoría de Servidores CDTalleres — YYYY-MM-DD HH:MM

## Estado de ejecución
| Servidor | IP | Ping | SSH | Datos recopilados |
|---|---|---|---|---|
| Backend | 164.92.94.47 | ✅/❌ | ✅/❌ | ✅/❌ |
| DB | 165.232.130.222 | ✅/❌ | ✅/❌ | ✅/❌ |
| Frontend | 209.38.75.235 | ✅/❌ | ✅/❌ | ✅/❌ |

## Servidor Backend (164.92.94.47)
### Sistema
### Recursos (CPU / RAM / Disco)
### Servicios activos
### ERPNext / Bench

## Servidor DB (165.232.130.222)
### Sistema
### Recursos
### Servicios activos
### MariaDB

## Servidor Frontend (209.38.75.235)
### Sistema
### Recursos
### Servicios activos
### Nginx

## Conectividad entre servidores

## Hallazgos y recomendaciones

## Bloqueos y errores
> Documentar CUALQUIER error encontrado:
> - Herramienta faltante (ej: sshpass no instalado)
> - Error de conexión SSH (mensaje exacto)
> - Comando que falló (comando + output de error)
> - Qué alternativas se intentaron
> - Qué se necesita para resolverlo
```
