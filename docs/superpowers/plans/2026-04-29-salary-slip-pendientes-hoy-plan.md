# Salary Slips Pendientes de Actualizar Hoy — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar en la card amber un badge con el count de Salary Slips del mes no actualizados hoy, con tabla expandible lazy que lista cada slip pendiente (Slip ID, Employee ID, Nombre, Última modif.).

**Architecture:** Dos nuevos métodos en `ERPNextService` (uno para count en stats, otro para lista lazy). Stats endpoint expone `slips_pendientes_hoy`. Nuevo endpoint `/api/nomina/slips-pendientes` devuelve la lista completa. `Nomina.vue` añade badge amber + tabla con el mismo patrón de `fetchDiff`.

**Tech Stack:** Laravel 11, PHP 8.2, Pest PHP, Vue 3 Composition API, Tailwind CSS, Carbon, ERPNext REST API

---

## File Map

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `app/Services/ERPNextService.php` | Modificar | Añadir `getSalarySlipsPendientesHoyCount()` y `getSalarySlipsPendientesHoy()` |
| `routes/web.php` | Modificar | Añadir `slips_pendientes_hoy` a stats + nuevo `GET /api/nomina/slips-pendientes` |
| `resources/js/Pages/Nomina.vue` | Modificar | Badge amber, tabla expandible, nuevos refs, reset en refreshStats |
| `tests/Feature/NominaSlipsPendientesTest.php` | Crear | Tests Pest para stats field + endpoint lazy |

---

## Task 1: Dos métodos en `ERPNextService`

**Files:**
- Modify: `app/Services/ERPNextService.php`

- [ ] **Step 1: Añadir `getSalarySlipsPendientesHoyCount()` al final de la clase (antes del `}` de cierre)**

```php
public function getSalarySlipsPendientesHoyCount(string $mesInicio): int
{
    try {
        $hoy = \Carbon\Carbon::now('America/Lima')->toDateString();

        $response = Http::withHeaders($this->getHeaders())
            ->timeout(15)
            ->get("{$this->baseUrl}/api/resource/Salary%20Slip", [
                'fields'            => '["name","modified"]',
                'filters'           => '[["start_date","=","' . $mesInicio . '"]]',
                'limit_page_length' => 'None',
            ]);

        if ($response->successful()) {
            $data = $response->json('data') ?? [];

            return collect($data)->filter(function ($slip) use ($hoy) {
                $fechaModified = \Carbon\Carbon::parse($slip['modified'])
                    ->setTimezone('America/Lima')
                    ->toDateString();
                return $fechaModified !== $hoy;
            })->count();
        }

        Log::error("ERPNext Error getSalarySlipsPendientesHoyCount: " . $response->body());
        return 0;
    } catch (\Exception $e) {
        Log::error("ERPNext Exception getSalarySlipsPendientesHoyCount: " . $e->getMessage());
        return 0;
    }
}
```

- [ ] **Step 2: Añadir `getSalarySlipsPendientesHoy()` inmediatamente después**

```php
public function getSalarySlipsPendientesHoy(string $mesInicio): array
{
    try {
        $hoy = \Carbon\Carbon::now('America/Lima')->toDateString();

        $response = Http::withHeaders($this->getHeaders())
            ->timeout(15)
            ->get("{$this->baseUrl}/api/resource/Salary%20Slip", [
                'fields'            => '["name","employee","employee_name","modified"]',
                'filters'           => '[["start_date","=","' . $mesInicio . '"]]',
                'limit_page_length' => 'None',
            ]);

        if ($response->successful()) {
            $data = $response->json('data') ?? [];

            return collect($data)
                ->filter(function ($slip) use ($hoy) {
                    $fechaModified = \Carbon\Carbon::parse($slip['modified'])
                        ->setTimezone('America/Lima')
                        ->toDateString();
                    return $fechaModified !== $hoy;
                })
                ->map(function ($slip) {
                    $modified = \Carbon\Carbon::parse($slip['modified'])
                        ->setTimezone('America/Lima');
                    return [
                        'name'          => $slip['name'],
                        'employee'      => $slip['employee'],
                        'employee_name' => $slip['employee_name'] ?? '',
                        'modified_fecha'=> $modified->toDateString(),
                        'modified_hora' => $modified->format('H:i:s'),
                    ];
                })
                ->values()
                ->toArray();
        }

        Log::error("ERPNext Error getSalarySlipsPendientesHoy: " . $response->body());
        return [];
    } catch (\Exception $e) {
        Log::error("ERPNext Exception getSalarySlipsPendientesHoy: " . $e->getMessage());
        return [];
    }
}
```

- [ ] **Step 3: Verificar que el archivo compila**

```bash
cd C:\dev\agente-tareo-rrhh
php artisan about
```

Expected: output normal sin errores de sintaxis.

- [ ] **Step 4: Commit**

```bash
git add app/Services/ERPNextService.php
git commit -m "feat(erp): add getSalarySlipsPendientesHoyCount() and getSalarySlipsPendientesHoy()"
```

---

## Task 2: Tests para el nuevo campo en stats y el endpoint lazy

**Files:**
- Create: `tests/Feature/NominaSlipsPendientesTest.php`

- [ ] **Step 1: Crear el archivo de test**

```php
<?php

use App\Models\User;
use App\Services\ERPNextService;

it('stats endpoint includes slips_pendientes_hoy', function () {
    $user = User::factory()->create();

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getSalarySlipsCount')->once()->andReturn(100);
        $mock->shouldReceive('getSalarySlipsModifiedToday')->once()
            ->andReturn(['count' => 5, 'ultima_modificacion' => '14:00:00']);
        $mock->shouldReceive('getSalarySlipsPendientesHoyCount')->once()->andReturn(95);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/stats');

    $response->assertStatus(200);
    $response->assertJsonFragment(['slips_pendientes_hoy' => 95]);
});

it('stats endpoint returns zero slips_pendientes_hoy when all slips updated today', function () {
    $user = User::factory()->create();

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getSalarySlipsCount')->once()->andReturn(100);
        $mock->shouldReceive('getSalarySlipsModifiedToday')->once()
            ->andReturn(['count' => 100, 'ultima_modificacion' => '16:00:00']);
        $mock->shouldReceive('getSalarySlipsPendientesHoyCount')->once()->andReturn(0);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/stats');

    $response->assertStatus(200);
    $response->assertJsonFragment(['slips_pendientes_hoy' => 0]);
});

it('slips-pendientes endpoint returns 401 when unauthenticated', function () {
    $response = $this->getJson('/api/nomina/slips-pendientes');
    $response->assertStatus(302);
});

it('slips-pendientes endpoint returns list of pending slips', function () {
    $user = User::factory()->create();

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getSalarySlipsPendientesHoy')->once()->andReturn([
            [
                'name'           => 'SAL-SLIP-00042',
                'employee'       => 'EMP-0001',
                'employee_name'  => 'Juan García',
                'modified_fecha' => '2026-04-28',
                'modified_hora'  => '09:14:05',
            ],
        ]);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/slips-pendientes');

    $response->assertStatus(200);
    $response->assertJsonCount(1);
    $response->assertJsonFragment([
        'name'           => 'SAL-SLIP-00042',
        'employee'       => 'EMP-0001',
        'employee_name'  => 'Juan García',
        'modified_fecha' => '2026-04-28',
        'modified_hora'  => '09:14:05',
    ]);
});

it('slips-pendientes endpoint returns empty array when all slips updated today', function () {
    $user = User::factory()->create();

    $this->mock(ERPNextService::class, function ($mock) {
        $mock->shouldReceive('getSalarySlipsPendientesHoy')->once()->andReturn([]);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/slips-pendientes');

    $response->assertStatus(200);
    $response->assertJson([]);
});
```

- [ ] **Step 2: Ejecutar tests — deben fallar (TDD rojo)**

```bash
php artisan test tests/Feature/NominaSlipsPendientesTest.php
```

Expected: FAIL — `slips_pendientes_hoy` no en response, ruta no existe.

- [ ] **Step 3: Commit del test en rojo**

```bash
git add tests/Feature/NominaSlipsPendientesTest.php
git commit -m "test(nomina): add failing tests for slips_pendientes_hoy and /api/nomina/slips-pendientes"
```

---

## Task 3: Modificar `routes/web.php`

**Files:**
- Modify: `routes/web.php`

- [ ] **Step 1: Modificar el bloque de `/api/nomina/stats` — añadir la llamada y el campo**

Localizar:
```php
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
```

Reemplazar por:
```php
    $erpService        = app(\App\Services\ERPNextService::class);
    $nominasGeneradas  = $erpService->getSalarySlipsCount($mesInicio);
    $modificadosHoy    = $erpService->getSalarySlipsModifiedToday();
    $pendientesCount   = $erpService->getSalarySlipsPendientesHoyCount($mesInicio);

    return response()->json([
        'total_deben'             => $totalDeben,
        'nominas_generadas'       => $nominasGeneradas,
        'activos'                 => $activos,
        'no_reportado'            => $noReportado,
        'inactivos'               => $inactivos,
        'slips_modificados_hoy'   => $modificadosHoy['count'],
        'ultima_modificacion_hoy' => $modificadosHoy['ultima_modificacion'],
        'slips_pendientes_hoy'    => $pendientesCount,
    ]);
```

- [ ] **Step 2: Añadir el endpoint `GET /api/nomina/slips-pendientes` después del cierre de `/api/nomina/diff`**

Localizar el cierre del endpoint `/api/nomina/diff`:
```php
})->middleware(['auth', 'verified']);
```
(el que pertenece al diff — búscalo por el contexto de `$sinNomina`)

Agregar inmediatamente después:
```php
Route::get('/api/nomina/slips-pendientes', function () {
    $mesInicio = \Carbon\Carbon::now('America/Lima')->startOfMonth()->toDateString();

    $lista = app(\App\Services\ERPNextService::class)
        ->getSalarySlipsPendientesHoy($mesInicio);

    return response()->json($lista);
})->middleware(['auth', 'verified']);
```

- [ ] **Step 3: Ejecutar tests — deben pasar (TDD verde)**

```bash
php artisan test tests/Feature/NominaSlipsPendientesTest.php
```

Expected: 5 tests PASS.

- [ ] **Step 4: Ejecutar suite completa — sin regresiones**

```bash
php artisan test
```

Expected: todos los tests previos siguen PASS.

- [ ] **Step 5: Commit**

```bash
git add routes/web.php
git commit -m "feat(nomina): add slips_pendientes_hoy to stats and GET /api/nomina/slips-pendientes"
```

---

## Task 4: Actualizar `Nomina.vue`

**Files:**
- Modify: `resources/js/Pages/Nomina.vue`

**IMPORTANTE:** Cargar skill antes de modificar:
```
C:\dev\agente-tareo-rrhh\skill\ui-ux-designer\skill.md
```

- [ ] **Step 1: Añadir `slips_pendientes_hoy` al objeto `stats` ref**

Localizar:
```js
    slips_modificados_hoy: 0,
    ultima_modificacion_hoy: null,
});
```

Reemplazar por:
```js
    slips_modificados_hoy: 0,
    ultima_modificacion_hoy: null,
    slips_pendientes_hoy: 0,
});
```

- [ ] **Step 2: Añadir tres nuevos refs después de `showDiff`**

Localizar:
```js
const showDiff = ref(false);
```

Agregar después:
```js
const pendientesSlips = ref([]);
const loadingPendientes = ref(false);
const showPendientes = ref(false);
```

- [ ] **Step 3: Añadir función `fetchPendientes` después de `fetchDiff`**

Localizar el cierre de `fetchDiff`:
```js
};
```
(el que cierra `fetchDiff`)

Agregar después:
```js
const fetchPendientes = async () => {
    if (showPendientes.value) {
        showPendientes.value = false;
        return;
    }
    if (pendientesSlips.value.length > 0) {
        showPendientes.value = true;
        return;
    }
    loadingPendientes.value = true;
    try {
        const response = await fetch('/api/nomina/slips-pendientes');
        pendientesSlips.value = await response.json();
        showPendientes.value = true;
    } catch (error) {
        console.error('Error fetching pendientes:', error);
    } finally {
        loadingPendientes.value = false;
    }
};
```

- [ ] **Step 4: Añadir reset en `refreshStats`**

Localizar:
```js
    missingEmployees.value = [];
    showDiff.value = false;
```

Reemplazar por:
```js
    missingEmployees.value = [];
    showDiff.value = false;
    pendientesSlips.value = [];
    showPendientes.value = false;
```

- [ ] **Step 5: Añadir badge amber en la card amber, debajo del sub-texto "Último / Ninguno hoy"**

Localizar el cierre de la card amber:
```html
                                </div>
                            </div>
```
(el `</div>` que cierra `v-if="!loading"` y luego el que cierra la card)

Reemplazar esos dos cierres por:
```html
                                </div>
                                <div v-if="!loading" class="mt-4 text-center">
                                    <button
                                        v-if="stats.slips_pendientes_hoy > 0"
                                        type="button"
                                        @click="fetchPendientes"
                                        :disabled="loadingPendientes"
                                        class="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-700 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-amber-900 dark:text-amber-300 dark:hover:bg-amber-800"
                                    >
                                        <span v-if="loadingPendientes">Buscando...</span>
                                        <span v-else>
                                            {{ stats.slips_pendientes_hoy }} pendientes
                                            {{ showPendientes ? '▲' : '▼' }} Ver detalle
                                        </span>
                                    </button>
                                </div>
                            </div>
```

- [ ] **Step 6: Añadir tabla expandible de pendientes después del bloque `</transition>` del diff**

Localizar:
```html
                        </transition>

                        <div class="mt-6 rounded-lg border border-blue-200
```

Insertar entre ambos:
```html
                        </transition>

                        <transition name="fade">
                            <div
                                v-if="showPendientes && pendientesSlips.length > 0"
                                class="mt-6 overflow-hidden rounded-lg border border-amber-200 bg-white dark:border-amber-800 dark:bg-gray-900"
                            >
                                <div class="flex items-center justify-between border-b border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-800 dark:bg-amber-900/30">
                                    <h3 class="text-sm font-semibold text-amber-800 dark:text-amber-300">
                                        Salary Slips pendientes de actualizar ({{ pendientesSlips.length }})
                                    </h3>
                                    <button
                                        type="button"
                                        @click="showPendientes = false"
                                        class="text-lg leading-none text-amber-400 hover:text-amber-600 dark:hover:text-amber-200"
                                    >
                                        x
                                    </button>
                                </div>
                                <div class="overflow-x-auto">
                                    <table class="w-full text-sm">
                                        <thead class="bg-gray-50 dark:bg-gray-800">
                                            <tr>
                                                <th class="px-4 py-2 text-left text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Slip ID</th>
                                                <th class="px-4 py-2 text-left text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Employee ID</th>
                                                <th class="px-4 py-2 text-left text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Nombre</th>
                                                <th class="px-4 py-2 text-left text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Última modif.</th>
                                            </tr>
                                        </thead>
                                        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
                                            <tr
                                                v-for="slip in pendientesSlips"
                                                :key="slip.name"
                                                class="hover:bg-gray-50 dark:hover:bg-gray-800/50"
                                            >
                                                <td class="px-4 py-2 font-mono text-gray-700 dark:text-gray-300">{{ slip.name }}</td>
                                                <td class="px-4 py-2 font-mono text-gray-700 dark:text-gray-300">{{ slip.employee }}</td>
                                                <td class="px-4 py-2 text-gray-800 dark:text-gray-200">{{ slip.employee_name }}</td>
                                                <td class="px-4 py-2 text-gray-500 dark:text-gray-400">{{ slip.modified_fecha }} {{ slip.modified_hora }}</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </transition>

                        <div class="mt-6 rounded-lg border border-blue-200
```

- [ ] **Step 7: Verificar build**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
```

Expected: `✓ built in XX.XXs`. Si falla por permisos:
```bash
docker exec -u root agente-tareo-rrhh-laravel.test-1 chown -R sail:sail /var/www/html/public/build
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
```

- [ ] **Step 8: Reiniciar Vite dev server para reflejar cambios**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 pkill -f vite
docker exec -d agente-tareo-rrhh-laravel.test-1 bash -c "cd /var/www/html && npm run dev > /tmp/vite.log 2>&1"
```

- [ ] **Step 9: Commit**

```bash
git add resources/js/Pages/Nomina.vue
git commit -m "feat(nomina): add pending slips badge and expandable table in amber card"
```

---

## Task 5: Archivo de salida del agente

**Files:**
- Create: `C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_009_salary-slip-pendientes-hoy.md`

- [ ] **Step 1: Crear el reporte con estado real de cada tarea**

```markdown
# Reporte de Ejecución: Salary Slips Pendientes de Actualizar Hoy

**Fecha:** 2026-04-29
**Agente:** [nombre]
**Proyecto:** Agente Tareo RRHH

## Progreso de Tareas

### Backend
- [x] `getSalarySlipsPendientesHoyCount()` añadido a `ERPNextService`
- [x] `getSalarySlipsPendientesHoy()` añadido a `ERPNextService`
- [x] `slips_pendientes_hoy` en response de `/api/nomina/stats`
- [x] `GET /api/nomina/slips-pendientes` registrado en `routes/web.php`

### Tests
- [x] `tests/Feature/NominaSlipsPendientesTest.php` creado y pasando (5 tests)
- [x] Suite completa sin regresiones

### Frontend
- [x] `slips_pendientes_hoy` en stats ref
- [x] Nuevos refs `pendientesSlips`, `loadingPendientes`, `showPendientes`
- [x] `fetchPendientes()` con caché local implementado
- [x] Reset en `refreshStats()`
- [x] Badge amber en card amber (solo cuando > 0)
- [x] Tabla expandible con 4 columnas
- [x] Build y Vite reiniciado

## Resultado de Pruebas
[Output de `php artisan test tests/Feature/NominaSlipsPendientesTest.php`]
[Output de `php artisan test`]
[Output del build]

## Observaciones
[Decisiones técnicas]

---
**Estado Final: COMPLETADO**
```

- [ ] **Step 2: Commit del reporte**

```bash
git add "C:/jarcrow/Trabajo/Agente-Tareo-RRHH/agentes/respuestas/2026-04-29_009_salary-slip-pendientes-hoy.md"
git commit -m "docs(agente): add execution report for salary-slip-pendientes-hoy"
```

---

## Verificación final

- [ ] `php artisan test` — todos los tests pasan
- [ ] Build sin errores, Vite reiniciado
- [ ] Card amber muestra badge "X pendientes ▼ Ver detalle" cuando `slips_pendientes_hoy > 0`
- [ ] Badge no visible cuando = 0
- [ ] Click badge → tabla con Slip ID, Employee ID, Nombre, Última modif.
- [ ] Toggle: click cierra, `×` cierra
- [ ] "Actualizar" limpia caché y estado de pendientes
