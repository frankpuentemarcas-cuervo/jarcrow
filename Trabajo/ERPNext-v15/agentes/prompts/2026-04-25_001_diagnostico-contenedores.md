---
fecha: 2026-04-25
agente_id: "001"
descripcion: diagnostico-contenedores-web-no-carga
proyecto: ERPNext-v15
ia_destino: antigravity
tipo: debug
estado: completado
falla: ""
archivo_salida: "c:\\dev\\erpv15\\diagnostico-results.md"
---

# Diagnóstico — ERPNext v15 Docker: Web No Carga

## Contexto para el agente

Proyecto ERPNext v15 (Overskull para Shalom). Stack Docker en producción en servidor 178.128.181.196. Todos los contenedores están corriendo. DNS del dominio `erpv15-qatest.shalom.com.pe` ya propagado apuntando a 178.128.181.196. Sin embargo al abrir el dominio en el browser no carga nada.

**Causa probable identificada**: El archivo `nginx.conf` tiene `server_name erp15docker.shalomcontrol.com` (dominio anterior) pero el DNS activo es `erpv15-qatest.shalom.com.pe`. El certificado SSL también es para el dominio anterior.

### Servidor

| Campo | Valor |
|---|---|
| IP | 178.128.181.196 |
| Usuario SSH | root |
| Llave SSH | `c:\dev\erpv15\id_rsa_deploy` |
| Dominio DNS activo | erpv15-qatest.shalom.com.pe |
| Ruta proyecto en servidor | a determinar (buscar docker-compose.yml) |

### Stack Docker (nombres de contenedores)

`erpnext-nginx-proxy`, `erpnext-frontend`, `erpnext-backend`, `erpnext-websocket`, `erpnext-database`, `erpnext-redis-cache`, `erpnext-redis-queue`, `erpnext-queue-short`, `erpnext-queue-long`, `erpnext-scheduler`

---

## ⚠️ REGLA CRÍTICA — Reporte de bloqueos

**SIEMPRE, ante cualquier error, bloqueo o impedimento:**

1. Genera el archivo de salida con lo que tengas hasta ese momento
2. Documenta en `## Bloqueos y errores`: qué intentaste, error EXACTO, alternativas, qué se necesita
3. **Nunca termines sin generar el archivo de salida.** Aunque sea parcial.

---

## Tareas a ejecutar

Conectar al servidor:
```bash
ssh -i c:\dev\erpv15\id_rsa_deploy -o StrictHostKeyChecking=no root@178.128.181.196
```

### 1. Estado general de contenedores

```bash
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Documentar cuáles están `Up`, cuáles `Exited` o `Restarting`.

### 2. Logs de nginx-proxy (causa más probable)

```bash
docker logs erpnext-nginx-proxy --tail 50 2>&1
docker logs erpnext-frontend --tail 30 2>&1
docker logs erpnext-backend --tail 30 2>&1
```

### 3. Verificar nginx.conf activo dentro del contenedor

```bash
docker exec erpnext-nginx-proxy cat /etc/nginx/conf.d/erpnext.conf 2>/dev/null | grep -E "(server_name|listen|ssl_cert)"
docker exec erpnext-nginx-proxy nginx -t 2>&1
```

### 4. Verificar que puertos 80 y 443 están expuestos

```bash
ss -tlnp | grep -E "(80|443)"
curl -sv http://localhost 2>&1 | head -30
curl -svk https://localhost 2>&1 | head -30
```

### 5. Verificar respuesta con dominio correcto

```bash
curl -svk -H "Host: erpv15-qatest.shalom.com.pe" https://localhost 2>&1 | head -40
curl -sv http://erpv15-qatest.shalom.com.pe 2>&1 | head -20
```

### 6. Verificar backend Frappe responde internamente

```bash
docker exec erpnext-backend curl -s http://localhost:8000 2>&1 | head -20
docker exec erpnext-frontend curl -s http://localhost:8080 2>&1 | head -20
```

### 7. Verificar sitio Frappe configurado

```bash
docker exec erpnext-backend bash -c "ls /home/frappe/frappe-bench/sites/" 2>/dev/null
docker exec erpnext-backend bash -c "cat /home/frappe/frappe-bench/sites/common_site_config.json" 2>/dev/null
```

---

## Archivo de salida

**Crear al terminar (aunque sea parcial):**
```
c:\dev\erpv15\diagnostico-results.md
```

### Estructura obligatoria

```markdown
# Diagnóstico ERPNext v15 Docker — YYYY-MM-DD HH:MM

## Estado de contenedores

| Contenedor | Estado | Puertos |
|---|---|---|
| erpnext-nginx-proxy | Up/Exited | 0.0.0.0:80->80, 443->443 |
| ... | | |

## server_name en nginx.conf activo
[valor encontrado]

## nginx -t resultado
[output]

## Respuesta HTTP/HTTPS
- http://localhost: [HTTP code]
- https://localhost: [HTTP code / error SSL]
- con Host erpv15-qatest.shalom.com.pe: [resultado]

## Backend Frappe responde internamente
- backend:8000: [✅/❌]
- frontend:8080: [✅/❌]

## Sitio Frappe configurado
- Sites encontrados: [lista]
- common_site_config.json: [contenido relevante]

## Logs de error relevantes
[errores de nginx-proxy, frontend, backend]

## Diagnóstico
[Conclusión del agente: ¿cuál es la causa raíz?]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien]
```
