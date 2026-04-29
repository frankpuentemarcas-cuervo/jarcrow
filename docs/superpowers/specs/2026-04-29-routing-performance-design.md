# Spec: Routing Fix + Performance Optimization

**Fecha:** 2026-04-29
**Proyecto:** Agente Tareo RRHH (`C:\dev\agente-tareo-rrhh`)
**Archivo de plan:** `docs/superpowers/plans/2026-04-29-routing-performance-plan.md`

---

## Problemas

1. **Routing:** `GET /` renderiza la página Welcome en lugar de redirigir al login.
2. **Session/Cache/Queue en DB:** Cada operación de sesión (login, requests autenticados) genera queries SQL. Redis ya corre en Docker pero no se usa.
3. **Stats endpoint lento:** 3 llamadas ERP secuenciales (~2s c/u = ~6s total) al cargar `/nomina`.
4. **REDIS_HOST incorrecto:** `.env` tiene `127.0.0.1` — no resuelve dentro del container Docker donde el hostname correcto es `redis`.

---

## Sub-proyecto A: Routing Fix

### Cambio en `routes/web.php`

Reemplazar el closure de `/`:
```php
// ANTES
Route::get('/', function () {
    return Inertia::render('Welcome', [...]);
});

// DESPUÉS
Route::get('/', function () {
    return redirect()->route('login');
});
```

El middleware `RedirectIfAuthenticated` (ya presente en rutas auth de Laravel) redirige usuarios autenticados de `/login` a `/dashboard` automáticamente. No requiere cambio adicional.

---

## Sub-proyecto B: Performance

### B1 — Redis para Session, Cache y Queue

**Archivo:** `.env` (y `.env.example` como referencia)

```env
SESSION_DRIVER=redis
CACHE_STORE=redis
QUEUE_CONNECTION=redis
REDIS_HOST=redis
REDIS_PASSWORD=null
REDIS_PORT=6379
```

`REDIS_HOST=redis` porque dentro del container Docker el servicio Redis se resuelve por el nombre del servicio definido en `docker-compose.yml` (`redis`), no por `127.0.0.1`.

Después de cambiar `.env`, ejecutar dentro del container:
```bash
php artisan config:clear
php artisan cache:clear
php artisan session:table  # NO — session ya no usa DB, omitir
```

**Impacto esperado:** Login y requests autenticados eliminan las queries `select * from sessions` y `insert into sessions`. Reducción de ~50-200ms por request según carga de DB.

### B2 — Http::pool() para paralelizar llamadas ERP en stats

**Archivo:** `app/Services/ERPNextService.php`

Nuevo método `getStatsParallel(string $mesInicio): array` que ejecuta las 3 llamadas ERP simultáneamente:

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

    // count
    $nominasGeneradas = $responses['count']->successful()
        ? count($responses['count']->json('data') ?? [])
        : 0;

    // modified today
    $modData = $responses['modified']->successful()
        ? ($responses['modified']->json('data') ?? [])
        : [];
    $modificadosCount = count($modData);
    $ultimaModificacion = null;
    if ($modificadosCount > 0) {
        $latest = collect($modData)->max('modified');
        $ultimaModificacion = \Carbon\Carbon::parse($latest)
            ->setTimezone('America/Lima')
            ->format('H:i:s');
    }

    // pendientes
    $pendData = $responses['pendientes']->successful()
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

**Archivo:** `routes/web.php` — reemplazar las 3 llamadas ERP en `/api/nomina/stats` por una sola:

```php
$erpStats = $erpService->getStatsParallel($mesInicio);

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

**Impacto esperado:** Stats endpoint pasa de ~6s (3×2s secuencial) a ~2s (paralelo).

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `routes/web.php` | Ruta `/` → redirect login; stats usa `getStatsParallel()` |
| `.env` | SESSION_DRIVER, CACHE_STORE, QUEUE_CONNECTION, REDIS_HOST |
| `.env.example` | Mismos cambios como referencia |
| `app/Services/ERPNextService.php` | Añadir `getStatsParallel()` |

## Tests a actualizar

Los tests existentes que mockean los 3 métodos ERP separados (`NominaStatsModifiedTodayTest`) deben actualizarse para mockear `getStatsParallel()`. Los tests de `NominaDiffTest` y `NominaSlipsPendientesTest` no se ven afectados (usan endpoints distintos).

## Criterios de aceptación

1. `GET /` redirige a `/login` (302) para usuarios no autenticados
2. `GET /` redirige a `/dashboard` (302) para usuarios autenticados
3. `php artisan config:show session` muestra `driver: redis`
4. `/api/nomina/stats` responde en ~2s en lugar de ~6s
5. Tests pasan: `php artisan test` — suite completa
6. `php artisan tinker` — `Cache::put('test', 1); Cache::get('test')` retorna `1` (confirma Redis)

## Archivo de salida del agente

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_010_routing-performance.md
```
