# Nómina Diff — Empleados sin Nómina Generada — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cuando existe diferencia entre nóminas esperadas y generadas, mostrar qué empleados específicos carecen de Salary Slip en ERPNext para el mes en curso.

**Architecture:** Nuevo método en `ERPNextService` obtiene los `employee` IDs que ya tienen Salary Slip. Un nuevo endpoint `/api/nomina/diff` hace diff contra la tabla local `colaboradores`. `Nomina.vue` expone el badge como botón clickeable que carga y muestra la lista expandible con caché local.

**Tech Stack:** Laravel 11, PHP 8.2, Pest PHP, Vue 3 Composition API, Tailwind CSS, ERPNext REST API, Carbon

---

## File Map

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `app/Services/ERPNextService.php` | Modificar | Añadir `getSalarySlipEmployees()` |
| `routes/web.php` | Modificar | Añadir `GET /api/nomina/diff` |
| `resources/js/Pages/Nomina.vue` | Modificar | Badge clickeable + tabla expandible + caché |
| `tests/Feature/NominaDiffTest.php` | Crear | Tests del endpoint `/api/nomina/diff` |

---

## Task 1: Método `getSalarySlipEmployees()` en ERPNextService

**Files:**
- Modify: `app/Services/ERPNextService.php`

- [ ] **Step 1: Abrir `app/Services/ERPNextService.php` y añadir el método al final de la clase, antes del cierre `}`**

```php
public function getSalarySlipEmployees(string $startDate): array
{
    try {
        $response = Http::withHeaders($this->getHeaders())
            ->timeout(15)
            ->get("{$this->baseUrl}/api/resource/Salary%20Slip", [
                'fields' => '["employee"]',
                'filters' => '[["start_date","=","' . $startDate . '"]]',
                'limit_page_length' => 'None'
            ]);

        if ($response->successful()) {
            return array_column($response->json('data') ?? [], 'employee');
        }

        Log::error("ERPNext Error fetching salary slip employees: " . $response->body());
        return [];
    } catch (\Exception $e) {
        Log::error("ERPNext Exception getSalarySlipEmployees: " . $e->getMessage());
        return [];
    }
}
```

- [ ] **Step 2: Verificar que el archivo compila sin errores**

```bash
cd C:\dev\agente-tareo-rrhh
php artisan about
```

Expected: sin errores de sintaxis, output normal de Laravel.

- [ ] **Step 3: Commit**

```bash
git add app/Services/ERPNextService.php
git commit -m "feat(erp): add getSalarySlipEmployees() to ERPNextService"
```

---

## Task 2: Test del endpoint `/api/nomina/diff`

**Files:**
- Create: `tests/Feature/NominaDiffTest.php`

- [ ] **Step 1: Crear el archivo de test**

```php
<?php

use App\Models\Colaborador;
use App\Models\User;
use App\Services\ERPNextService;
use Carbon\Carbon;
use Illuminate\Support\Facades\Http;

it('returns 401 when unauthenticated', function () {
    $response = $this->getJson('/api/nomina/diff');
    $response->assertStatus(302); // redirect to login
});

it('returns empty array when all employees have salary slips', function () {
    $user = User::factory()->create();

    $mesInicio = Carbon::now('America/Lima')->startOfMonth()->toDateString();
    $mesFin    = Carbon::now('America/Lima')->endOfMonth()->toDateString();

    Colaborador::factory()->create([
        'employee_id' => 'EMP-0001',
        'nombre'      => 'Juan',
        'apellido'    => 'García',
        'estado'      => 'Activo',
    ]);

    $this->mock(ERPNextService::class, function ($mock) use ($mesInicio) {
        $mock->shouldReceive('getSalarySlipEmployees')
            ->once()
            ->with($mesInicio)
            ->andReturn(['EMP-0001']);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/diff');

    $response->assertStatus(200);
    $response->assertJson([]);
});

it('returns employees missing salary slips', function () {
    $user = User::factory()->create();

    $mesInicio = Carbon::now('America/Lima')->startOfMonth()->toDateString();

    Colaborador::factory()->create([
        'employee_id' => 'EMP-0001',
        'nombre'      => 'Juan',
        'apellido'    => 'García',
        'estado'      => 'Activo',
    ]);
    Colaborador::factory()->create([
        'employee_id' => 'EMP-0002',
        'nombre'      => 'María',
        'apellido'    => 'López',
        'estado'      => 'No Reportado',
    ]);

    $this->mock(ERPNextService::class, function ($mock) use ($mesInicio) {
        $mock->shouldReceive('getSalarySlipEmployees')
            ->once()
            ->with($mesInicio)
            ->andReturn(['EMP-0001']); // solo EMP-0001 tiene nómina
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/diff');

    $response->assertStatus(200);
    $response->assertJsonCount(1);
    $response->assertJsonFragment([
        'employee_id' => 'EMP-0002',
        'nombre'      => 'María',
        'apellido'    => 'López',
        'estado'      => 'No Reportado',
    ]);
});

it('includes inactivos with fecha_de_relevo in current month', function () {
    $user = User::factory()->create();

    $mesInicio    = Carbon::now('America/Lima')->startOfMonth()->toDateString();
    $fechaRelevo  = Carbon::now('America/Lima')->toDateString();

    Colaborador::factory()->create([
        'employee_id'    => 'EMP-0010',
        'nombre'         => 'Carlos',
        'apellido'       => 'Ruiz',
        'estado'         => 'Inactivo',
        'fecha_de_relevo'=> $fechaRelevo,
    ]);

    $this->mock(ERPNextService::class, function ($mock) use ($mesInicio) {
        $mock->shouldReceive('getSalarySlipEmployees')
            ->once()
            ->with($mesInicio)
            ->andReturn([]); // nadie tiene nómina
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/diff');

    $response->assertStatus(200);
    $response->assertJsonFragment(['employee_id' => 'EMP-0010']);
});

it('excludes inactivos with fecha_de_relevo outside current month', function () {
    $user = User::factory()->create();

    $mesInicio      = Carbon::now('America/Lima')->startOfMonth()->toDateString();
    $fechaFuera     = Carbon::now('America/Lima')->subMonth()->toDateString();

    Colaborador::factory()->create([
        'employee_id'    => 'EMP-0020',
        'nombre'         => 'Ana',
        'apellido'       => 'Torres',
        'estado'         => 'Inactivo',
        'fecha_de_relevo'=> $fechaFuera,
    ]);

    $this->mock(ERPNextService::class, function ($mock) use ($mesInicio) {
        $mock->shouldReceive('getSalarySlipEmployees')
            ->once()
            ->with($mesInicio)
            ->andReturn([]);
    });

    $response = $this->actingAs($user)->getJson('/api/nomina/diff');

    $response->assertStatus(200);
    $response->assertJson([]);
});
```

- [ ] **Step 2: Ejecutar los tests para verificar que fallan (TDD — rojo)**

```bash
cd C:\dev\agente-tareo-rrhh
php artisan test tests/Feature/NominaDiffTest.php
```

Expected: FAIL — `Route [/api/nomina/diff] not defined` o similar.

- [ ] **Step 3: Commit del test en rojo**

```bash
git add tests/Feature/NominaDiffTest.php
git commit -m "test(nomina): add failing tests for /api/nomina/diff endpoint"
```

---

## Task 3: Endpoint `GET /api/nomina/diff` en `routes/web.php`

**Files:**
- Modify: `routes/web.php`

- [ ] **Step 1: Añadir el endpoint en `routes/web.php` después de la ruta `/api/nomina/stats`**

Localizar la línea:
```php
})->middleware(['auth', 'verified']);
```
(el cierre de `/api/nomina/stats`), y agregar inmediatamente después:

```php
Route::get('/api/nomina/diff', function () {
    $mesInicio = \Carbon\Carbon::now('America/Lima')->startOfMonth()->toDateString();
    $mesFin    = \Carbon\Carbon::now('America/Lima')->endOfMonth()->toDateString();

    $empleadosDeben = \App\Models\Colaborador::query()
        ->where(function ($q) use ($mesInicio, $mesFin) {
            $q->whereIn('estado', ['Activo', 'No Reportado'])
              ->orWhere(function ($q2) use ($mesInicio, $mesFin) {
                  $q2->where('estado', 'Inactivo')
                     ->whereBetween('fecha_de_relevo', [$mesInicio, $mesFin]);
              });
        })
        ->select('employee_id', 'nombre', 'apellido', 'estado')
        ->get();

    $conNomina = app(\App\Services\ERPNextService::class)
        ->getSalarySlipEmployees($mesInicio);

    $sinNomina = $empleadosDeben
        ->filter(fn($c) => !in_array($c->employee_id, $conNomina))
        ->values();

    return response()->json($sinNomina);
})->middleware(['auth', 'verified']);
```

- [ ] **Step 2: Ejecutar los tests para verificar que pasan (TDD — verde)**

```bash
php artisan test tests/Feature/NominaDiffTest.php
```

Expected: todos PASS. Si alguno falla, revisar el query de `Colaborador` y el mock del service.

- [ ] **Step 3: Ejecutar suite completa para verificar no hay regresiones**

```bash
php artisan test
```

Expected: todos los tests previos siguen PASS.

- [ ] **Step 4: Commit**

```bash
git add routes/web.php
git commit -m "feat(nomina): add GET /api/nomina/diff endpoint"
```

---

## Task 4: Actualizar `Nomina.vue` — Badge clickeable + tabla expandible

**Files:**
- Modify: `resources/js/Pages/Nomina.vue`

**IMPORTANTE:** Cargar skill antes de modificar este archivo:
```
C:\dev\agente-tareo-rrhh\skill\ui-ux-designer\skill.md
```

- [ ] **Step 1: Añadir nuevos refs en el bloque `<script setup>`**

Localizar:
```js
const diferencia = computed(() => stats.value.total_deben - stats.value.nominas_generadas);
```

Agregar después:
```js
const missingEmployees = ref([])
const loadingDiff = ref(false)
const showDiff = ref(false)
```

- [ ] **Step 2: Añadir función `fetchDiff` en `<script setup>`**

Agregar después de los nuevos refs:
```js
const fetchDiff = async () => {
    if (showDiff.value) {
        showDiff.value = false;
        return;
    }
    if (missingEmployees.value.length > 0) {
        showDiff.value = true;
        return;
    }
    loadingDiff.value = true;
    try {
        const res = await fetch('/api/nomina/diff');
        missingEmployees.value = await res.json();
        showDiff.value = true;
    } catch (error) {
        console.error('Error fetching diff:', error);
    } finally {
        loadingDiff.value = false;
    }
};
```

- [ ] **Step 3: Modificar `refreshStats` para invalidar caché del diff**

Localizar en `refreshStats`:
```js
const refreshStats = async () => {
    loading.value = true;
```

Reemplazar por:
```js
const refreshStats = async () => {
    loading.value = true;
    missingEmployees.value = [];
    showDiff.value = false;
```

- [ ] **Step 4: Reemplazar el badge estático por badge clickeable en el `<template>`**

Localizar el bloque completo:
```html
<div v-if="!loading" class="mt-6 text-center">
    <span v-if="diferencia === 0" class="inline-block px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-sm font-semibold rounded-full">
        ✓ Completo
    </span>
    <span v-else-if="diferencia > 0" class="inline-block px-3 py-1 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 text-sm font-semibold rounded-full">
        Faltan {{ diferencia }} nóminas
    </span>
    <span v-else class="inline-block px-3 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300 text-sm font-semibold rounded-full">
        {{ Math.abs(diferencia) }} nóminas extra
    </span>
</div>
```

Reemplazar por:
```html
<div v-if="!loading" class="mt-6 text-center">
    <span v-if="diferencia === 0"
          class="inline-block px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-sm font-semibold rounded-full">
        ✓ Completo
    </span>
    <button v-else-if="diferencia > 0"
            @click="fetchDiff"
            :disabled="loadingDiff"
            class="inline-flex items-center gap-2 px-3 py-1 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 text-sm font-semibold rounded-full hover:bg-red-200 dark:hover:bg-red-800 transition disabled:opacity-50 disabled:cursor-not-allowed">
        <span v-if="loadingDiff">⏳ Buscando...</span>
        <span v-else>
            Faltan {{ diferencia }} nóminas
            <span class="ml-1">{{ showDiff ? '▲' : '▼' }} Ver detalle</span>
        </span>
    </button>
    <span v-else class="inline-block px-3 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300 text-sm font-semibold rounded-full">
        {{ Math.abs(diferencia) }} nóminas extra
    </span>
</div>
```

- [ ] **Step 5: Añadir la tabla expandible después del bloque del botón "Actualizar"**

Localizar:
```html
<p v-if="lastUpdated" class="text-xs text-gray-500 dark:text-gray-400 text-center">
    Última actualización: {{ lastUpdated }}
</p>
```

Agregar después (antes de la sección `<!-- Nota -->`):
```html
<!-- Tabla de empleados sin nómina -->
<transition name="fade">
    <div v-if="showDiff && missingEmployees.length > 0"
         class="mt-6 bg-white dark:bg-gray-900 border border-red-200 dark:border-red-800 rounded-lg overflow-hidden">
        <div class="flex items-center justify-between px-4 py-3 bg-red-50 dark:bg-red-900/30 border-b border-red-200 dark:border-red-800">
            <h3 class="text-sm font-semibold text-red-800 dark:text-red-300">
                Empleados sin nómina generada ({{ missingEmployees.length }})
            </h3>
            <button @click="showDiff = false"
                    class="text-red-400 hover:text-red-600 dark:hover:text-red-200 text-lg leading-none">
                ×
            </button>
        </div>
        <table class="w-full text-sm">
            <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                    <th class="px-4 py-2 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">ID</th>
                    <th class="px-4 py-2 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Nombre</th>
                    <th class="px-4 py-2 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Estado</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
                <tr v-for="emp in missingEmployees" :key="emp.employee_id"
                    class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td class="px-4 py-2 font-mono text-gray-700 dark:text-gray-300">{{ emp.employee_id }}</td>
                    <td class="px-4 py-2 text-gray-800 dark:text-gray-200">{{ emp.apellido }}, {{ emp.nombre }}</td>
                    <td class="px-4 py-2">
                        <span class="px-2 py-0.5 rounded-full text-xs font-medium"
                              :class="{
                                  'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300': emp.estado === 'Activo',
                                  'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300': emp.estado === 'No Reportado',
                                  'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300': emp.estado === 'Inactivo',
                              }">
                            {{ emp.estado }}
                        </span>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</transition>
```

- [ ] **Step 6: Añadir CSS de transición al final del archivo (antes del cierre `</script setup>` o en `<style>`)**

Agregar al final del archivo, después de `</script>`:
```html
<style scoped>
.fade-enter-active, .fade-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
    opacity: 0;
    transform: translateY(-4px);
}
</style>
```

- [ ] **Step 7: Verificar que el frontend compila sin errores**

```bash
cd C:\dev\agente-tareo-rrhh
npm run build
```

Expected: BUILD SUCCESSFUL sin errores. Si hay errores de Vue, revisar que todos los refs están declarados y los atributos `:class` tienen sintaxis correcta.

- [ ] **Step 8: Commit**

```bash
git add resources/js/Pages/Nomina.vue
git commit -m "feat(nomina): add clickable diff badge and expandable missing employees table"
```

---

## Task 5: Crear archivo de salida del agente

**Files:**
- Create: `C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_007_nomina-diff-empleados-faltantes.md`

- [ ] **Step 1: Crear el reporte de ejecución con el estado real de cada tarea completada**

```markdown
# Reporte de Ejecución: Nómina Diff — Empleados sin Nómina Generada

**Fecha:** 2026-04-29
**Agente:** [nombre del agente]
**Proyecto:** Agente Tareo RRHH

## Progreso de Tareas

### Backend
- [x] Método `getSalarySlipEmployees()` añadido a `ERPNextService`
- [x] Endpoint `GET /api/nomina/diff` registrado en `routes/web.php`

### Tests
- [x] `tests/Feature/NominaDiffTest.php` creado y pasando (5 tests)

### Frontend
- [x] Badge "Faltan X nóminas" convertido en botón clickeable
- [x] Función `fetchDiff` implementada con caché local
- [x] Tabla expandible de empleados faltantes con color por estado
- [x] Reset de estado diff al refrescar stats
- [x] Transición CSS fade añadida

## Resultado de Pruebas

[Describir el output de `php artisan test tests/Feature/NominaDiffTest.php`]
[Describir resultado visual al probar con diferencia > 0 y diferencia = 0]

## Observaciones

[Cualquier decisión técnica tomada durante la implementación]

---
**Estado Final: COMPLETADO**
```

- [ ] **Step 2: Commit final**

```bash
git add C:/jarcrow/Trabajo/Agente-Tareo-RRHH/agentes/respuestas/2026-04-29_007_nomina-diff-empleados-faltantes.md
git commit -m "docs(agente): add execution report for nomina-diff feature"
```

---

## Verificación final

- [ ] `php artisan test` — todos los tests pasan
- [ ] `npm run build` — sin errores
- [ ] En `/nomina` con diferencia > 0: badge clickeable muestra tabla con empleados
- [ ] En `/nomina` con diferencia = 0: badge "✓ Completo" no es clickeable
- [ ] Click en badge → despliega tabla. Click de nuevo → colapsa. Click "×" → colapsa.
- [ ] Click "Actualizar" → limpia lista, próximo click en badge re-fetcha desde ERP
