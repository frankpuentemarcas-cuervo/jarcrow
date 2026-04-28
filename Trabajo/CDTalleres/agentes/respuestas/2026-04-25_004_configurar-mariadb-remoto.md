---
fecha: 2026-04-25
agente_id: "004"
prompt_ref: "prompts/2026-04-25_004_configurar-mariadb-remoto.md"
estado: parcial
archivo_fuente: "c:\\dev\\cdtalleres\\mariadb-config-results.md"
---

# Respuesta Agente 004 — MariaDB Remoto

## Credenciales ERPNext (IMPORTANTE — usar en prompts siguientes)

- **db_name**: `_0646d69b639ad0ff`
- **db_password**: `f1Z6583dZNustHQC`
- **db_host objetivo**: `165.232.130.222`

## Estado

| Paso | Estado |
|---|---|
| bind-address → 0.0.0.0 | ✅ en `/etc/mysql/my.cnf` |
| MariaDB reiniciado | ✅ |
| Firewall UFW puerto 3306 desde Backend | ✅ |
| Puerto 3306 accesible desde Backend | ✅ `nc -zv` exitoso |
| GRANT usuario remoto `_0646d69b639ad0ff`@`164.92.94.47` | ⚠️ NO HECHO |
| GRANT usuario remoto `_0646d69b639ad0ff`@`209.38.75.235` | ⚠️ NO HECHO |

## Bloqueador pendiente

Root MariaDB tiene contraseña desconocida. El archivo `/root/.my.cnf` tiene `4X+9zXs3k6%1e` pero no funciona.
El GRANT no se pudo ejecutar → el usuario Frappe NO puede conectar remotamente aún.

## Acción requerida antes de prompt 006

Acceso interactivo al servidor DB para ejecutar el GRANT:
```sql
-- Conectar a MariaDB (probar sin password o con la del .my.cnf)
mysql -u root
-- o
mysql -u root -p  -- probar: 4X+9zXs3k6%1e | .Overskull2026.m | (vacío)

-- Una vez dentro:
GRANT ALL PRIVILEGES ON `_0646d69b639ad0ff`.* TO '_0646d69b639ad0ff'@'164.92.94.47' IDENTIFIED BY 'f1Z6583dZNustHQC';
GRANT ALL PRIVILEGES ON `_0646d69b639ad0ff`.* TO '_0646d69b639ad0ff'@'209.38.75.235' IDENTIFIED BY 'f1Z6583dZNustHQC';
FLUSH PRIVILEGES;
```
