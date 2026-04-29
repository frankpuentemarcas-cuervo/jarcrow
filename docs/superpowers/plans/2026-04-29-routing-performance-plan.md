# Routing Fix + Performance Optimization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redirigir `/` al login, migrar Session/Cache/Queue a Redis y paralelizar las 3 llamadas ERP del endpoint stats para reducir su tiempo de ~6s a ~2s.

**Architecture:** Routing fix es un cambio de 3 líneas. Redis requiere cambio de `.env` + clear de config. El pool paralelo añade `getStatsParallel()` a `ERPNextService` y elimina las 3 llamadas secuenciales del route; los tests existentes del stats endpoint se actualizan para mockear el nuevo método único.

**Tech Stack:** Laravel 11, PHP 8.2, Pest PHP, Redis (phpredis), `Illuminate\Support\Facades\Http::pool()`

---

## File Map

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `routes/web.php` | Modificar | Routing `/` fix + stats usa `getStatsParallel()` |
| `.env` | Modificar | SESSION/CACHE/QUEUE → redis, REDIS_HOST → redis |
| `.env.example` | Modificar | Mismos cambios como referencia |
| `app/Services/ERPNextService.php` | Modificar | Añadir `getStatsParallel()` |
| `tests/Feature/RoutingTest.php` | Crear | Test redirect `/` → login |
| `tests/Feature/NominaStatsModifiedTodayTest.php` | Modificar | Reemplazar 3 mocks por `getStatsParallel()` mock |
| `tests/Feature/NominaSlipsPendientesTest.php` | Modificar | Reemplazar 3 mocks por `getStatsParallel()` mock en tests de stats |

---

## Task 1: Routing Fix — `/` redirige a login

**Files:**
- Modify: `routes/web.php:10-17`
- Create: `tests/Feature/RoutingTest.php`

- [ ] **Step 1: Crear test que verifica el redirect**

```php
<?php
// tests/Feature/RoutingTest.php

use App\Models\User;

it('redirects unauthenticated users from / to login', function () {
    $response = $this->get('/');
    $response->assertRedirect(route('login'));
});

it('redirects authenticated users from / to login then to dashboard', function () {
    $user = User::factory()->create();
    $response = $this->actingAs($user)->get('/');
    // authenticated users hitting / still get redirected to login,
    // then RedirectIfAuthenticated sends them to /dashboard
    $response->assertRedirect(route('login'));
});
```

- [ ] **Step 2: Ejecutar test — debe fallar (TDD rojo)**

```bash
cd C:\dev\agente-tareo-rrhh
php artisan test tests/Feature/RoutingTest.php
```

Expected: FAIL — respuesta es 200 (Welcome page), no 302.

- [ ] **Step 3: Aplicar routing fix en `routes/web.php`**

Localizar y reemplazar el bloque completo de la ruta `/`:

```php
// REEMPLAZAR ESTO:
Route::get('/', function () {
    return Inertia::render('Welcome', [
        'canLogin' => Route::has('login'),
        'canRegister' => Route::has('register'),
        'laravelVersion' => Application::VERSION,
        'phpVersion' => PHP_VERSION,
    ]);
});

// POR ESTO:
Route::get('/', function () {
    return redirect()->route('login');
});
```

- [ ] **Step 4: Eliminar imports no usados en `routes/web.php`**

Con el cambio anterior, `Illuminate\Foundation\Application` ya no se usa. Eliminar la línea:
```php
use Illuminate\Foundation\Application;
```

- [ ] **Step 5: Ejecutar test — debe pasar**

```bash
php artisan test tests/Feature/RoutingTest.php
```

Expected: 2 tests PASS.

- [ ] **Step 6: Ejecutar suite completa — sin regresiones**

```bash
php artisan test
```

Expected: todos los tests previos siguen PASS.

- [ ] **Step 7: Commit**

```bash
git add routes/web.php tests/Feature/RoutingTest.php
git commit -m "fix(routing): redirect / to login instead of rendering Welcome page"
```

---

## Task 2: Migrar Session, Cache y Queue a Redis

**Files:**
- Modify: `.env`
- Modify: `.env.example`

- [ ] **Step 1: Verificar que Redis está saludable en Docker**

```bash
docker exec agente-tareo-rrhh-redis-1 redis-cli ping
```

Expected: `PONG`

- [ ] **Step 2: Actualizar `.env` — cambiar los 4 valores**

Localizar y reemplazar línea por línea:

```env
# ANTES                          # DESPUÉS
SESSION_DRIVER=database    →     SESSION_DRIVER=redis
CACHE_STORE=database       →     CACHE_STORE=redis
QUEUE_CONNECTION=database  →     QUEUE_CONNECTION=redis
REDIS_HOST=127.0.0.1       →     REDIS_HOST=redis
```

El `REDIS_HOST` debe ser `redis` (nombre del servicio en `docker-compose.yml`), no `127.0.0.1` que solo resuelve en el host, no dentro del container.

- [ ] **Step 3: Actualizar `.env.example` con los mismos cambios**

Aplicar exactamente los mismos 4 cambios en `.env.example`.

- [ ] **Step 4: Limpiar config y cache dentro del container**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan config:clear
docker exec agente-tareo-rrhh-laravel.test-1 php artisan cache:clear
```

Expected: `Configuration cache cleared.` y `Application cache cleared.`

- [ ] **Step 5: Verificar que session driver es redis**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan config:show session | grep driver
```

Expected: `driver ................ redis`

- [ ] **Step 6: Verificar que Redis recibe datos (cache funcional)**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan tinker --execute="Cache::put('test_redis', 'ok', 10); echo Cache::get('test_redis');"
```

Expected: `ok`

- [ ] **Step 7: Ejecutar suite de tests — sin regresiones**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan test
```

Expected: todos los tests pasan (los Feature tests usan `RefreshDatabase` con driver de test, no se ven afectados por el cambio de session driver).

- [ ] **Step 8: Commit**

```bash
git add .env.example
git commit -m "perf(config): migrate session, cache and queue from database to redis"
```

Nota: `.env` NO se commitea (está en `.gitignore`). Solo `.env.example`.

---

## Task 3: Añadir `getStatsParallel()` a ERPNextService

**Files:**
- Modify: `app/Services/ERPNextService.php`

- [ ] **Step 1: Añadir el método `getStatsParallel()` al final de la clase (antes del `}` de cierre)**

```php
public function getStatsParallel(string $mesInicio): array
{
    $hoy = \Carbon\Carbon::now('America/Lima')->toDateString();

    $responses = Http::pool(fn ($pool) => [
        $pool->as('count')
             ->withHeaders($this->getHeaders())
             ->timeout(15)
             ->get("{$this->baseUrl}/api/resource/Salary%20Slip", [
                 'fields'            => '["name"]',
                 'filters'           => '[["start_date","=","' . $mesInicio . '"]]',
                 'limit_page_length' => 'None',
             ]),
        $pool->as('modified')
             ->withHeaders($this->getHeaders())
             ->timeout(15)
             ->get("{$this->baseUrl}/api/resource/Salary%20Slip", [
                 'fields'            => '["name","employee","modified"]',
                 'filters'           => '[["modified",">=","' . $hoy . ' 00:00:00"],["modified","<=","' . $hoy . ' 23:59:59"]]',
                 'limit_page_length' => 'None',
             ]),
        $pool->as('pendientes')
             ->withHeaders($this->getHeaders())
             ->timeout(15)
             ->get("{$this->baseUrl}/api/resource/Salary%20Slip", [
                 'fields'            => '["name","modified"]',
                 'filters'           => '[["start_date","=","' . $mesInicio . '"]]',
                 'limit_page_length' => 'None',
             ]),
    ]);

    $nominasGeneradas = $responses['count']->successful()
        ? count($responses['count']->json('data') ?? [])
        : 0;

    $modData           = $responses['modified']->successful()
        ? ($responses['modified']->json('data') ?? [])
        : [];
    $modificadosCount  = count($modData);
    $ultimaModificacion = null;
    if ($modificadosCount > 0) {
        $latest = collect($modData)->max('modified');
        $ultimaModificacion = \Carbon\Carbon::parse($latest)
            ->setTimezone('America/Lima')
            ->format('H:i:s');
    }

    $pendData       = $responses['pendientes']->successful()
        ? ($responses['pendientes']->json('data') ?? [])
        : [];
    $pendientesCount = collect($pendData)->filter(function ($slip) use ($hoy) {
        return \Carbon\Carbon::parse($slip['modified'])
            ->setTimezone('America/Lima')
            ->toDateString() !== $hoy;
    })->count();

    return [
        'nominas_generadas'       => $nominasGeneradas,
        'slips_modificados_hoy'   => $modificadosCount,
        'ultima_modificacion_hoy' => $ultimaModificacion,
        'slips_pendientes_hoy'    => $pendientesCount,
    ];
}
```

- [ ] **Step 2: Verificar que el archivo compila**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan about
```

Expected: output normal sin errores de sintaxis.

- [ ] **Step 3: Commit**

```bash
git add app/Services/ERPNextService.php
git commit -m "feat(erp): add getStatsParallel() using Http::pool() for concurrent ERP calls"
```

---

## Task 4: Actualizar tests que mockean las 3 llamadas separadas

**Files:**
- Modify: `tests/Feature/NominaStatsModifiedTodayTest.php`
- Modify: `tests/Feature/NominaSlipsPendientesTest.php`

- [ ] **Step 1: Reemplazar `NominaStatsModifiedTodayTest.php` completo**

```php
<?php

use App\Models\Colaborador;
use App\Models\User;
use App\Services\ERPNextService;

it('stats endpoint includes slips_modificados_hoy and ultima_modificacion_hoy', function () {
    $user = User::factory()->create();

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getStatsParallel')
            ->once()
            ->andReturn([
                'nominas_generadas'       => 100,
                'slips_modificados_hoy'   => 5,
                'ultima_modificacion_hoy' => '14:35:22',
                'slips_pendientes_hoy'    => 95,
            ]);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/stats');

    $response->assertOk();
    $response->assertJsonFragment([
        'slips_modificados_hoy'   => 5,
        'ultima_modificacion_hoy' => '14:35:22',
    ]);
});

it('stats endpoint returns null ultima_modificacion_hoy when no slips modified today', function () {
    $user = User::factory()->create();

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getStatsParallel')
            ->once()
            ->andReturn([
                'nominas_generadas'       => 100,
                'slips_modificados_hoy'   => 0,
                'ultima_modificacion_hoy' => null,
                'slips_pendientes_hoy'    => 0,
            ]);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/stats');

    $response->assertOk();
    $response->assertJsonFragment([
        'slips_modificados_hoy'   => 0,
        'ultima_modificacion_hoy' => null,
    ]);
});

it('stats endpoint still returns existing fields alongside new ones', function () {
    $user = User::factory()->create();

    Colaborador::create([
        'nombre'      => 'Juan',
        'apellido'    => 'Garcia',
        'employee_id' => 'EMP-0001',
        'estado'      => 'Activo',
    ]);

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getStatsParallel')
            ->once()
            ->andReturn([
                'nominas_generadas'       => 1,
                'slips_modificados_hoy'   => 1,
                'ultima_modificacion_hoy' => '09:00:00',
                'slips_pendientes_hoy'    => 0,
            ]);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/stats');

    $response->assertOk();
    $response->assertJsonStructure([
        'total_deben',
        'nominas_generadas',
        'activos',
        'no_reportado',
        'inactivos',
        'slips_modificados_hoy',
        'ultima_modificacion_hoy',
        'slips_pendientes_hoy',
    ]);
});
```

- [ ] **Step 2: Actualizar los tests de stats en `NominaSlipsPendientesTest.php`**

Localizar los dos tests que mockean el stats endpoint (los que tienen `getSalarySlipsCount`, `getSalarySlipsModifiedToday` y `getSalarySlipsPendientesHoyCount`). Reemplazar los mocks de esos dos tests únicamente:

**Test 1** — `it stats endpoint includes slips_pendientes_hoy`:
```php
it('stats endpoint includes slips_pendientes_hoy', function () {
    $user = User::factory()->create();

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getStatsParallel')
            ->once()
            ->andReturn([
                'nominas_generadas'       => 100,
                'slips_modificados_hoy'   => 5,
                'ultima_modificacion_hoy' => '14:00:00',
                'slips_pendientes_hoy'    => 95,
            ]);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/stats');

    $response->assertStatus(200);
    $response->assertJsonFragment(['slips_pendientes_hoy' => 95]);
});
```

**Test 2** — `it stats endpoint returns zero slips_pendientes_hoy when all slips updated today`:
```php
it('stats endpoint returns zero slips_pendientes_hoy when all slips updated today', function () {
    $user = User::factory()->create();

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getStatsParallel')
            ->once()
            ->andReturn([
                'nominas_generadas'       => 100,
                'slips_modificados_hoy'   => 100,
                'ultima_modificacion_hoy' => '16:00:00',
                'slips_pendientes_hoy'    => 0,
            ]);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/stats');

    $response->assertStatus(200);
    $response->assertJsonFragment(['slips_pendientes_hoy' => 0]);
});
```

Los otros 3 tests de `NominaSlipsPendientesTest` (auth guard, lista con datos, lista vacía) NO tocan el stats endpoint — no requieren cambio.

- [ ] **Step 3: Ejecutar los tests actualizados — deben fallar (TDD rojo, `getStatsParallel` no en route aún)**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan test tests/Feature/NominaStatsModifiedTodayTest.php tests/Feature/NominaSlipsPendientesTest.php
```

Expected: FAIL — el route stats aún llama los 3 métodos separados, no `getStatsParallel`.

- [ ] **Step 4: Commit de tests actualizados**

```bash
git add tests/Feature/NominaStatsModifiedTodayTest.php tests/Feature/NominaSlipsPendientesTest.php
git commit -m "test(nomina): update stats mocks to use getStatsParallel()"
```

---

## Task 5: Actualizar route `/api/nomina/stats` para usar `getStatsParallel()`

**Files:**
- Modify: `routes/web.php:91-118`

- [ ] **Step 1: Reemplazar las 3 llamadas ERP en el stats route**

Localizar:
```php
    $erpService = app(\App\Services\ERPNextService::class);
    $nominasGeneradas = $erpService->getSalarySlipsCount($mesInicio);
    $modificadosHoy = $erpService->getSalarySlipsModifiedToday();
    $pendientesCount = $erpService->getSalarySlipsPendientesHoyCount($mesInicio);

    return response()->json([
        'total_deben' => $totalDeben,
        'nominas_generadas' => $nominasGeneradas,
        'activos' => $activos,
        'no_reportado' => $noReportado,
        'inactivos' => $inactivos,
        'slips_modificados_hoy' => $modificadosHoy['count'],
        'ultima_modificacion_hoy' => $modificadosHoy['ultima_modificacion'],
        'slips_pendientes_hoy' => $pendientesCount,
    ]);
```

Reemplazar por:
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

- [ ] **Step 2: Ejecutar tests — deben pasar (TDD verde)**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan test tests/Feature/NominaStatsModifiedTodayTest.php tests/Feature/NominaSlipsPendientesTest.php
```

Expected: todos PASS.

- [ ] **Step 3: Ejecutar suite completa — sin regresiones**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan test
```

Expected: todos los tests PASS.

- [ ] **Step 4: Commit**

```bash
git add routes/web.php
git commit -m "perf(nomina): parallelize 3 ERP calls in stats endpoint via Http::pool()"
```

---

## Task 6: Rebuild y restart Vite

- [ ] **Step 1: Build del frontend**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
```

Si falla por permisos:
```bash
docker exec -u root agente-tareo-rrhh-laravel.test-1 chown -R sail:sail /var/www/html/public/build
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
```

Expected: `✓ built in XX.XXs`

- [ ] **Step 2: Reiniciar Vite dev server**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 pkill -f vite
docker exec -d agente-tareo-rrhh-laravel.test-1 bash -c "cd /var/www/html && npm run dev > /tmp/vite.log 2>&1"
```

Verificar:
```bash
docker exec agente-tareo-rrhh-laravel.test-1 cat /tmp/vite.log
```

Expected: `VITE v6.4.2  ready in XXXX ms`

- [ ] **Step 3: Commit**

No hay cambios de código — no requiere commit.

---

## Task 7: Archivo de salida del agente

**Files:**
- Create: `C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_010_routing-performance.md`

- [ ] **Step 1: Crear reporte**

```markdown
# Reporte de Ejecución: Routing Fix + Performance Optimization

**Fecha:** 2026-04-29
**Agente:** [nombre]
**Proyecto:** Agente Tareo RRHH

## Progreso de Tareas

### Routing Fix
- [x] `GET /` redirige a login (302)
- [x] Test `RoutingTest.php` creado y pasando

### Redis Migration
- [x] `.env` actualizado: SESSION_DRIVER, CACHE_STORE, QUEUE_CONNECTION, REDIS_HOST
- [x] `.env.example` actualizado
- [x] `php artisan config:clear` ejecutado
- [x] Redis verificado con `Cache::put/get`

### Performance — Http::pool()
- [x] `getStatsParallel()` añadido a `ERPNextService`
- [x] Tests actualizados para mockear `getStatsParallel()`
- [x] Stats route usa `getStatsParallel()`
- [x] Build y Vite reiniciado

## Resultado de Pruebas
[Output de `php artisan test`]
[Output de `redis-cli ping`]
[Output de verificación de Cache]
[Output del build]

## Observaciones
[Decisiones técnicas]

---
**Estado Final: COMPLETADO**
```

- [ ] **Step 2: Commit del reporte**

```bash
git add "C:/jarcrow/Trabajo/Agente-Tareo-RRHH/agentes/respuestas/2026-04-29_010_routing-performance.md"
git commit -m "docs(agente): add execution report for routing-performance"
```

---

## Verificación final

- [ ] `GET /` → 302 a `/login`
- [ ] `php artisan config:show session` muestra `driver: redis`
- [ ] `php artisan test` — todos los tests PASS
- [ ] Build sin errores, Vite corriendo
- [ ] `/api/nomina/stats` responde notablemente más rápido (3 calls paralelas)
