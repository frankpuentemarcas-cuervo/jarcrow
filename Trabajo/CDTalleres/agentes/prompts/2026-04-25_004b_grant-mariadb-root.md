---
fecha: 2026-04-25
agente_id: "004b"
descripcion: grant-mariadb-root
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: completado
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\grant-mariadb-results.md"
dependencia: "004 (bind-address ya en 0.0.0.0, UFW ya abierto)"
---

# Resolver GRANT MariaDB — Acceso Remoto Usuario Frappe

## Contexto para el agente

Proyecto CDTalleres (ERPNext v13.9.2 para Shalom / Overskull). El servidor DB (165.232.130.222) ya tiene MariaDB escuchando en 0.0.0.0:3306 y el firewall abierto. El problema: el agente anterior no pudo ejecutar el GRANT porque la contraseña de root MariaDB es desconocida. Hay que encontrar la contraseña de root y ejecutar los GRANTs necesarios.

### Servidor de trabajo

| Rol | IP | Usuario SSH | Password SSH |
|---|---|---|---|
| DB | 165.232.130.222 | root | .Overskull2026.m |

### Datos conocidos

- **db_name (usuario Frappe)**: `_0646d69b639ad0ff`
- **db_password (usuario Frappe)**: `f1Z6583dZNustHQC`
- **IP Backend** (necesita acceso a DB): `164.92.94.47`
- **IP Frontend/App** (necesita acceso a DB): `209.38.75.235`
- **Config MariaDB**: `/etc/mysql/my.cnf`
- **Posibles passwords root probadas antes**: `.Overskull2026.m`, `4X+9zXs3k6%1e` (fallaron en modo no interactivo)

---

## ⚠️ REGLA CRÍTICA — Reporte de bloqueos

**SIEMPRE, ante cualquier error, bloqueo o impedimento:**

1. Genera el archivo de salida con lo que tengas hasta ese momento
2. Documenta en `## Bloqueos y errores`: qué intentaste, error EXACTO, alternativas, qué se necesita
3. **Nunca termines sin generar el archivo de salida.** Aunque sea parcial.

---

## Tareas a ejecutar

Conectar al servidor DB:
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@165.232.130.222
```

### 1. Encontrar la contraseña de root MariaDB

Intentar en este orden. Detenerse en el primero que funcione.

```bash
# Intento A — sin password (auth_socket)
mysql -u root -e "SELECT 1;" 2>&1

# Intento B — password del sistema SSH
mysql -u root -p'.Overskull2026.m' -e "SELECT 1;" 2>&1

# Intento C — password del .my.cnf
mysql -u root -p'4X+9zXs3k6%1e' -e "SELECT 1;" 2>&1

# Intento D — ver si hay otro archivo .my.cnf
cat /root/.my.cnf 2>/dev/null
cat /home/erpnext/.my.cnf 2>/dev/null

# Intento E — ver plugin de auth de root
mysql -u root -e "SELECT User, Host, plugin FROM mysql.user WHERE User='root';" 2>/dev/null
```

### 2. Si ninguna contraseña funciona — reset de root via modo seguro

```bash
# Detener MariaDB
systemctl stop mariadb

# Iniciar en modo skip-grant-tables
mysqld_safe --skip-grant-tables --skip-networking &
sleep 3

# Entrar sin password y resetear
mysql -u root << 'EOF'
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY '.Overskull2026.m';
FLUSH PRIVILEGES;
EOF

# Detener mysqld_safe y reiniciar normal
kill $(pgrep mysqld_safe) 2>/dev/null
kill $(pgrep mysqld) 2>/dev/null
sleep 2
systemctl start mariadb
sleep 3

# Verificar con nueva password
mysql -u root -p'.Overskull2026.m' -e "SELECT 'root OK';" 2>&1
```

### 3. Ejecutar los GRANTs (una vez con acceso root)

Usar la contraseña que funcionó del paso anterior:

```bash
mysql -u root -p'[PASSWORD_QUE_FUNCIONO]' << 'EOF'
-- Ver usuarios actuales del sitio
SELECT User, Host FROM mysql.user WHERE User = '_0646d69b639ad0ff';

-- GRANT desde servidor Backend
GRANT ALL PRIVILEGES ON `_0646d69b639ad0ff`.* 
  TO '_0646d69b639ad0ff'@'164.92.94.47' 
  IDENTIFIED BY 'f1Z6583dZNustHQC';

-- GRANT desde servidor Frontend/App
GRANT ALL PRIVILEGES ON `_0646d69b639ad0ff`.* 
  TO '_0646d69b639ad0ff'@'209.38.75.235' 
  IDENTIFIED BY 'f1Z6583dZNustHQC';

FLUSH PRIVILEGES;

-- Verificar que quedaron creados
SELECT User, Host FROM mysql.user WHERE User = '_0646d69b639ad0ff';
EOF
```

### 4. Verificar conexión desde servidor Backend

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@164.92.94.47 '
mysql -h 165.232.130.222 \
      -u _0646d69b639ad0ff \
      -pf1Z6583dZNustHQC \
      _0646d69b639ad0ff \
      -e "SELECT COUNT(*) as tablas FROM information_schema.tables WHERE table_schema=DATABASE();" 2>&1
'
```

### 5. Verificar conexión desde servidor Frontend/App

```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235 '
mysql -h 165.232.130.222 \
      -u _0646d69b639ad0ff \
      -pf1Z6583dZNustHQC \
      _0646d69b639ad0ff \
      -e "SELECT COUNT(*) as tablas FROM information_schema.tables WHERE table_schema=DATABASE();" 2>&1
'
```

Resultado esperado: número de tablas (ERPNext v13 tiene ~900+ tablas).

---

## Archivo de salida

**Crear al terminar (aunque sea parcial):**
```
c:\dev\cdtalleres\grant-mariadb-results.md
```

### Estructura obligatoria

```markdown
# GRANT MariaDB CDTalleres — YYYY-MM-DD HH:MM

## Contraseña root encontrada
- Método que funcionó: [intento A/B/C/D/reset]
- Password root: [valor — necesario para operaciones futuras]

## GRANTs ejecutados

| Usuario | Host | Estado |
|---|---|---|
| _0646d69b639ad0ff | 164.92.94.47 | ✅/❌ |
| _0646d69b639ad0ff | 209.38.75.235 | ✅/❌ |

## Verificación de conexión remota

| Servidor origen | Resultado | Tablas encontradas |
|---|---|---|
| Backend 164.92.94.47 | ✅/❌ | número |
| Frontend 209.38.75.235 | ✅/❌ | número |

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
> - Error exacto:
> - Alternativas intentadas:
> - Qué se necesita:
```
