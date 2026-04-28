---
fecha: 2026-04-25
agente_id: "004"
descripcion: configurar-mariadb-remoto
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: superado-por-004b
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\mariadb-config-results.md"
dependencia: "003 (disco debe tener espacio antes de modificar config)"
---

# Configurar MariaDB para Conexiones Remotas — Servidor DB

## Contexto para el agente

Proyecto CDTalleres (ERPNext v13.9.2 para Shalom / Overskull). Estamos separando servicios en 3 servidores. El servidor DB (165.232.130.222) tiene MariaDB 10.4.21 con `bind-address = 127.0.0.1`, lo que impide que el servidor Backend (164.92.94.47) se conecte remotamente. Hay que habilitarlo.

### Servidores involucrados

| Rol | IP | Usuario | Password |
|---|---|---|---|
| **DB** (donde trabajarás) | 165.232.130.222 | root | .Overskull2026.m |
| Backend (origen de conexión) | 164.92.94.47 | root | .Overskull2026.m |

- **MariaDB versión**: 10.4.21
- **Config file**: `/etc/mysql/mariadb.conf.d/50-server.cnf`
- **Site ERPNext**: `CDTALLERES`
- **Bench path**: `/home/erpnext/frappe-bench`

---

## ⚠️ REGLA CRÍTICA — Reporte de bloqueos

**SIEMPRE, ante cualquier error, bloqueo o impedimento:**

1. Genera el archivo de salida con lo que tengas hasta ese momento
2. Documenta el problema en la sección `## Bloqueos y errores`
3. Incluye: qué intentaste, error EXACTO, alternativas probadas, qué se necesita

**Nunca termines sin generar el archivo de salida.** Aunque sea parcial.

---

## ⚠️ REGLA DE SEGURIDAD

- Hacer backup del archivo de config ANTES de modificarlo
- NO cambiar contraseñas de usuarios existentes
- NO borrar usuarios o bases de datos existentes
- Si algo falla, restaurar el backup del config y dejar MariaDB en estado original

---

## Tareas a ejecutar

Conectar al servidor DB:
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222
```

### 1. Obtener credenciales actuales de ERPNext

Necesitamos el usuario y password que Frappe usa para conectarse a MariaDB:

```bash
cat /home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json
# Buscar: db_name, db_password
```

Documentar `db_name` y `db_password` en el archivo de salida (necesarios para el siguiente paso).

### 2. Backup del archivo de configuración

```bash
cp /etc/mysql/mariadb.conf.d/50-server.cnf /etc/mysql/mariadb.conf.d/50-server.cnf.bak.$(date +%Y%m%d)
echo "Backup creado: OK"
ls -lh /etc/mysql/mariadb.conf.d/
```

### 3. Cambiar bind-address

```bash
# Ver config actual
grep -n "bind-address" /etc/mysql/mariadb.conf.d/50-server.cnf

# Cambiar a 0.0.0.0 (acepta conexiones de cualquier IP)
sed -i 's/^bind-address.*=.*/bind-address = 0.0.0.0/' /etc/mysql/mariadb.conf.d/50-server.cnf

# Verificar cambio
grep -n "bind-address" /etc/mysql/mariadb.conf.d/50-server.cnf
```

### 4. Reiniciar MariaDB

```bash
systemctl restart mariadb
sleep 3
systemctl status mariadb | head -20

# Verificar que escucha en 0.0.0.0:3306
ss -tlnp | grep 3306
```

### 5. Crear usuario con acceso remoto desde Backend

```bash
# Reemplazar DB_NAME y DB_PASS con los valores del site_config.json obtenidos en Tarea 1
mysql -u root << 'EOF'
-- Ver usuarios existentes
SELECT User, Host FROM mysql.user WHERE User NOT IN ('root', 'mysql', '');

-- Crear usuario con acceso desde IP del Backend
-- IMPORTANTE: reemplazar DB_NAME y DB_PASS con valores reales del site_config.json
GRANT ALL PRIVILEGES ON `DB_NAME`.* TO 'DB_NAME'@'164.92.94.47' IDENTIFIED BY 'DB_PASS';
FLUSH PRIVILEGES;

-- Verificar
SELECT User, Host FROM mysql.user WHERE Host = '164.92.94.47';
EOF
```

### 6. Verificar conectividad desde servidor Backend

Desde el servidor Backend, probar conexión al DB:

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
echo "=== TEST CONEXIÓN A DB REMOTO ==="
nc -zv 165.232.130.222 3306 2>&1
# Si nc no disponible:
# timeout 5 bash -c "</dev/tcp/165.232.130.222/3306" && echo "PUERTO ABIERTO" || echo "PUERTO CERRADO"
'
```

### 7. Verificar firewall (UFW)

En el servidor DB:
```bash
ufw status
# Si UFW está activo, abrir puerto 3306 solo para Backend:
ufw allow from 164.92.94.47 to any port 3306
ufw status
```

---

## Archivo de salida

**Crear al terminar (aunque sea parcial):**
```
c:\dev\cdtalleres\mariadb-config-results.md
```

### Estructura obligatoria

```markdown
# Configuración MariaDB Remoto CDTalleres — YYYY-MM-DD HH:MM

## Credenciales ERPNext encontradas
- db_name: [valor]
- db_password: [valor — necesario para prompts siguientes]

## Cambios realizados

| Paso | Estado | Detalle |
|---|---|---|
| Backup config | ✅/❌ | |
| bind-address cambiado | ✅/❌ | valor anterior → 0.0.0.0 |
| MariaDB reiniciado | ✅/❌ | |
| Usuario remoto creado | ✅/❌ | |
| Firewall actualizado | ✅/❌ | |
| Conexión desde Backend | ✅/❌ | |

## Verificación final
[output de `ss -tlnp | grep 3306` y test de conexión]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
> - Error exacto:
> - Alternativas intentadas:
> - Qué se necesita:
```
