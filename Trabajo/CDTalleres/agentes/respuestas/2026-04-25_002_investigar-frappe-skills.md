---
fecha: 2026-04-25
agente_id: "002"
prompt_ref: "prompts/2026-04-25_002_investigar-frappe-skills.md"
estado: completado
archivo_fuente: "c:\\dev\\cdtalleres\\frappe-skills-evaluation.md"
---

# Respuesta Agente 002 — Investigar Frappe Skills

## 📊 Tabla Resumen de Skills Relevantes

| Skill | Relevancia | Propósito Principal | Caso de Uso en CDTalleres |
|-------|------------|---------------------|---------------------------|
| **frappe-ops-performance** | **CRÍTICA** | Tuning de MariaDB, Redis, Gunicorn y Profiling | Optimización de locks en `tabSeries` y dimensionamiento de workers |
| **frappe-agent-debugger** | **ALTA** | Debugging de errores, análisis de logs y tracebacks | Identificar cuellos de botella no visibles en logs estándar |
| **frappe-core-database** | **ALTA** | Operaciones de DB, queries, locks y transacciones | Analizar comportamiento de queries pesadas y manejo de bloqueos |
| **frappe-ops-deployment** | **ALTA** | Configuración de Nginx, Supervisor, Docker y SSL | Soporte para migración a arquitectura de 3 capas |
| **frappe-ops-bench** | **MEDIA** | Gestión de sitios y comandos bench | Mantenimiento de nuevos nodos y configuración multi-tenancy |
| **frappe-core-cache** | **MEDIA** | Redis caching y distributed locking | Optimizar uso de caché para reducir carga en DB |
| **frappe-syntax-query-builder** | **MEDIA** | Construcción de queries optimizadas con `frappe.qb` | Refactorizar queries ineficientes detectadas en profiling |

---

## 🔍 Análisis de Skills Clave

### frappe-ops-performance — CRÍTICA
- **Caso de uso**: Habilitar slow_query_log, analizar con mysqldumpslow, tuning innodb
- **Técnicas clave**: `innodb_buffer_pool_size`, `innodb_flush_method = O_DIRECT`, workers = `(2 * CPU_CORES) + 1`
- **Instalar**: Sí

### frappe-agent-debugger — ALTA
- **Caso de uso**: Monitorear `logs/web.log` y `logs/worker.log`, tracing con `frappe.logger()`
- **Técnicas clave**: `bench console`, inspección en vivo
- **Instalar**: Sí

### frappe-core-database — ALTA
- **Caso de uso**: Anti-patrones N+1, reducir hits a DB con `frappe.db.get_cached_value`
- **Técnicas clave**: `frappe.db.sql` parametrizado para queries complejas
- **Instalar**: Sí

### frappe-ops-deployment — ALTA
- **Caso de uso**: Separar DB, Backend y Frontend en 3 servidores
- **Técnicas clave**: `supervisor.conf` para múltiples workers, hardening Nginx
- **Instalar**: Sí

---

## 🕵️ Hallazgos sobre tabSeries y Naming Series

1. **Mecanismo**: `frappe.model.naming.getseries` usa `SELECT ... FOR UPDATE` → lock de fila por serie
2. **Problema**: Alta concurrencia de documentos = contención en `tabSeries` → esperas en cola
3. **Soluciones identificadas**:
   - `autoname: hash` o UUID (v15+) → elimina dependencia de `tabSeries` para DocTypes de alto volumen
   - Aumentar `innodb_buffer_pool_size` + SSD → reduce tiempo que `tabSeries` permanece bloqueada
   - Evitar lógica pesada en `autoname`

---

## 🛠️ Plan de Instalación

```bash
# Desde raíz del repo clonado: c:\dev\cdtalleres\Frappe_Claude_Skill_Package\

# Prioridad Alta
cp -r skills/source/ops/frappe-ops-performance ~/.claude/skills/
cp -r skills/source/agents/frappe-agent-debugger ~/.claude/skills/
cp -r skills/source/core/frappe-core-database ~/.claude/skills/
cp -r skills/source/ops/frappe-ops-deployment ~/.claude/skills/

# Prioridad Media
cp -r skills/source/ops/frappe-ops-bench ~/.claude/skills/
cp -r skills/source/core/frappe-core-cache ~/.claude/skills/
cp -r skills/source/syntax/frappe-syntax-query-builder ~/.claude/skills/
```

## Orden de uso recomendado para diagnóstico

1. `frappe-ops-performance` — habilitar logs de queries lentas, revisar config MariaDB
2. `frappe-agent-debugger` — monitorear latencias en tiempo real
3. `frappe-core-database` — auditar queries que tocan `tabSeries`
