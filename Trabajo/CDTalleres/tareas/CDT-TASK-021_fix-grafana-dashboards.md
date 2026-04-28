---
titulo: "Fix Grafana — importar dashboards y levantar Locust target"
proyecto: CDTalleres
categoria: trabajo
prioridad: alta
estado: pendiente
automatizable: si
ia_recomendada: crowbot
prompt_preparado: false
fecha_creacion: 2026-04-25
tiempo_estimado: 1h
tags: [grafana, prometheus, monitoreo, locust]
---

## Descripción
Grafana instalado y corriendo en `http://164.92.94.47:3000` pero no muestra data porque los dashboards de infraestructura (Node Exporter, MySQL) no se importaron correctamente, y el target de Locust está DOWN.

## Contexto
El prompt 012 instaló Prometheus + Grafana. Todos los targets de node_exporter y mysqld están UP. El problema es:
1. Dashboard Node Exporter Full (ID: 1860) — requiere importación manual JSON
2. Dashboard MySQL Overview (ID: 7362) — requiere importación manual JSON
3. Target `locust:9646` está DOWN — Locust no expone métricas en ese puerto

## Tareas para el prompt 021

1. Importar dashboard 1860 (Node Exporter Full) via API Grafana con JSON completo
2. Importar dashboard 7362 (MySQL Overview) via API Grafana con JSON completo
3. Verificar que Locust está corriendo con `--web-port 9646` o configurar Prometheus exporter de Locust
4. Confirmar que métricas aparecen en Grafana para los 3 servidores

## Datos técnicos
- Grafana: `http://164.92.94.47:3000` (admin/admin o verificar password)
- Prometheus: `http://164.92.94.47:9090`
- Locust: instalado en backend `164.92.94.47`
- Scripts Locust: `c:\dev\cdtalleres\locust\` (ver prompt 013)

## Criterios de aceptación
- [ ] Dashboard Node Exporter Full visible con métricas de CPU/RAM/disco de 3 servidores
- [ ] Dashboard MySQL Overview visible con métricas de MariaDB
- [ ] Target Locust UP en Prometheus o explicación de por qué no aplica
- [ ] Grafana muestra data en tiempo real sin errores "No data"

## Prompt preparado
Requiere crear prompt 021.
