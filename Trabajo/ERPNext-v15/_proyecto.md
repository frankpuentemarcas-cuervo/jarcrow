---
nombre: ERPNext v15
cliente: shalom
categoria: trabajo
estado: activo
stack:
  backend: erpnext (frappe/python)
  frontend: erpnext (jinja/js)
  database: mariadb
  infra: docker
repo: "https://github.com/[tu-org]/erpv15"
ruta_local: "c:\\dev\\erpv15"
servidor: 178.128.181.196
dominio: erpv15-qatest.shalom.com.pe
skills_asignados:
  - erp-task-comparator
  - backend-architect
ia_principal: crowbot
fecha_inicio: 2024-01-01
ultima_actividad: 2026-04-25
---

# ERPNext v15

## Descripción
Sistema ERP de Shalom basado en ERPNext v15 (Frappe Framework). Gestión de recursos humanos, tareas, incidencias y operaciones de la empresa.

## Arquitectura
- **Runtime**: Docker containers (custom images)
- **Base de datos**: MariaDB
- **Web server**: Nginx (reverse proxy + SSL)
- **Deploy**: GitHub Actions → SSH → Docker Compose
- **Backups**: `apps.tar.gz`, `sites.tar.gz`, `db-backup.sql.gz`

## Componentes principales
| Componente | Descripción |
|---|---|
| ERPNext | ERP core v15 |
| Custom apps | Módulos personalizados |
| ZKTeco sync | Integración biométrica (script Python separado) |
| Docker stack | docker-compose.windows.yml (local) + prod |

## Skills asignados
| Skill | Uso | IA |
|---|---|---|
| erp-task-comparator | Sincronización de tareas ERP ↔ JSON local | Claude Code |
| backend-architect | Diseño de integraciones API con ERP | Claude Code |

## Accesos
- **Servidor**: `178.128.181.196` (root, SSH key: `c:\dev\erpv15\id_rsa_deploy`)
- **ERP URL**: `https://erpv15-qatest.shalom.com.pe`
- **ERP API**: Token-based auth

## Restricciones importantes
> ⚠️ **No usar `departamento` en queries de Task** — ERPNext retorna DataError 417. Solo válido en Issue DocType.

## Historial reciente
- 2026-04-25: Docker stack fixed, URL loads but WITHOUT CSS (assets issue)
- 2026-04-25: Troubleshooting DNS connectivity
- 2026-04-24: SSH deployment keys + Docker compose fixes
- 2026-04-24: Fixing deployment authentication + Nginx config
- 2026-04-24: Database restore + Docker environment setup

