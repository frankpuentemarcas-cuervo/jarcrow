# Salary Slips Modificados Hoy — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar una 3ra card en `/nomina` con el conteo de Salary Slips cuyo campo `modified` sea del día actual (zona horaria Lima).

**Architecture:** Nuevo método `getSalarySlipsModifiedToday()` en `ERPNextService` hace una sola llamada a ERPNext. El endpoint `/api/nomina/stats` existente llama ese método y añade dos campos al response. `Nomina.vue` cambia de grid 2→3 columnas y renderiza la nueva card amber.

**Tech Stack:** Laravel 11, PHP 8.2, Pest PHP, Vue 3 Composition API, Tailwind CSS, Carbon, ERPNext REST API

---

## File Map

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `app/Services/ERPNextService.php` | Modificar | Añadir `getSalarySlipsModifiedToday()` |
| `routes/web.php` | Modificar | Añadir los 2 nuevos campos al response de `/api/nomina/stats` |
| `resources/js/Pages/Nomina.vue` | Modificar | Grid 3 cols + 3ra card amber + stats ref ampliado |
| `tests/Feature/NominaStatsModifiedTodayTest.php` | Crear | Tests Pest del nuevo comportamiento del endpoint stats |

---

## Task 1: Método `getSalarySlipsModifiedToday()` en ERPNextService

**Files:**
- Modify: `app/Services/ERPNextService.php`

- [ ] **Step 1: Abrir `app/Services/ERPNextService.php` y añadir el método después de `getSalarySlipEmployees()`, antes del cierre `}` de la clase**

```php
public function getSalarySlipsModifiedToday(): array
{
    try {
        $hoy = \Carbon\Carbon::now('America/Lima')->toDateString();

        $response = Http::withHeaders($this->getHeaders())
            ->timeout(15)
            ->get("{$this->baseUrl}/api/resource/Salary%20Slip", [
                'fields'           => '["name","employee","modified"]',
                'filters'          => '[["modified",">=","' . $hoy . ' 00:00:00"],["modified","<=","' . $hoy . ' 23:59:59"]]',
                'limit_page_length' => 'None',
            ]);

        if ($response->successful()) {
            $data = $response->json('data') ?? [];

            if (empty($data)) {
                return ['count' => 0, 'ultima_modificacion' => null];
            }

            $ultimaModificacion = collect($data)
                ->max('modified');

            $hora = \Carbon\Carbon::parse($ultimaModificacion)
                ->setTimezone('America/Lima')
                ->format('H:i:s');

            return [
                'count'               => count($data),
                'ultima_modificacion' => $hora,
            ];
        }

        Log::error("ERPNext Error fetching slips modified today: " . $response->body());
        return ['count' => 0, 'ultima_modificacion' => null];
    } catch (\Exception $e) {
        Log::error("ERPNext Exception getSalarySlipsModifiedToday: " . $e->getMessage());
        return ['count' => 0, 'ultima_modificacion' => null];
    }
}
```

- [ ] **Step 2: Verificar que el archivo compila**

```bash
cd C:\dev\agente-tareo-rrhh
php artisan about
```

Expected: output normal sin errores de sintaxis.

- [ ] **Step 3: Commit**

```bash
git add app/Services/ERPNextService.php
git commit -m "feat(erp): add getSalarySlipsModifiedToday() to ERPNextService"
```

---

## Task 2: Test del nuevo comportamiento del endpoint `/api/nomina/stats`

**Files:**
- Create: `tests/Feature/NominaStatsModifiedTodayTest.php`

- [ ] **Step 1: Crear el archivo de test**

```php
<?php

use App\Models\Colaborador;
use App\Models\User;
use App\Services\ERPNextService;

it('stats endpoint includes slips_modificados_hoy and ultima_modificacion_hoy', function () {
    $user = User::factory()->create();

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getSalarySlipsCount')
            ->once()
            ->andReturn(100);

        $mock->shouldReceive('getSalarySlipsModifiedToday')
            ->once()
            ->andReturn(['count' => 5, 'ultima_modificacion' => '14:35:22']);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/stats');

    $response->assertStatus(200);
    $response->assertJsonFragment([
        'slips_modificados_hoy'   => 5,
        'ultima_modificacion_hoy' => '14:35:22',
    ]);
});

it('stats endpoint returns null ultima_modificacion_hoy when no slips modified today', function () {
    $user = User::factory()->create();

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getSalarySlipsCount')
            ->once()
            ->andReturn(100);

        $mock->shouldReceive('getSalarySlipsModifiedToday')
            ->once()
            ->andReturn(['count' => 0, 'ultima_modificacion' => null]);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/stats');

    $response->assertStatus(200);
    $response->assertJsonFragment([
        'slips_modificados_hoy'   => 0,
        'ultima_modificacion_hoy' => null,
    ]);
});

it('stats endpoint still returns existing fields alongside new ones', function () {
    $user = User::factory()->create();

    Colaborador::create([
        'nombre'      => 'Juan',
        'apellido'    => 'García',
        'employee_id' => 'EMP-0001',
        'estado'      => 'Activo',
    ]);

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getSalarySlipsCount')->once()->andReturn(1);
        $mock->shouldReceive('getSalarySlipsModifiedToday')->once()
            ->andReturn(['count' => 1, 'ultima_modificacion' => '09:00:00']);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/stats');

    $response->assertStatus(200);
    $response->assertJsonStructure([
        'total_deben',
        'nominas_generadas',
        'activos',
        'no_reportado',
        'inactivos',
        'slips_modificados_hoy',
        'ultima_modificacion_hoy',
    ]);
});
```

- [ ] **Step 2: Ejecutar los tests — deben fallar (TDD rojo)**

```bash
cd C:\dev\agente-tareo-rrhh
php artisan test tests/Feature/NominaStatsModifiedTodayTest.php
```

Expected: FAIL — `getSalarySlipsModifiedToday` no existe en el response de stats / método no mockeado correctamente.

- [ ] **Step 3: Commit del test en rojo**

```bash
git add tests/Feature/NominaStatsModifiedTodayTest.php
git commit -m "test(nomina): add failing tests for slips_modificados_hoy in stats endpoint"
```

---

## Task 3: Modificar `/api/nomina/stats` en `routes/web.php`

**Files:**
- Modify: `routes/web.php` (líneas 91-113)

- [ ] **Step 1: Reemplazar el bloque completo de la ruta `/api/nomina/stats`**

Localizar:
```php
Route::get('/api/nomina/stats', function () {
    $mesInicio = \Carbon\Carbon::now('America/Lima')->startOfMonth()->toDateString();
    $mesFin = \Carbon\Carbon::now('America/Lima')->endOfMonth()->toDateString();

    $activos = \App\Models\Colaborador::where('estado', 'Activo')->count();
    $noReportado = \App\Models\Colaborador::where('estado', 'No Reportado')->count();
    $inactivos = \App\Models\Colaborador::where('estado', 'Inactivo')
        ->whereBetween('fecha_de_relevo', [$mesInicio, $mesFin])
        ->count();

    $totalDeben = $activos + $noReportado + $inactivos;

    $erpService = app(\App\Services\ERPNextService::class);
    $nominasGeneradas = $erpService->getSalarySlipsCount($mesInicio);

    return response()->json([
        'total_deben' => $totalDeben,
        'nominas_generadas' => $nominasGeneradas,
        'activos' => $activos,
        'no_reportado' => $noReportado,
        'inactivos' => $inactivos,
    ]);
})->middleware(['auth', 'verified']);
```

Reemplazar por:
```php
Route::get('/api/nomina/stats', function () {
    $mesInicio = \Carbon\Carbon::now('America/Lima')->startOfMonth()->toDateString();
    $mesFin    = \Carbon\Carbon::now('America/Lima')->endOfMonth()->toDateString();

    $activos     = \App\Models\Colaborador::where('estado', 'Activo')->count();
    $noReportado = \App\Models\Colaborador::where('estado', 'No Reportado')->count();
    $inactivos   = \App\Models\Colaborador::where('estado', 'Inactivo')
        ->whereBetween('fecha_de_relevo', [$mesInicio, $mesFin])
        ->count();

    $totalDeben  = $activos + $noReportado + $inactivos;

    $erpService        = app(\App\Services\ERPNextService::class);
    $nominasGeneradas  = $erpService->getSalarySlipsCount($mesInicio);
    $modificadosHoy    = $erpService->getSalarySlipsModifiedToday();

    return response()->json([
        'total_deben'             => $totalDeben,
        'nominas_generadas'       => $nominasGeneradas,
        'activos'                 => $activos,
        'no_reportado'            => $noReportado,
        'inactivos'               => $inactivos,
        'slips_modificados_hoy'   => $modificadosHoy['count'],
        'ultima_modificacion_hoy' => $modificadosHoy['ultima_modificacion'],
    ]);
})->middleware(['auth', 'verified']);
```

- [ ] **Step 2: Ejecutar tests — deben pasar (TDD verde)**

```bash
php artisan test tests/Feature/NominaStatsModifiedTodayTest.php
```

Expected: 3 tests PASS.

- [ ] **Step 3: Ejecutar suite completa — sin regresiones**

```bash
php artisan test
```

Expected: todos los tests previos siguen PASS.

- [ ] **Step 4: Commit**

```bash
git add routes/web.php
git commit -m "feat(nomina): add slips_modificados_hoy to /api/nomina/stats response"
```

---

## Task 4: Actualizar `Nomina.vue` — Grid 3 cols + card amber

**Files:**
- Modify: `resources/js/Pages/Nomina.vue`

**IMPORTANTE:** Cargar skill antes de modificar este archivo:
```
C:\dev\agente-tareo-rrhh\skill\ui-ux-designer\skill.md
```

- [ ] **Step 1: Ampliar el objeto `stats` en `<script setup>` para incluir los dos nuevos campos**

Localizar:
```js
const stats = ref({
    total_deben: 0,
    nominas_generadas: 0,
    activos: 0,
    no_reportado: 0,
    inactivos: 0,
});
```

Reemplazar por:
```js
const stats = ref({
    total_deben: 0,
    nominas_generadas: 0,
    activos: 0,
    no_reportado: 0,
    inactivos: 0,
    slips_modificados_hoy: 0,
    ultima_modificacion_hoy: null,
});
```

- [ ] **Step 2: Cambiar el grid de 2 a 3 columnas en el `<template>`**

Localizar:
```html
<div class="mb-6 grid grid-cols-1 gap-6 md:grid-cols-2">
```

Reemplazar por:
```html
<div class="mb-6 grid grid-cols-1 gap-6 md:grid-cols-3">
```

- [ ] **Step 3: Añadir la 3ra card amber inmediatamente después del cierre de la 2da card (la verde de "Total generadas")**

La 2da card termina con `</div>` después de la sección del badge de diferencia. Localizar el cierre de esa card:
```html
                            </div>

                        </div>
```
(el primer `</div>` cierra la card verde, el segundo cierra el grid)

Insertar la nueva card entre ambos cierres:
```html
                            </div>

                            <!-- Card: Salary Slips actualizados hoy -->
                            <div class="flex flex-col items-center justify-center rounded-lg border border-amber-200 bg-gradient-to-br from-amber-50 to-yellow-50 p-8 dark:border-amber-800 dark:from-gray-700 dark:to-gray-600">
                                <p class="mb-2 text-center text-sm font-medium text-gray-600 dark:text-gray-300">
                                    Salary Slips actualizados hoy
                                </p>
                                <p
                                    class="text-center text-6xl font-bold transition-all duration-300"
                                    :class="loading ? 'text-gray-400 dark:text-gray-500' : (stats.slips_modificados_hoy > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-gray-400 dark:text-gray-500')"
                                >
                                    {{ loading ? '...' : stats.slips_modificados_hoy }}
                                </p>
                                <div v-if="!loading" class="mt-4 text-center">
                                    <span v-if="stats.slips_modificados_hoy > 0" class="text-sm text-gray-500 dark:text-gray-400">
                                        Último: {{ stats.ultima_modificacion_hoy }}
                                    </span>
                                    <span v-else class="text-sm text-gray-400 dark:text-gray-500">
                                        Ninguno hoy
                                    </span>
                                </div>
                            </div>

                        </div>
```

- [ ] **Step 4: Verificar que el frontend compila sin errores**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
```

Expected: `✓ built in XX.XXs` con `Nomina-XXXXXXXX.js` en la lista de assets.

Si el build falla por permisos en `public/build`, corregir primero:
```bash
docker exec -u root agente-tareo-rrhh-laravel.test-1 chown -R sail:sail /var/www/html/public/build
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
```

- [ ] **Step 5: Commit**

```bash
git add resources/js/Pages/Nomina.vue
git commit -m "feat(nomina): add third card showing salary slips modified today"
```

---

## Task 5: Crear archivo de salida del agente

**Files:**
- Create: `C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_008_salary-slip-modificados-hoy.md`

- [ ] **Step 1: Crear el reporte con el estado real de cada tarea**

```markdown
# Reporte de Ejecución: Salary Slips Modificados Hoy

**Fecha:** 2026-04-29
**Agente:** [nombre]
**Proyecto:** Agente Tareo RRHH

## Progreso de Tareas

### Backend
- [x] Método `getSalarySlipsModifiedToday()` añadido a `ERPNextService`
- [x] Response de `/api/nomina/stats` incluye `slips_modificados_hoy` y `ultima_modificacion_hoy`

### Tests
- [x] `tests/Feature/NominaStatsModifiedTodayTest.php` creado y pasando (3 tests)
- [x] Suite completa sin regresiones

### Frontend
- [x] `stats` ref ampliado con `slips_modificados_hoy` y `ultima_modificacion_hoy`
- [x] Grid cambiado a `md:grid-cols-3`
- [x] 3ra card amber implementada con estados count > 0 y count = 0
- [x] Build verificado

## Resultado de Pruebas

[Output de `php artisan test tests/Feature/NominaStatsModifiedTodayTest.php`]
[Output de `php artisan test` — suite completa]
[Resultado del build]

## Observaciones

[Decisiones técnicas durante la implementación]

---
**Estado Final: COMPLETADO**
```

- [ ] **Step 2: Commit del reporte**

```bash
git add "C:/jarcrow/Trabajo/Agente-Tareo-RRHH/agentes/respuestas/2026-04-29_008_salary-slip-modificados-hoy.md"
git commit -m "docs(agente): add execution report for salary-slip-modificados-hoy"
```

---

## Verificación final

- [ ] `php artisan test` — todos los tests pasan
- [ ] Build Docker sin errores
- [ ] En `/nomina`: 3 cards visibles en pantalla mediana/grande
- [ ] Card amber muestra número en amber cuando `slips_modificados_hoy > 0`, con sub-texto "Último: HH:MM:SS"
- [ ] Card amber muestra número en gris cuando = 0, con sub-texto "Ninguno hoy"
- [ ] Botón "Actualizar" refresca las 3 cards simultáneamente
