---
fecha: 2026-04-25
agente_id: "001"
prompt_ref: "prompts/2026-04-25_001_verificar-conectividad.md"
estado: completado
archivo_fuente: "c:\\dev\\cdtalleres\\server-audit-results.md"
---

# Respuesta Agente 001 — Auditoría de Servidores CDTalleres

## Hallazgos críticos

### Infraestructura (los 3 servidores son idénticos — snapshot)
| Servidor | IP | OS | CPU | RAM | Disco | ERPNext |
|---|---|---|---|---|---|---|
| Backend | 164.92.94.47 | Ubuntu 20.04 | 2 cores | 4GB | 87% (67GB) | 13.9.2 |
| DB | 165.232.130.222 | Ubuntu 20.04 | 2 cores | 4GB | 87% (67GB) | 13.9.2 |
| Frontend | 209.38.75.235 | Ubuntu 20.04 | 2 cores | 4GB | 87% (67GB) | 13.9.2 |

- **Versión**: ERPNext 13.9.2 / Frappe 13.9.1 (NO es v15 como se asumía — es v13)
- **Ruta bench**: `/home/erpnext/frappe-bench`
- **Site**: `CDTALLERES`
- **Apps extra**: `notification 0.0.1`, `scanpda 0.0.1`
- **developer_mode**: 1 (activo en producción — problema)
- **Redis**: 3 instancias locales (puertos 11000, 12000, 13000)

### Bloqueadores para separación de servicios
1. **MariaDB bind-address = 127.0.0.1** → rechaza conexiones externas, Backend no puede conectar a DB server
2. **Disco al 87%** en los 3 servidores — riesgo inmediato
3. Todos los servicios corren en los 3 nodos (aún sin separar)

### Acciones requeridas (en orden)
1. Limpiar disco (logs, backups viejos)
2. Cambiar `bind-address` en servidor DB
3. Crear usuario MariaDB con acceso remoto desde IP del Backend
4. Separar servicios por servidor
