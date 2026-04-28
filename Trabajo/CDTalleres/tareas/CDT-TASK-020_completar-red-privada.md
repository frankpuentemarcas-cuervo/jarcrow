---
titulo: "Completar configuración red privada interna (T4-T9)"
proyecto: CDTalleres
categoria: trabajo
prioridad: critica
estado: pendiente
automatizable: si
ia_recomendada: crowbot
prompt_preparado: true
fecha_creacion: 2026-04-25
tiempo_estimado: 1h
tags: [red-privada, mariadb, infraestructura]
---

## Descripción
Prompt 019 quedó incompleto — solo se ejecutaron T1-T3 (/etc/hosts en 3 servidores). Faltan T4-T9.

## Contexto
La red privada de DigitalOcean está activa y los hosts se resolvieron correctamente. Falta migrar la conexión DB de IP pública a IP privada y verificar que todo funciona.

## Tareas pendientes del prompt 019

| Tarea | Descripción |
|---|---|
| T4 | Cambiar `db_host` en `common_site_config.json` a `10.124.0.7` (en frontend y backend) |
| T5 | Verificar/corregir `bind-address` MariaDB a `0.0.0.0` |
| T6 | Agregar grants MySQL para `10.124.0.9` y `10.124.0.10` |
| T7 | Test conexión MySQL desde backend por IP privada |
| T8 | Reiniciar servicios Frappe |
| T9 | Comparar latencia IP privada vs IP pública |

## Contexto técnico
- Frontend: `209.38.75.235` / privada `10.124.0.10`
- Backend: `164.92.94.47` / privada `10.124.0.9`
- DB: `146.190.42.73` / privada `10.124.0.7`
- DB name: `_0646d69b639ad0ff`
- Bench: `/home/erpnext/frappe-bench` — Site: `CDTALLERES`
- SSH: `sshpass -p '.Overskull2026.m' ssh root@[IP]`

## Criterios de aceptación
- [ ] `common_site_config.json` tiene `db_host: 10.124.0.7` en frontend y backend
- [ ] MariaDB acepta conexiones desde `10.124.0.9` y `10.124.0.10`
- [ ] `mysql -h 10.124.0.7` desde backend retorna SELECT 1 OK
- [ ] Servicios Frappe reiniciados y HTTP responde
- [ ] Latencia privada < latencia pública documentada

## Prompt preparado
Prompt 019 ya existe — reanudar desde T4:
`C:\jarcrow\🏢 Trabajo\CDTalleres\agentes\prompts\2026-04-25_019_configurar-red-privada-interna.md`

Indicar al agente: "ejecutar desde T4 en adelante, T1-T3 ya completados"
