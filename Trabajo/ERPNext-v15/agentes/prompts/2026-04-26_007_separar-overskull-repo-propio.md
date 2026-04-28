---
fecha: 2026-04-26
agente_id: "007"
descripcion: separar-app-overskull-repo-propio-github
proyecto: ERPNext-v15
ia_destino: antigravity
tipo: ejecucion
estado: pendiente
falla: ""
archivo_salida: "c:\\dev\\erpv15\\overskull-repo-results.md"
dependencia: "ninguna"
---

# Separar App Overskull — Repo Propio en GitHub

## Contexto para el agente

Proyecto ERPNext v15 de Shalom. La custom app `overskull` vive actualmente dentro del repo de infraestructura Docker (`erprrhhover`), en la ruta `docker/data/apps/overskull/`. Esta carpeta está **excluida del repo** vía `.gitignore` (`docker/data/` está ignorado), por lo tanto la app no tiene historial en GitHub.

**Objetivo**: Extraer la app overskull a su propio repo GitHub, inicializar git limpio, hacer primer commit, y conectar producción a ese repo. Esto permite que GitHub Actions haga deploy solo de la app, sin mezclar con infra.

### Rutas clave (local Windows)

- App local: `c:\dev\erpv15\docker\data\apps\overskull\`
- Repo docker actual: `c:\dev\erpv15\` → remote `https://github.com/frankpuentemarcas-cuervo/erprrhhover.git`
- SSH key producción: `c:\dev\erpv15\id_rsa_deploy`

### Producción

- Servidor: `178.128.181.196`
- SSH: `ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no root@178.128.181.196`
- App en prod: `/home/erpnext/frappe-bench/apps/overskull/`
- Bench: `/home/erpnext/frappe-bench/`
- Site: `erp15docker.shalomcontrol.com`

### Estado actual app local

- Git inicializado: **SÍ** (tiene `.git/` propio desde cuando fue creada con bench)
- Remote actual: ninguno (estaba aislada del repo docker por `.gitignore`)
- Historial: 0 commits propios (el historial que ves es del repo padre docker)
- Fixtures: `overskull/fixtures/*.json` — exportados y listos
- `.gitignore` actual: `.DS_Store`, `*.pyc`, `*.egg-info`, `*.swp`, `tags`, `node_modules`, `__pycache__`

---

## ⚠️ REGLA CRÍTICA — Reporte después de CADA tarea

1. Crear `c:\dev\erpv15\overskull-repo-results.md` y actualizar después de CADA tarea
2. Documentar resultado (✅/❌), output exacto, errores completos
3. Si un paso falla → documentar → no continuar sin resolver
4. Nunca terminar sin el archivo de salida

## 📲 Notificaciones Telegram — obligatorio después de CADA tarea

```bash
TBOT_TOKEN="8610126794:AAFcmZUxmq9swtkOMH7Ez-vbLFOvTelLFOs"
TBOT_CHAT="1412266627"
# En Windows usar PowerShell:
# Invoke-WebRequest -Uri "https://api.telegram.org/bot$TBOT_TOKEN/sendMessage" -Method POST -Body @{chat_id=$TBOT_CHAT; text="mensaje"; parse_mode="Markdown"}
```

---

## Tareas a ejecutar

### T1 — Crear repo GitHub `overskull-app`

Crear repo nuevo en GitHub bajo el usuario `frankpuentemarcas-cuervo`:

- **Nombre**: `overskull-app`
- **Visibilidad**: Private
- **Sin README** (para no tener conflictos al primer push)
- **Sin .gitignore** (la app ya tiene el suyo)

Usar GitHub CLI si está disponible:

```powershell
# Verificar gh CLI
gh --version

# Crear repo privado
gh repo create frankpuentemarcas-cuervo/overskull-app --private --description "Overskull SAC — Custom app ERPNext v15"
```

Si `gh` no está instalado, crear manualmente desde https://github.com/new y documentar la URL del repo creado.

**Documentar**: URL del repo creado → `https://github.com/frankpuentemarcas-cuervo/overskull-app`

---

### T2 — Mejorar `.gitignore` de la app

El `.gitignore` actual es mínimo. Agregar exclusiones para archivos de debug, QA y datos que no deben versionarse:

```powershell
$gitignorePath = "c:\dev\erpv15\docker\data\apps\overskull\.gitignore"

$additions = @"

# Ruff cache
.ruff_cache/

# Archivos de debug y QA (scripts temporales)
overskull/pcge_*.py
overskull/qa_*.py
overskull/check_*.py
overskull/verify_*.py
overskull/debug_*.py
overskull/fix_property_setter.py
overskull/restore_master_data.py
overskull/crear_asistencias*.py
overskull/add_attendance_status.py
overskull/setup_attendance*.py
overskull/update_*.py
overskull/leave_migration.py
overskull/leave_fixes.py
overskull/leave_configuration.py
overskull/task_hooks.py
overskull/test_report.py
cleanup_leave.py

# Datos de fixtures que no son código
overskull/fixtures/*.xlsx
overskull/fixtures/Registro_*.xlsx

# Planning interno
.planning/

# Resultados de tests
*.log
"@

Add-Content -Path $gitignorePath -Value $additions
Get-Content $gitignorePath
```

**IMPORTANTE**: Antes de agregar al `.gitignore`, confirmar con Frank si alguno de esos archivos SÍ debe versionarse. Los scripts de `scripts/` (payroll, attendance) probablemente SÍ son parte de la app — NO ignorarlos.

---

### T3 — Inicializar git limpio y primer commit

La app puede tener un `.git/` previo con estado confuso. Hacer git limpio:

```powershell
Set-Location "c:\dev\erpv15\docker\data\apps\overskull"

# Verificar estado actual
git status
git log --oneline -3 2>$null

# Si tiene .git/ con historial ajeno — reiniciar limpio
# ADVERTENCIA: esto borra historial local de la app
Remove-Item -Recurse -Force .git -ErrorAction SilentlyContinue

# Inicializar repo limpio
git init
git branch -M main

# Configurar remote
git remote add origin https://github.com/frankpuentemarcas-cuervo/overskull-app.git

# Ver qué archivos quedarán en el commit
git status
```

Revisar qué archivos aparecen como untracked. Confirmar que no hay datos sensibles (passwords, tokens). Luego:

```powershell
# Stage todo (el .gitignore filtra lo que no debe ir)
git add .

# Verificar qué se va a commitear
git status
git diff --cached --stat

# Primer commit
git commit -m "feat: initial commit — overskull custom app v0.0.1

Apps: frappe, erpnext, hrms
Fixtures: Custom Fields, Property Setters, Client Scripts, Server Scripts, Print Formats
Overrides: attendance, employee_checkin, leave_application, payroll_entry, salary_slip
DocTypes propios: Fondo de Pensiones, TablaHistorialContratos"
```

---

### T4 — Push al repo GitHub

```powershell
Set-Location "c:\dev\erpv15\docker\data\apps\overskull"

# Push inicial
git push -u origin main
```

Si falla por autenticación, usar token personal de GitHub (Personal Access Token):

```powershell
# Configurar credenciales si pide
git remote set-url origin https://[TOKEN]@github.com/frankpuentemarcas-cuervo/overskull-app.git
git push -u origin main
```

**Verificar**: abrir `https://github.com/frankpuentemarcas-cuervo/overskull-app` y confirmar que los archivos están visibles.

---

### T5 — Conectar producción al repo

En el servidor de producción, reemplazar la app actual (sin git) por un clone del repo:

```bash
ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no root@178.128.181.196 '
BENCH=/home/erpnext/frappe-bench
APP_PATH=$BENCH/apps/overskull

echo "=== Backup app actual ==="
cp -r $APP_PATH ${APP_PATH}_backup_20260426
ls -la $BENCH/apps/

echo "=== Verificar bench puede ver la app ==="
cd $BENCH
ls apps/

echo "=== Inicializar git en app existente ==="
cd $APP_PATH
git init
git branch -M main
git remote add origin https://github.com/frankpuentemarcas-cuervo/overskull-app.git

echo "=== Pull desde GitHub ==="
git fetch origin main
git reset --hard origin/main

echo "=== Verificar estado ==="
git log --oneline -3
git status
'
```

**NOTA**: Si el repo es privado, necesita token de acceso o deploy key. Ver T6.

---

### T6 — Configurar Deploy Key en GitHub para producción

Para que producción pueda hacer `git pull` sin contraseña:

**Paso 6a — Generar SSH key en servidor de producción:**

```bash
ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no root@178.128.181.196 '
# Generar key para deploy (sin passphrase)
ssh-keygen -t ed25519 -C "erpnext-prod-deploy" -f /root/.ssh/overskull_deploy -N ""
echo "=== Clave pública (agregar a GitHub) ==="
cat /root/.ssh/overskull_deploy.pub

echo "=== Configurar SSH para usar esta key con GitHub ==="
cat >> /root/.ssh/config << EOF

Host github-overskull
    HostName github.com
    User git
    IdentityFile /root/.ssh/overskull_deploy
    StrictHostKeyChecking no
EOF
cat /root/.ssh/config
'
```

**Paso 6b — Agregar la clave pública como Deploy Key en GitHub:**
- Ir a `https://github.com/frankpuentemarcas-cuervo/overskull-app/settings/keys`
- Click "Add deploy key"
- Title: `erpnext-prod-178.128.181.196`
- Key: pegar el contenido de `overskull_deploy.pub`
- **NO marcar** "Allow write access"
- Click "Add key"

**Paso 6c — Cambiar remote en producción a SSH:**

```bash
ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no root@178.128.181.196 '
cd /home/erpnext/frappe-bench/apps/overskull
git remote set-url origin git@github-overskull:frankpuentemarcas-cuervo/overskull-app.git
git remote -v

echo "=== Test pull ==="
git pull
'
```

---

### T7 — Crear GitHub Actions workflow de deploy

Crear el archivo de workflow en la app local:

```powershell
New-Item -ItemType Directory -Force -Path "c:\dev\erpv15\docker\data\apps\overskull\.github\workflows"

$workflow = @'
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy overskull app to production
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: 178.128.181.196
          username: root
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            set -e
            BENCH=/home/erpnext/frappe-bench
            SITE=erp15docker.shalomcontrol.com

            echo "=== Pull latest overskull ==="
            cd $BENCH/apps/overskull
            git pull origin main

            echo "=== Migrate (aplica fixtures nuevos) ==="
            cd $BENCH
            bench --site $SITE migrate

            echo "=== Build assets (si hay cambios JS/CSS) ==="
            bench build --app overskull

            echo "=== Restart workers ==="
            supervisorctl restart all

            echo "=== Deploy completado: $(date) ==="
'@

Set-Content -Path "c:\dev\erpv15\docker\data\apps\overskull\.github\workflows\deploy.yml" -Value $workflow -Encoding utf8
```

**Paso 7b — Agregar SSH_PRIVATE_KEY como secret en GitHub:**
- Ir a `https://github.com/frankpuentemarcas-cuervo/overskull-app/settings/secrets/actions`
- Click "New repository secret"
- Name: `SSH_PRIVATE_KEY`
- Value: contenido de `c:\dev\erpv15\id_rsa_deploy` (la key privada completa, incluyendo header/footer)
- Click "Add secret"

**Paso 7c — Commitear y pushear el workflow:**

```powershell
Set-Location "c:\dev\erpv15\docker\data\apps\overskull"
git add .github/
git commit -m "ci: add GitHub Actions deploy workflow to production"
git push
```

---

### T8 — Verificar ciclo completo

Hacer un cambio mínimo y verificar que llega a producción automáticamente:

```powershell
# Editar README con timestamp
Set-Location "c:\dev\erpv15\docker\data\apps\overskull"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
Add-Content -Path README.md -Value "`n<!-- deploy test $timestamp -->"

git add README.md
git commit -m "test: verify CI/CD pipeline end-to-end"
git push
```

Luego verificar en GitHub Actions:
- `https://github.com/frankpuentemarcas-cuervo/overskull-app/actions`
- El workflow debe aparecer en ejecución

Y en producción confirmar el pull llegó:

```bash
ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no root@178.128.181.196 \
  "cd /home/erpnext/frappe-bench/apps/overskull && git log --oneline -3"
```

---

## Archivo de salida

```
c:\dev\erpv15\overskull-repo-results.md
```

### Estructura obligatoria

```markdown
# Overskull Repo Setup — YYYY-MM-DD HH:MM

## Estado de tareas

| Tarea | Estado | Notas |
|---|---|---|
| T1. Repo GitHub creado | ✅/❌ | URL: https://github.com/frankpuentemarcas-cuervo/overskull-app |
| T2. .gitignore mejorado | ✅/❌ | archivos excluidos: |
| T3. Git init + primer commit | ✅/❌ | archivos commiteados: X |
| T4. Push a GitHub | ✅/❌ | URL verificada: |
| T5. Producción conectada | ✅/❌ | git pull OK: |
| T6. Deploy key configurada | ✅/❌ | key en GitHub: sí/no |
| T7. GitHub Actions workflow | ✅/❌ | workflow URL: |
| T8. Ciclo completo verificado | ✅/❌ | push → deploy: OK/FAIL |

## Flujo CI/CD resultante

push main → GitHub Actions → SSH prod → git pull + migrate + build + restart

## Bloqueos y errores

[vacío si todo OK]
```
