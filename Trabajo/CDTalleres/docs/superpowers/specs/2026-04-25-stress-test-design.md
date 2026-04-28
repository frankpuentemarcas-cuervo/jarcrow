# Stress Test Diagnóstico CDTalleres — Diseño

**Fecha:** 2026-04-25
**Proyecto:** CDTalleres (ERPNext v13.9.2 / Frappe 13.9.1)
**Objetivo:** Forzar colapso bajo alta concurrencia para identificar cuello de botella invisible (tabSeries locks, Gunicorn queue, MariaDB connections, Redis)

---

## Contexto

El profiling (prompt 005) identificó:
- Backend (164.92.94.47) con `db_host=127.0.0.1` — errores silenciosos de conexión
- Gunicorn workers=3 en 2 cores (subóptimo)
- tabSeries con contadores >100k en ACC-GLE y MAT-SLE — candidato a lock contention bajo carga
- 162 series activas — alto riesgo de `SELECT FOR UPDATE` concurrentes

El stress test corre **antes** de aplicar el fix del prompt 010, para tener baseline del sistema con bugs actuales.

---

## Arquitectura del Stack de Prueba

```
Backend (164.92.94.47) — nodo orquestador
├── Locust 2.x
│   ├── 100–200 usuarios virtuales concurrentes
│   ├── Ramp-up: 10 usuarios/segundo hasta 200
│   ├── Target: https://cdtalleres-copia.shalom.com.pe
│   └── Web UI: http://164.92.94.47:8089
│
├── Prometheus
│   ├── :9090 — scraping cada 5s
│   ├── locust-exporter :9646 → métricas HTTP Locust
│   ├── mysqld_exporter :9104 en DB (146.190.42.73)
│   └── node_exporter :9100 en los 3 servidores
│
└── Grafana :3000
    ├── Dashboard: Locust Load (RPS, latencia p50/p95/p99, error rate)
    ├── Dashboard: MariaDB (connections, locks, InnoDB waits, tabSeries)
    └── Dashboard: Sistema (CPU/RAM/IO/network por servidor)

DB (146.190.42.73)
└── mysqld_exporter (systemd service)

Frontend (209.38.75.235)
└── node_exporter (systemd service)
```

---

## DocTypes Atacados

| DocType | Endpoint REST | Operación | Peso |
|---|---|---|---|
| Purchase Order | `/api/resource/Purchase Order` | POST (crear) | 30% |
| Purchase Invoice | `/api/resource/Purchase Invoice` | POST (crear) | 25% |
| Orden de Trabajo 2 | `/api/resource/Orden de Trabajo 2` | POST (crear) | 25% |
| Solicitud de Pagos | `/api/resource/Solicitud de Pagos` | POST (crear) | 20% |
| Cualquiera | GET lista | GET | intercalado |

Cada POST crea un documento mínimo válido con los campos obligatorios del DocType. Las creaciones fuerzan uso de `tabSeries` → `SELECT FOR UPDATE` — el candidato principal a contención.

---

## Parámetros del Test

| Parámetro | Valor |
|---|---|
| Usuarios máximos | 200 |
| Ramp-up rate | 10 usuarios/segundo |
| Duración total | 15 minutos |
| Think time entre requests | 0–1s (aleatorio) |
| Auth | API Key + API Secret de usuario ERPNext dedicado |
| Host target | https://cdtalleres-copia.shalom.com.pe |
| Locust corre en | 164.92.94.47 (red interna → Frontend) |

---

## Métricas Capturadas

### HTTP (Locust)
- Requests por segundo (RPS)
- Latencia p50, p95, p99 por endpoint
- Error rate y tipos de error (5xx, timeouts, connection refused)
- Failures acumuladas

### MariaDB (mysqld_exporter)
- `mysql_global_status_threads_connected` — conexiones activas
- `mysql_global_status_innodb_row_lock_waits` — lock waits InnoDB
- `mysql_global_status_innodb_row_lock_time_avg` — tiempo promedio de lock
- `mysql_info_schema_innodb_trx_*` — transacciones bloqueadas
- Query personalizada: `SELECT * FROM tabSeries ORDER BY current DESC LIMIT 10` — contadores en tiempo real

### Sistema — 3 servidores (node_exporter)
- CPU usage por core
- RAM usage y swap
- Disk I/O (await, utilization)
- Network connections (ESTABLISHED, TIME_WAIT)
- Load average

---

## Indicadores de Colapso

| Síntoma | Causa probable |
|---|---|
| Error rate >10% con HTTP 500 | Gunicorn workers saturados |
| Latencia p99 >10s | tabSeries lock contention |
| `threads_connected` >150 | MariaDB max_connections alcanzado |
| `innodb_row_lock_waits` creciente | SELECT FOR UPDATE en tabSeries |
| CPU Backend >90% | Workers Python agotados |
| CPU DB >80% | Query pressure MariaDB |
| HTTP 502/504 | Nginx timeout → Gunicorn muerto |

---

## Prompts del Agente (secuencia)

| Prompt | Descripción | Output |
|---|---|---|
| 011 | Instalar node_exporter en 3 servidores + mysqld_exporter en DB | `c:\dev\cdtalleres\exporters-install-results.md` |
| 012 | Instalar Prometheus + Grafana en Backend, configurar datasource y dashboards | `c:\dev\cdtalleres\prometheus-grafana-results.md` |
| 013 | Instalar Locust, crear script de carga, crear usuario API en ERPNext | `c:\dev\cdtalleres\locust-setup-results.md` |
| 014 | Ejecutar stress test 15 min, capturar métricas, generar reporte diagnóstico | `c:\dev\cdtalleres\stress-test-results.md` |

---

## Seguridad

- El test corre contra servidor de **copia** (`cdtalleres-copia.shalom.com.pe`) — NO producción
- Usuario API dedicado con permisos mínimos (solo los 4 DocTypes)
- Grafana protegido con credenciales (admin / CDTStress2026)
- Prometheus no expuesto a internet (bind 127.0.0.1, acceso via Grafana)
- node_exporter bind a IP privada (acceso solo desde Backend)

---

## Criterio de Éxito del Diagnóstico

Al terminar el prompt 014, el reporte debe identificar con evidencia de métricas:
1. **Qué falló primero** (Gunicorn / MariaDB / Redis / Red)
2. **A qué concurrencia** colapsó (N usuarios)
3. **Qué métrica lo confirma** (lock waits, HTTP 5xx, CPU spike)
4. **Recomendación priorizada** para el siguiente fix
