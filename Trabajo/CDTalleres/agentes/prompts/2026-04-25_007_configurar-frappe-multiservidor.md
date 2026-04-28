---
fecha: 2026-04-25
agente_id: "007"
descripcion: configurar-frappe-multiservidor
proyecto: CDTalleres
ia_destino: antigravity
tipo: ejecucion
estado: completado
falla: ""
archivo_salida: "c:\\dev\\cdtalleres\\frappe-config-results.md"
dependencia: "006 (servicios separados)"
---

# Configurar Frappe para Arquitectura Multi-Servidor — CDTalleres

## Contexto para el agente

Proyecto CDTalleres (ERPNext v13.9.2 / Frappe 13.9.1 para Shalom / Overskull). Los servicios ya están separados. Ahora hay que decirle a Frappe dónde está cada servicio: la DB está en otro servidor (165.232.130.222) y el sitio debe levantar correctamente en el servidor Frontend/App (209.38.75.235).

### Arquitectura actual

| Servidor | IP | Rol |
|---|---|---|
| Frontend/App | 209.38.75.235 | Nginx + Gunicorn + Redis — **aquí corre Frappe** |
| Backend | 164.92.94.47 | Workers adicionales (por ahora secundario) |
| DB | 165.232.130.222 | MariaDB 10.4.21 |

### Datos importantes
- **Bench path**: `/home/erpnext/frappe-bench`
- **Site**: `CDTALLERES`
- **Usuario bench**: `erpnext`
- **MariaDB IP remota**: `165.232.130.222`
- **DB name y password**: obtener de `/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json`
- **Dominio**: `cdtalleres-copia.shalom.com.pe` (apunta a 209.38.75.235)

### Servidores

| Rol | IP | Usuario | Password |
|---|---|---|---|
| Frontend/App (trabajo principal aquí) | 209.38.75.235 | root | .Overskull2026.m |
| DB | 165.232.130.222 | root | .Overskull2026.m |

---

## ⚠️ REGLA CRÍTICA — Reporte completo obligatorio

**El archivo de salida debe generarse AL TERMINAR CADA TAREA, no solo al final.**

Ante cualquier situación — éxito, error, bloqueo o impedimento:

1. **Genera o actualiza el archivo de salida** con lo ejecutado hasta ese momento
2. Documenta CADA paso: su resultado (✅/❌), output relevante, y si falló: error EXACTO + alternativas probadas
3. **Nunca termines sin el archivo de salida.** Aunque sea parcial.
4. Si un paso falla y no hay alternativa, documentarlo y **continuar con el siguiente paso** — no detenerse.

---

## ⚠️ REGLA DE SEGURIDAD

- Hacer backup de TODOS los archivos de config antes de modificarlos
- Si Frappe no levanta después de un cambio, restaurar el backup y documentar el error

---

## Tareas a ejecutar (todas en servidor 209.38.75.235)

Conectar:
```bash
sshpass -p '.Overskull2026.m' ssh -o StrictHostKeyChecking=no root@209.38.75.235
```

### 1. Backup de configs actuales

```bash
BENCH=/home/erpnext/frappe-bench
DATE=$(date +%Y%m%d_%H%M)

cp $BENCH/sites/CDTALLERES/site_config.json $BENCH/sites/CDTALLERES/site_config.json.bak.$DATE
cp $BENCH/sites/common_site_config.json $BENCH/sites/common_site_config.json.bak.$DATE 2>/dev/null

echo "Backups creados:"
ls -lh $BENCH/sites/CDTALLERES/site_config.json.bak.$DATE
ls -lh $BENCH/sites/common_site_config.json.bak.$DATE 2>/dev/null
```

### 2. Ver configuración actual

```bash
echo "=== site_config.json ==="
cat /home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json

echo "=== common_site_config.json ==="
cat /home/erpnext/frappe-bench/sites/common_site_config.json 2>/dev/null
```

Documentar los valores actuales de `db_host`, `db_name`, `db_password` en el archivo de salida.

### 3. Actualizar site_config.json — apuntar a DB remota

Editar `/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json` y agregar/actualizar `db_host`:

```bash
# Ver el archivo primero
cat /home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json

# Agregar db_host con Python (no rompe el JSON)
python3 -c "
import json
f = '/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json'
with open(f) as fp:
    cfg = json.load(fp)
cfg['db_host'] = '165.232.130.222'
cfg['db_port'] = 3306
with open(f, 'w') as fp:
    json.dump(cfg, fp, indent=1)
print('OK:', json.dumps(cfg, indent=1))
"
```

### 4. Verificar conexión a MariaDB remota desde este servidor

```bash
DB_PASS=$(python3 -c "import json; print(json.load(open('/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json'))['db_password'])")
DB_NAME=$(python3 -c "import json; print(json.load(open('/home/erpnext/frappe-bench/sites/CDTALLERES/site_config.json'))['db_name'])")

echo "DB: $DB_NAME"
mysql -h 165.232.130.222 -u "$DB_NAME" -p"$DB_PASS" "$DB_NAME" -e "SELECT COUNT(*) as total_doctypes FROM tabDocType;" 2>&1
```

Si falla: documentar el error exacto. Posibles causas: usuario no tiene permisos desde 209.38.75.235 (el prompt 004 solo lo hizo para 164.92.94.47). En ese caso, hacer el grant desde el servidor DB.

### 5. Reiniciar servicios de Frappe

```bash
# Como root, reiniciar supervisor
supervisorctl reload 2>/dev/null
supervisorctl restart all 2>/dev/null
sleep 5
supervisorctl status

# Reiniciar nginx
nginx -t && systemctl restart nginx
systemctl status nginx | head -10
```

### 6. Verificar que Frappe levanta

```bash
# Verificar que gunicorn responde localmente
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 2>/dev/null
echo ""

# Verificar que nginx responde en 80
curl -s -o /dev/null -w "%{http_code}" http://209.38.75.235 2>/dev/null
echo ""

# Ver logs de error
tail -30 /home/erpnext/frappe-bench/logs/web.log 2>/dev/null
tail -20 /var/log/nginx/error.log 2>/dev/null
```

### 7. Agregar el dominio al site de Frappe

```bash
cd /home/erpnext/frappe-bench
sudo -u erpnext bench --site CDTALLERES add-to-hosts 2>/dev/null || true

# Verificar que el site responde con el dominio (sin SSL aún)
curl -s -o /dev/null -w "%{http_code}" -H "Host: cdtalleres-copia.shalom.com.pe" http://209.38.75.235 2>/dev/null
echo ""
```

---

## Archivo de salida

**Crear al terminar (aunque sea parcial):**
```
c:\dev\cdtalleres\frappe-config-results.md
```

### Estructura obligatoria

```markdown
# Configuración Frappe Multi-Servidor CDTalleres — YYYY-MM-DD HH:MM

## Configuración actual (antes de cambios)
- db_host: [valor original]
- db_name: [valor]
- db_password: [valor — necesario para siguientes prompts]
- redis_cache: [valor]
- redis_queue: [valor]

## Cambios realizados

| Paso | Estado | Detalle |
|---|---|---|
| Backup configs | ✅/❌ | |
| db_host actualizado | ✅/❌ | nuevo valor: 165.232.130.222 |
| Conexión MariaDB remota | ✅/❌ | resultado del SELECT |
| Servicios reiniciados | ✅/❌ | |
| Gunicorn responde en :8000 | ✅/❌ | HTTP code: |
| Nginx responde en :80 | ✅/❌ | HTTP code: |
| Dominio responde | ✅/❌ | HTTP code: |

## Logs de error relevantes
[Cualquier error en web.log o nginx/error.log]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
> - Error exacto:
> - Alternativas intentadas:
> - Qué se necesita:
```
