---
nombre: CDTalleres
cliente: shalom
categoria: trabajo
estado: activo
stack:
  backend: erpnext (frappe/python)
  frontend: erpnext (jinja/js)
  database: mariadb
  infra: digitalocean-vps (3 servidores)
repo: ""
ruta_local: "c:\\dev\\cdtalleres"
servidores:
  backend: 164.92.94.47
  database: 165.232.130.222
  frontend: 209.38.75.235
dominio: por-definir
skills_asignados:
  - frappe-ops-performance
  - frappe-ops-deployment
  - frappe-ops-bench
  - frappe-agent-debugger
  - frappe-core-database
  - frappe-syntax-query-builder
ia_principal: crowbot
fecha_inicio: 2026-04-25
ultima_actividad: 2026-04-25
---

# CDTalleres

## Descripción
Sistema ERPNext para gestión de talleres de Shalom. Actualmente presenta problemas de performance no detectables en logs. Se sospecha que la tabla `tabSeries` (Naming Series) genera saturación.

## Arquitectura actual (3 servidores desde snapshot)

| Rol | IP | Usuario | Auth |
|---|---|---|---|
| **Backend** (Gunicorn/Workers) | `164.92.94.47` | root | password |
| **Base de datos** (MariaDB) | `165.232.130.222` | root | password |
| **Frontend/App** (Nginx + assets) | `209.38.75.235` | root | password |

> Todos los servidores fueron creados desde el mismo snapshot del servidor original.

## Problema a investigar
- **Síntoma**: Demora en el servidor no perceptible en logs
- **Sospecha principal**: Saturación por `tabSeries` (tabla de Naming Series)
- **`tabSeries`**: Tabla de Frappe que controla el nombrado automático de DocTypes (numeración correlativa). Cada documento nuevo hace un `SELECT FOR UPDATE` en esta tabla, generando locks.
- **Estrategia**: Dividir servicios en 3-5 servidores para aislar componentes y encontrar el cuello de botella

## Skills asignados (Frappe Claude Skill Package)
| Skill | Uso | Fuente |
|---|---|---|
| frappe-ops-performance | Tuning MariaDB, Redis, Gunicorn workers, profiling queries | GitHub: OpenAEC-Foundation |
| frappe-ops-deployment | Config Nginx, Supervisor, Docker, SSL, hardening | GitHub: OpenAEC-Foundation |
| frappe-ops-bench | Comandos bench, gestión de sites, multi-tenancy | GitHub: OpenAEC-Foundation |
| frappe-agent-debugger | Debug errores, bench console, tracebacks, log files | GitHub: OpenAEC-Foundation |
| frappe-core-database | Operaciones de base de datos, queries, locks | GitHub: OpenAEC-Foundation |
| frappe-syntax-query-builder | Queries con frappe.qb, joins, aggregation | GitHub: OpenAEC-Foundation |

## Fases de investigación
1. ✅ Servidores creados desde snapshot (por Frank)
2. 🔜 Verificar conectividad a los 3 servidores
3. 🔜 Evaluar estado actual de cada servidor
4. 🔜 Configurar separación de servicios (DB ↔ Backend ↔ Frontend)
5. 🔜 Instalar herramientas de profiling
6. 🔜 Ejecutar pruebas de carga
7. 🔜 Analizar `tabSeries` locks
