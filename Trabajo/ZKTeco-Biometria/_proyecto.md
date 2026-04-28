---
nombre: ZKTeco Biometría
cliente: shalom
categoria: trabajo
estado: activo
stack:
  backend: python
  frontend: none
  database: none (API-based)
  infra: local script
repo: ""
ruta_local: "c:\\dev\\erpv15\\zkteco_historial.py"
servidor: ""
dominio: ""
skills_asignados:
  - backend-architect
  - unit-testing
ia_principal: claude-code
fecha_inicio: 2026-04-01
ultima_actividad: 2026-04-22
---

# ZKTeco Biometría

## Descripción
Script Python para sincronizar datos de asistencia biométrica (dispositivos ZKTeco) con ERPNext v15 Employee Checkin.

## Arquitectura
- **Script**: `zkteco_historial.py` (Python, standalone)
- **Dispositivo**: ZKTeco (ZKLib para comunicación)
- **Destino**: ERPNext v15 API → Employee Checkin DocType
- **Auth**: HMAC authentication vía `ERPNextClient`
- **Lookup**: Matcheo por campo `biometrico_id` en Employee DocType

## Funcionalidades
| Comando | Descripción |
|---|---|
| `sync` | Sincroniza datos del día actual |
| `range` | Sincroniza rango de fechas |
| `-test` | Modo prueba con fecha específica |

## Skills asignados
| Skill | Uso | IA |
|---|---|---|
| backend-architect | Diseño de integración biométrica ↔ ERP | Claude Code |
| unit-testing | Tests del script de sincronización | Claude Code |

## Notas técnicas
- El script filtra registros localmente antes de enviar a ERP
- Manejo de duplicados integrado
- Output optimizado para consola Windows (encoding)
- Búsqueda de empleado: `biometrico_id` → `employee_name`
