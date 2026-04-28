---
titulo: "Tuning Gunicorn workers + MariaDB parámetros"
proyecto: CDTalleres
categoria: trabajo
prioridad: alta
estado: pendiente
automatizable: si
ia_recomendada: crowbot
prompt_preparado: false
fecha_creacion: 2026-04-25
tiempo_estimado: 1h
tags: [gunicorn, mariadb, performance, tuning]
---

## Descripción
Gunicorn corre con 3 workers cuando debería tener 5 (2*CPU+1). MariaDB tiene parámetros por defecto sin optimizar para carga de producción ERPNext.

## Contexto
Detectado en prompt 005 (profiling). El backend tiene 2 CPU cores → fórmula = (2*2)+1 = 5 workers. Con 3 workers se desperdicia capacidad de procesamiento paralelo. MariaDB aún no tiene tuning específico para el patrón de uso de ERPNext.

## Tareas para el prompt 022

### Gunicorn
- Cambiar workers en supervisor config de 3 → 5
- Ajustar `worker_timeout` a 120s (ERPNext recomienda)
- Reiniciar y verificar 5 procesos activos

### MariaDB
- Verificar `innodb_buffer_pool_size` (actual: 2GB — evaluar si es correcto para el servidor)
- Ajustar `max_connections` (evaluar carga real vs límite actual)
- Verificar `innodb_lock_wait_timeout` (bajar a 30s para fallar rápido en lugar de bloquear)
- Habilitar `slow_query_log` permanente con umbral 1s
- Revisar `query_cache` (deprecado en MariaDB 10.6+, confirmar estado)

## Datos técnicos
- Backend: `164.92.94.47` — supervisor config en `/etc/supervisor/conf.d/`
- DB: `146.190.42.73` — MariaDB config en `/etc/mysql/`
- Bench: `/home/erpnext/frappe-bench`

## Criterios de aceptación
- [ ] `ps aux | grep gunicorn` muestra 5 workers
- [ ] `SHOW VARIABLES LIKE 'slow_query_log'` retorna ON
- [ ] `innodb_lock_wait_timeout` ≤ 30
- [ ] Reinicio limpio sin errores en supervisor

## Prompt preparado
Requiere crear prompt 022.
