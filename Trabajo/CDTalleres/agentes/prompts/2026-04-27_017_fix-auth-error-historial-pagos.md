---
fecha: 2026-04-27
agente_id: "017"
descripcion: "diagnostico-auth-error-password-not-found-historial-pagos-txt"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: ejecucion-diagnostico-fix
estado: completado
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_017_fix-auth-error-historial-pagos.md"
---

# Fix: AuthenticationError "Password not found" — Generar TXT Solicitud de Pagos

## 🚨 Error Reportado

Usuario click botón "Generar TXT" en Solicitud de Pagos → server retorna:

```json
{
  "valor": false,
  "msn": "Error al crear un historial de pagos",
  "error": {
    "exc_type": "AuthenticationError",
    "exc": "frappe.exceptions.AuthenticationError: Password not found"
  }
}
```

**Stack trace clave:**
```
File "frappe/api.py", line 244, in validate_api_key_secret
    doc_secret = frappe.utils.password.get_decrypted_password(doctype, doc, fieldname='api_secret')
File "frappe/utils/password.py", line 51, in get_decrypted_password
    frappe.throw(_('Password not found'), frappe.AuthenticationError)
```

---

## 🏗️ Arquitectura Involucrada

| Componente | Server | Rol |
|---|---|---|
| **Laravel App (origen request)** | `157.245.187.72:2324` (P-SERVICE) | Botón "Generar TXT" — Laravel calls Frappe API |
| **Frappe Backend (Frappe API)** | `164.92.94.47` | Recibe POST autenticado, valida api_key+api_secret |
| **MariaDB (`__Auth` table)** | `165.232.130.222` (10.124.0.7) | Almacena `api_secret` cifrado |

Flujo error:
1. Laravel → POST `https://cdtalleres.shalom.com.pe/api/method/...` con header `Authorization: token API_KEY:API_SECRET`
2. Frappe localiza User por `api_key`
3. Frappe intenta decifrar `api_secret` de `__Auth` → **falla** ← AQUÍ
4. AuthenticationError "Password not found" → Laravel recibe error

**Endpoint Laravel afectado:** [`NominaSalarialController.php:1787-1792`](file:///var/www/html/horario_salida/app/Http/Controllers/ERPNext/NominaSalarialController.php#L1787)

---

## 🔐 ACCESO SSH

```bash
# Frontend
ssh -i ~/.ssh/cdtalleres_frontend root@209.38.75.235

# Backend (Frappe)
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47

# DB dedicada
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222

# Laravel App (P-SERVICE)
ssh -i ~/.ssh/cdtalleres_frontend -p 2324 root@157.245.187.72
```

**DB:** `_0646d69b639ad0ff` (10.124.0.7)
**Pass MariaDB root:** `.Overskull2026.m`

---

## 🎯 Hipótesis a Verificar

| H | Causa | Probabilidad |
|---|---|---|
| H1 | `__Auth.password` borrado para usuario API | ALTA |
| H2 | `encryption_key` en site_config.json cambió → no decifra secrets viejos | ALTA |
| H3 | Usuario API regenerado pero secret nuevo no fue guardado en Laravel | MEDIA |
| H4 | Migración Frappe corrompió tabla `__Auth` | MEDIA |
| H5 | api_key Laravel no coincide con ningún user Frappe | BAJA |

---

## 📋 Tareas

### T1 — Identificar API key que envía Laravel

```bash
ssh -i ~/.ssh/cdtalleres_frontend -p 2324 root@157.245.187.72 '

cd /var/www/html/horario_salida

echo "=== Buscar config api_key/api_secret en Laravel ===" 
grep -rn "api_key\|api_secret" app/Http/Controllers/ERPNext/NominaSalarialController.php 2>/dev/null | head -20

echo ""
echo "=== Variables ENV relacionadas ===" 
grep -E "API_KEY|API_SECRET|FRAPPE|ERP|CDTALLERES" .env 2>/dev/null

echo ""
echo "=== Buscar BD donde Laravel guarda credenciales ===" 
grep -rn "users_erpnext\|api_credentials\|frappe_users" app/Http/Controllers/ 2>/dev/null | head -10

'
```

**Esperado:** Identificar dónde Laravel obtiene api_key/api_secret (BD propia, .env, config).

---

### T2 — Extraer api_key actual usada por Laravel

```bash
ssh -i ~/.ssh/cdtalleres_frontend -p 2324 root@157.245.187.72 '

cd /var/www/html/horario_salida

echo "=== Conexión BD Laravel ===" 
grep -E "DB_HOST|DB_DATABASE|DB_USERNAME" .env 2>/dev/null

echo ""
echo "=== Tablas relacionadas a auth Frappe ===" 
php artisan tinker --execute="
\$tables = DB::select('"'"'SHOW TABLES'"'"');
foreach (\$tables as \$t) {
    \$name = array_values((array)\$t)[0];
    if (stripos(\$name, '"'"'erp'"'"') !== false || stripos(\$name, '"'"'frappe'"'"') !== false || stripos(\$name, '"'"'api'"'"') !== false) {
        echo \$name . PHP_EOL;
    }
}
" 2>&1 | head -20

'
```

**Esperado:** Localizar tabla Laravel que guarda credenciales API.

---

### T3 — Listar API users en Frappe (BD dedicada)

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222 '

echo "=== Users con api_key configurado ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name as user,
  api_key,
  enabled,
  user_type
FROM tabUser
WHERE api_key IS NOT NULL AND api_key != '"'"''"'"''
ORDER BY name;
" 2>&1

echo ""
echo "=== Conteo api_secret en __Auth ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  doctype,
  fieldname,
  COUNT(*) as count
FROM __Auth
WHERE fieldname = '"'"'api_secret'"'"'
GROUP BY doctype, fieldname;
" 2>&1

echo ""
echo "=== Comparar: Users con api_key vs __Auth.api_secret ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  u.name as user,
  u.api_key,
  CASE WHEN a.password IS NULL THEN '"'"'❌ NO SECRET'"'"' ELSE '"'"'✅ HAS SECRET'"'"' END as secret_status
FROM tabUser u
LEFT JOIN __Auth a ON a.doctype = '"'"'User'"'"' AND a.name = u.name AND a.fieldname = '"'"'api_secret'"'"'
WHERE u.api_key IS NOT NULL AND u.api_key != '"'"''"'"''
ORDER BY u.name;
" 2>&1

'
```

**Esperado:** 
- Lista users con api_key
- Identificar cuáles tienen `__Auth.password` faltante → causa "Password not found"

---

### T4 — Verificar `encryption_key` en site_config

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

# Site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | grep -v common_site | head -1)

echo "=== encryption_key actual ===" 
grep "encryption_key" /home/erpnext/frappe-bench/sites/$SITE/site_config.json 2>&1

echo ""
echo "=== Backup configs (verificar si encryption_key cambió) ===" 
ls -la /home/erpnext/frappe-bench/sites/$SITE/site_config.json* 2>&1
ls -la /home/erpnext/frappe-bench/sites/$SITE/private/backups/*.gz 2>&1 | tail -5

echo ""
echo "=== Test decrypt con key actual ===" 
cd /home/erpnext/frappe-bench
bench --site $SITE console << "PYEOF"
import frappe
from frappe.utils.password import get_decrypted_password

# Listar users con api_key
users = frappe.db.sql("""
    SELECT name, api_key 
    FROM tabUser 
    WHERE api_key IS NOT NULL AND api_key != ""
""", as_dict=True)

print(f"Users con api_key: {len(users)}")

for u in users:
    try:
        secret = get_decrypted_password("User", u.name, "api_secret")
        if secret:
            print(f"OK   {u.name}: secret decrypts (len={len(secret)})")
        else:
            print(f"FAIL {u.name}: secret NULL")
    except Exception as e:
        print(f"FAIL {u.name}: {str(e)[:80]}")
PYEOF

'
```

**Esperado:** Identificar exactamente qué users fallan al decifrar (lista exacta).

---

### T5 — Inspeccionar tabla `__Auth` directamente

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222 '

echo "=== Estructura __Auth ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "DESCRIBE __Auth;" 2>&1

echo ""
echo "=== Registros api_secret existentes ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  doctype,
  name as user,
  fieldname,
  LEFT(password, 30) as encrypted_preview,
  LENGTH(password) as len
FROM __Auth
WHERE fieldname = '"'"'api_secret'"'"'
ORDER BY name;
" 2>&1

'
```

**Esperado:** Ver users con secret en `__Auth`. Comparar con `tabUser.api_key`.

---

### T6 — Localizar usuario API que usa Laravel "Generar TXT"

```bash
ssh -i ~/.ssh/cdtalleres_frontend -p 2324 root@157.245.187.72 '

cd /var/www/html/horario_salida

echo "=== Código exacto NominaSalarialController línea 1750-1800 ===" 
sed -n "1750,1800p" app/Http/Controllers/ERPNext/NominaSalarialController.php 2>&1

echo ""
echo "=== Función que obtiene credentials ===" 
grep -B 2 -A 10 "api_key\|api_secret" app/Http/Controllers/ERPNext/NominaSalarialController.php | head -50

'
```

**Esperado:** Ver cómo Laravel construye Authorization header. Identificar:
- ¿Hardcoded api_key/secret?
- ¿BD Laravel guarda credentials?
- ¿Por usuario logged?

---

### T7 — FIX A: Regenerar api_secret de user afectado (si __Auth roto)

**Pre-requisito:** Saber qué user usa Laravel (obtenido en T6).

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

# Site
SITE=$(ls /home/erpnext/frappe-bench/sites/ | grep -v patches.json | grep -v common_site | head -1)

cd /home/erpnext/frappe-bench

echo "=== Regenerar api_secret usuario afectado ===" 

# CAMBIAR: ${USER_EMAIL} por usuario real que usa Laravel
USER_EMAIL="administrator@cdtalleres.com"  # AJUSTAR

bench --site $SITE console << PYEOF
import frappe
from frappe.utils.password import update_password

USER = "$USER_EMAIL"

# Generar nuevo api_secret
import secrets
new_secret = secrets.token_hex(15)

# Setear secret cifrado en __Auth
frappe.db.sql("""
    DELETE FROM __Auth WHERE doctype='User' AND name=%s AND fieldname='api_secret'
""", USER)

# Insertar via Frappe API (cifrado correcto)
user_doc = frappe.get_doc("User", USER)
user_doc.api_secret = new_secret
user_doc.save(ignore_permissions=True)
frappe.db.commit()

# Verificar
from frappe.utils.password import get_decrypted_password
decrypted = get_decrypted_password("User", USER, "api_secret")
print(f"User: {USER}")
print(f"api_key: {user_doc.api_key}")
print(f"new api_secret: {new_secret}")
print(f"verify decrypt: {'"'"'OK'"'"' if decrypted == new_secret else '"'"'FAIL'"'"'}")
PYEOF

'
```

**⚠️ NO ejecutar T7 hasta confirmar usuario en T6.**

---

### T8 — FIX B: Actualizar credenciales en Laravel

Después de T7, copiar nuevo `api_secret` a Laravel:

```bash
ssh -i ~/.ssh/cdtalleres_frontend -p 2324 root@157.245.187.72 '

cd /var/www/html/horario_salida

# Si Laravel guarda en .env:
echo "=== Backup .env actual ===" 
cp .env .env.bak.$(date +%s)

# CAMBIAR estas 2 lineas con nuevo api_key/api_secret de T7
# sed -i "s|^API_KEY=.*|API_KEY=NUEVO_API_KEY|" .env
# sed -i "s|^API_SECRET=.*|API_SECRET=NUEVO_API_SECRET|" .env

# Si Laravel guarda en BD:
# php artisan tinker --execute "DB::table(...)..."

echo "=== Cache clear Laravel ===" 
php artisan config:clear
php artisan cache:clear

'
```

**⚠️ Este task es plantilla. Ejecutar después de T6 confirmar dónde guarda Laravel y T7 generar nuevo secret.**

---

### T9 — Test end-to-end

```bash
echo "=== Test desde Laravel curl al endpoint Frappe ===" 

ssh -i ~/.ssh/cdtalleres_frontend -p 2324 root@157.245.187.72 "

# Reemplazar API_KEY y API_SECRET con valores actualizados
API_KEY=\"...\"
API_SECRET=\"...\"

curl -s -X GET 'https://cdtalleres.shalom.com.pe/api/method/frappe.auth.get_logged_user' \
  -H \"Authorization: token \${API_KEY}:\${API_SECRET}\" \
  -k | head -50

"
```

**Esperado:** `{"message":"<usuario>"}` (no AuthenticationError).

---

### T10 — Validación final BD

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@165.232.130.222 '

echo "=== Estado final __Auth para users API ===" 
mysql -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  u.name as user,
  u.enabled,
  CASE WHEN u.api_key IS NULL OR u.api_key = '"'"''"'"' THEN '"'"'NO KEY'"'"' ELSE '"'"'HAS KEY'"'"' END as key_status,
  CASE WHEN a.password IS NULL THEN '"'"'❌ NO SECRET'"'"' ELSE '"'"'✅ HAS SECRET'"'"' END as secret_status
FROM tabUser u
LEFT JOIN __Auth a ON a.doctype = '"'"'User'"'"' AND a.name = u.name AND a.fieldname = '"'"'api_secret'"'"'
WHERE u.api_key IS NOT NULL AND u.api_key != '"'"''"'"''
ORDER BY u.name;
" 2>&1

'
```

**Esperado:** Todos users con api_key tienen api_secret válido.

---

## 📋 Checklist

- [ ] T1: Identificado dónde Laravel guarda credenciales (env/BD)
- [ ] T2: Localizada tabla/config con api_key actual
- [ ] T3: Listados users API en Frappe + estado __Auth
- [ ] T4: encryption_key NO cambió + lista users que fallan decrypt
- [ ] T5: Inspeccionada tabla __Auth (registros existentes)
- [ ] T6: Identificado usuario exacto que Laravel usa
- [ ] T7: Regenerado api_secret usuario afectado (FIX A)
- [ ] T8: Actualizado credenciales Laravel (FIX B)
- [ ] T9: Test curl autenticado retorna user (no error)
- [ ] T10: BD final muestra todos users con secret válido

---

## 📊 Reporte

Crear: `c:\jarcrow\Trabajo\CDTalleres\agentes\respuestas\2026-04-27_017_fix-auth-error-historial-pagos.md`

**Estructura:**

```markdown
# Fix AuthenticationError Generar TXT

## T1: Config Laravel
[output] — credentials en: env/BD/hardcoded

## T2: api_key actual usada
api_key: [valor]
storage: [env/tabla X/etc]

## T3: Estado users Frappe
Users con api_key: [N]
Users sin __Auth.api_secret: [lista]

## T4: Decrypt test
[output bench console]
Users que FALLAN: [lista exacta]
encryption_key: [valor presente/cambiado]

## T5: Tabla __Auth
[output records]

## T6: Usuario Laravel
User identificado: [email]
Línea código: NominaSalarialController.php:[L]

## T7: Regeneración secret
new api_secret: [valor]
verify decrypt: [OK/FAIL]

## T8: Update Laravel
Storage actualizado: [si/no]

## T9: Test E2E
curl response: [exact output]

## T10: BD final
Todos users OK: [si/no]

## CONCLUSIÓN
**Causa raíz:** [H1/H2/H3/H4/H5]
**Fix aplicado:** [descripción]
**Estado final:** [resuelto/pendiente]
```

---

## ⚠️ INSTRUCCIONES CRÍTICAS

1. **T1-T6 solo investigación** — NO modificar nada
2. **T7-T8 modifican** — ejecutar SOLO después de identificar user exacto en T6
3. **Backup `.env`** antes de cualquier cambio en Laravel (T8 ya lo hace)
4. **Confirmar encryption_key NO cambió** (T4) antes de regenerar secret — si cambió, hay que rotar TODOS los secrets
5. Si T4 muestra `encryption_key` distinto a histórico → problema mayor (rotar todos secrets cifrados)

---

## 🔄 Plan Rollback

Si T7 rompe acceso de otros sistemas que usaban mismo user:

```bash
# Restore .env Laravel
ssh -i ~/.ssh/cdtalleres_frontend -p 2324 root@157.245.187.72 '
cd /var/www/html/horario_salida
ls -la .env.bak.* | tail -1
# Restaurar backup
'
```

api_secret nuevo NO afecta otros sistemas si usan api_secret distinto.
Si comparten mismo user → todos sistemas necesitan update credentials.

---

## 🎯 Resultado Esperado

Usuario click "Generar TXT" en Solicitud de Pagos:
- ✅ Laravel envía request autenticado a Frappe
- ✅ Frappe valida api_key + api_secret correctamente
- ✅ Frappe crea Historial Pagos TXT (autoname=hash + before_insert SEQUENCE = `HPT-XXXXX`)
- ✅ Laravel recibe 200 OK + nombre documento
- ✅ Sin AuthenticationError "Password not found"
