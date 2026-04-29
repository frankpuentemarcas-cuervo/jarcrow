---
fecha: 2026-04-29
agente_id: "010"
descripcion: "routing-fix-redis-migration-http-pool-performance"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "C:\\jarcrow\\Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-29_010_routing-performance.md"
---

# Fase 10: Routing Fix + Performance Optimization

## Contexto

Proyecto en `C:\dev\agente-tareo-rrhh`. Tres problemas a resolver:

1. `GET /` muestra la página Welcome en lugar de redirigir al login
2. Session/Cache/Queue usan driver `database` — Redis ya corre en Docker pero no se usa
3. El endpoint `/api/nomina/stats` hace 3 llamadas ERP secuenciales (~6s total) en lugar de paralelas

**Stack:** Laravel 11, PHP 8.2, Pest PHP, Redis (phpredis), Vue 3, Docker/Sail

---

## Instrucciones para el Agente

### Ejecutar el Plan de Implementación

Lee y ejecuta el plan completo paso a paso:

```
C:\jarcrow\docs\superpowers\plans\2026-04-29-routing-performance-plan.md
```

7 tareas con código completo. **No saltear ningún step — incluye TDD.**

### Resumen de cambios

#### Task 1 — Routing Fix

**`routes/web.php`** — reemplazar closure de `/`:
```php
Route::get('/', function () {
    return redirect()->route('login');
});
```
Eliminar `use Illuminate\Foundation\Application;` (ya no se usa).

**`tests/Feature/RoutingTest.php`** — crear con 2 tests Pest que verifican redirect 302.

#### Task 2 — Redis Migration

**`.env`** — cambiar 4 valores:
```
SESSION_DRIVER=redis
CACHE_STORE=redis
QUEUE_CONNECTION=redis
REDIS_HOST=redis   ← era 127.0.0.1, incorrecto en Docker
```
**`.env.example`** — mismos cambios.

Post-cambio dentro del container:
```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan config:clear
docker exec agente-tareo-rrhh-laravel.test-1 php artisan cache:clear
```

Verificación:
```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan config:show session | grep driver
# Expected: driver ................ redis

docker exec agente-tareo-rrhh-laravel.test-1 php artisan tinker --execute="Cache::put('test_redis', 'ok', 10); echo Cache::get('test_redis');"
# Expected: ok
```

#### Task 3 — `getStatsParallel()` en ERPNextService

**`app/Services/ERPNextService.php`** — añadir al final de la clase:
- Método `getStatsParallel(string $mesInicio): array`
- Usa `Http::pool()` para ejecutar simultáneamente:
  - `count`: GET Salary Slip con `start_date=$mesInicio` → count
  - `modified`: GET Salary Slip con `modified=hoy` → count + ultima hora
  - `pendientes`: GET Salary Slip con `start_date=$mesInicio` → PHP filter excluye modified=hoy → count
- Retorna: `['nominas_generadas', 'slips_modificados_hoy', 'ultima_modificacion_hoy', 'slips_pendientes_hoy']`

El código completo está en el plan (Task 3, Step 1).

#### Task 4 — Actualizar tests

**`tests/Feature/NominaStatsModifiedTodayTest.php`** — reemplazar archivo completo. Los 3 tests ahora mockean `getStatsParallel()` en lugar de los 3 métodos separados. Código completo en el plan (Task 4, Step 1).

**`tests/Feature/NominaSlipsPendientesTest.php`** — actualizar solo los 2 tests del stats endpoint para mockear `getStatsParallel()`. Los otros 3 tests no cambian. Código en el plan (Task 4, Step 2).

#### Task 5 — Actualizar route stats

**`routes/web.php`** — reemplazar las 3 llamadas ERP separadas por:
```php
$erpService = app(\App\Services\ERPNextService::class);
$erpStats   = $erpService->getStatsParallel($mesInicio);

return response()->json([
    'total_deben'             => $totalDeben,
    'nominas_generadas'       => $erpStats['nominas_generadas'],
    'activos'                 => $activos,
    'no_reportado'            => $noReportado,
    'inactivos'               => $inactivos,
    'slips_modificados_hoy'   => $erpStats['slips_modificados_hoy'],
    'ultima_modificacion_hoy' => $erpStats['ultima_modificacion_hoy'],
    'slips_pendientes_hoy'    => $erpStats['slips_pendientes_hoy'],
]);
```

#### Task 6 — Build + Vite

```bash
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
docker exec agente-tareo-rrhh-laravel.test-1 pkill -f vite
docker exec -d agente-tareo-rrhh-laravel.test-1 bash -c "cd /var/www/html && npm run dev > /tmp/vite.log 2>&1"
```

---

## Criterios de Éxito

1. `GET /` → 302 a `/login`
2. `php artisan config:show session` muestra `driver: redis`
3. `Cache::put/get` funciona (Redis operativo)
4. `php artisan test` → todos los tests PASS (incluyendo `RoutingTest`)
5. Build sin errores, Vite corriendo

---

## Archivo de Salida

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_010_routing-performance.md
```

Incluir: checklist `[x]`, output de tests, output de verificación Redis, output del build, estado final.
