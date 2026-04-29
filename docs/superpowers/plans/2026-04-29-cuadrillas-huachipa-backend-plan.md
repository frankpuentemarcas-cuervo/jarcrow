# Cuadrillas Huachipa — Backend Plan (Plan A)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear la capa backend completa del módulo Cuadrillas Huachipa: migration, model, 3 controllers, rutas y 2 métodos ERP, con tests para cada componente.

**Architecture:** `CuadrillaController` resourceful maneja CRUD + disable vía Inertia. `HuachipaEmpleadoController` expone endpoints JSON para búsqueda de empleados ERP. La lógica de "mover empleado" detecta conflictos y retorna 409 si `move_confirmed` no es `true`. Plan B cubre el frontend completo.

**Tech Stack:** Laravel 11, PHP 8.2, Pest PHP, MariaDB, ERPNext REST API, Carbon

---

## File Map

| Archivo | Acción |
|---------|--------|
| `database/migrations/2026_04_29_create_cuadrillas_table.php` | Crear |
| `app/Models/Cuadrilla.php` | Crear |
| `app/Http/Controllers/HuachipaController.php` | Crear |
| `app/Http/Controllers/CuadrillaController.php` | Crear |
| `app/Http/Controllers/HuachipaEmpleadoController.php` | Crear |
| `app/Services/ERPNextService.php` | Modificar — añadir 2 métodos al final |
| `routes/web.php` | Modificar — añadir grupo huachipa antes de `Route::middleware('auth')` |
| `tests/Feature/CuadrillasTest.php` | Crear |

---

## Task 1: Migration y Model

**Files:**
- Create: `database/migrations/2026_04_29_create_cuadrillas_table.php`
- Create: `app/Models/Cuadrilla.php`

- [ ] **Step 1: Crear la migration**

```bash
cd C:\dev\agente-tareo-rrhh
docker exec agente-tareo-rrhh-laravel.test-1 php artisan make:migration create_cuadrillas_table
```

Abrir el archivo generado y reemplazar el contenido del método `up()`:

```php
public function up(): void
{
    Schema::create('cuadrillas', function (Blueprint $table) {
        $table->id();
        $table->string('codigo', 20)->unique();
        $table->string('nombre', 100);
        $table->string('supervisor_id', 50)->nullable();
        $table->json('empleados')->default('[]');
        $table->enum('estado', ['activo', 'inactivo'])->default('activo');
        $table->foreignId('created_by')->nullable()->constrained('users')->nullOnDelete();
        $table->timestamps();
        $table->index('estado');
        $table->index('supervisor_id');
    });
}

public function down(): void
{
    Schema::dropIfExists('cuadrillas');
}
```

- [ ] **Step 2: Ejecutar la migration**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan migrate
```

Expected: `... cuadrillas table created`

- [ ] **Step 3: Crear el Model `app/Models/Cuadrilla.php`**

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Cuadrilla extends Model
{
    use HasFactory;

    protected $fillable = [
        'codigo',
        'nombre',
        'supervisor_id',
        'empleados',
        'estado',
        'created_by',
    ];

    protected $casts = [
        'empleados' => 'array',
    ];

    protected $appends = ['empleados_count'];

    public function getEmpleadosCountAttribute(): int
    {
        return count($this->empleados ?? []);
    }

    public function scopeActivos($query)
    {
        return $query->where('estado', 'activo');
    }

    public function scopeInactivos($query)
    {
        return $query->where('estado', 'inactivo');
    }

    public function createdBy()
    {
        return $this->belongsTo(User::class, 'created_by');
    }
}
```

- [ ] **Step 4: Verificar que el modelo funciona**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan tinker --execute="echo App\Models\Cuadrilla::count();"
```

Expected: `0`

- [ ] **Step 5: Commit**

```bash
git add database/migrations app/Models/Cuadrilla.php
git commit -m "feat(huachipa): add cuadrillas migration and Cuadrilla model"
```

---

## Task 2: ERPNextService — 2 métodos para Huachipa

**Files:**
- Modify: `app/Services/ERPNextService.php`

- [ ] **Step 1: Añadir `getEmpleadosHuachipa()` al final de la clase (antes del `}` de cierre)**

```php
public function getEmpleadosHuachipa(): array
{
    try {
        $response = Http::withHeaders($this->getHeaders())
            ->timeout(15)
            ->get("{$this->baseUrl}/api/resource/Employee", [
                'fields'            => '["name","employee_name","custom_nro_documento"]',
                'filters'           => '[["branch","=","HUACHIPA CO"],["status","=","Active"]]',
                'limit_page_length' => 'None',
            ]);

        if ($response->successful()) {
            return $response->json('data') ?? [];
        }

        Log::error("ERPNext Error getEmpleadosHuachipa: " . $response->body());
        return [];
    } catch (\Exception $e) {
        Log::error("ERPNext Exception getEmpleadosHuachipa: " . $e->getMessage());
        return [];
    }
}
```

- [ ] **Step 2: Añadir `searchEmpleadosHuachipa()` inmediatamente después**

```php
public function searchEmpleadosHuachipa(string $q): array
{
    try {
        $response = Http::withHeaders($this->getHeaders())
            ->timeout(10)
            ->get("{$this->baseUrl}/api/resource/Employee", [
                'fields'  => '["name","employee_name","custom_nro_documento"]',
                'filters' => '[["branch","=","HUACHIPA CO"],["status","=","Active"],["employee_name","like","%' . $q . '%"]]',
                'or_filters' => '[["name","like","%' . $q . '%"],["custom_nro_documento","like","%' . $q . '%"]]',
                'limit_page_length' => 20,
            ]);

        if ($response->successful()) {
            return $response->json('data') ?? [];
        }

        Log::error("ERPNext Error searchEmpleadosHuachipa: " . $response->body());
        return [];
    } catch (\Exception $e) {
        Log::error("ERPNext Exception searchEmpleadosHuachipa: " . $e->getMessage());
        return [];
    }
}
```

- [ ] **Step 3: Verificar que el archivo compila**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan about
```

Expected: output normal sin errores.

- [ ] **Step 4: Commit**

```bash
git add app/Services/ERPNextService.php
git commit -m "feat(erp): add getEmpleadosHuachipa() and searchEmpleadosHuachipa()"
```

---

## Task 3: Tests de backend (TDD — escribir antes de controllers)

**Files:**
- Create: `tests/Feature/CuadrillasTest.php`

- [ ] **Step 1: Crear el archivo de tests**

```php
<?php

use App\Models\Cuadrilla;
use App\Models\User;
use App\Services\ERPNextService;

// ── Routing ───────────────────────────────────────────────────────────

it('huachipa index requires authentication', function () {
    $this->get('/huachipa')->assertRedirect('/login');
});

it('cuadrillas index requires authentication', function () {
    $this->get('/huachipa/cuadrillas')->assertRedirect('/login');
});

// ── CRUD ─────────────────────────────────────────────────────────────

it('can list cuadrillas activas', function () {
    $user = User::factory()->create();
    Cuadrilla::create([
        'codigo' => 'CUA-001', 'nombre' => 'Grupo Norte',
        'supervisor_id' => 'EMP-0001', 'empleados' => ['EMP-0010'],
        'estado' => 'activo', 'created_by' => $user->id,
    ]);

    $response = $this->actingAs($user)->get('/huachipa/cuadrillas?estado=activo');
    $response->assertStatus(200);
    $response->assertInertia(fn ($page) => $page
        ->component('Huachipa/Cuadrillas/Index')
        ->has('cuadrillas.data', 1)
    );
});

it('can store a new cuadrilla', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)->post('/huachipa/cuadrillas', [
        'codigo'        => 'CUA-001',
        'nombre'        => 'Grupo Norte',
        'supervisor_id' => 'EMP-0001',
        'empleados'     => ['EMP-0010', 'EMP-0011'],
        'move_confirmed'=> false,
    ]);

    $response->assertRedirect();
    $this->assertDatabaseHas('cuadrillas', ['codigo' => 'CUA-001', 'estado' => 'activo']);
});

it('rejects cuadrilla without empleados', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)->post('/huachipa/cuadrillas', [
        'codigo'        => 'CUA-001',
        'nombre'        => 'Grupo Norte',
        'supervisor_id' => 'EMP-0001',
        'empleados'     => [],
    ]);

    $response->assertSessionHasErrors('empleados');
});

it('rejects duplicate codigo', function () {
    $user = User::factory()->create();
    Cuadrilla::create([
        'codigo' => 'CUA-001', 'nombre' => 'Existente',
        'supervisor_id' => 'EMP-0001', 'empleados' => ['EMP-0010'],
        'estado' => 'activo', 'created_by' => $user->id,
    ]);

    $response = $this->actingAs($user)->post('/huachipa/cuadrillas', [
        'codigo'        => 'CUA-001',
        'nombre'        => 'Nueva',
        'supervisor_id' => 'EMP-0002',
        'empleados'     => ['EMP-0020'],
    ]);

    $response->assertSessionHasErrors('codigo');
});

it('returns 409 when employee belongs to another cuadrilla and move_confirmed is false', function () {
    $user = User::factory()->create();
    Cuadrilla::create([
        'codigo' => 'CUA-001', 'nombre' => 'Grupo Norte',
        'supervisor_id' => 'EMP-0001', 'empleados' => ['EMP-0010'],
        'estado' => 'activo', 'created_by' => $user->id,
    ]);

    $response = $this->actingAs($user)->postJson('/huachipa/cuadrillas', [
        'codigo'         => 'CUA-002',
        'nombre'         => 'Grupo Sur',
        'supervisor_id'  => 'EMP-0002',
        'empleados'      => ['EMP-0010'],
        'move_confirmed' => false,
    ]);

    $response->assertStatus(409);
    $response->assertJsonStructure(['conflicts']);
});

it('moves employee when move_confirmed is true', function () {
    $user = User::factory()->create();
    $cuadrillaA = Cuadrilla::create([
        'codigo' => 'CUA-001', 'nombre' => 'Grupo Norte',
        'supervisor_id' => 'EMP-0001', 'empleados' => ['EMP-0010'],
        'estado' => 'activo', 'created_by' => $user->id,
    ]);

    $this->actingAs($user)->postJson('/huachipa/cuadrillas', [
        'codigo'         => 'CUA-002',
        'nombre'         => 'Grupo Sur',
        'supervisor_id'  => 'EMP-0002',
        'empleados'      => ['EMP-0010'],
        'move_confirmed' => true,
    ]);

    $cuadrillaA->refresh();
    expect($cuadrillaA->empleados)->not->toContain('EMP-0010');
    $this->assertDatabaseHas('cuadrillas', ['codigo' => 'CUA-002']);
});

it('disables a cuadrilla', function () {
    $user = User::factory()->create();
    $cuadrilla = Cuadrilla::create([
        'codigo' => 'CUA-001', 'nombre' => 'Grupo Norte',
        'supervisor_id' => 'EMP-0001', 'empleados' => ['EMP-0010'],
        'estado' => 'activo', 'created_by' => $user->id,
    ]);

    $this->actingAs($user)->patch("/huachipa/cuadrillas/{$cuadrilla->id}/disable");

    $cuadrilla->refresh();
    expect($cuadrilla->estado)->toBe('inactivo');
});

it('cannot physically delete an active cuadrilla', function () {
    $user = User::factory()->create();
    $cuadrilla = Cuadrilla::create([
        'codigo' => 'CUA-001', 'nombre' => 'Grupo Norte',
        'supervisor_id' => 'EMP-0001', 'empleados' => ['EMP-0010'],
        'estado' => 'activo', 'created_by' => $user->id,
    ]);

    $response = $this->actingAs($user)->delete("/huachipa/cuadrillas/{$cuadrilla->id}");
    $response->assertStatus(422);
    $this->assertDatabaseHas('cuadrillas', ['id' => $cuadrilla->id]);
});

it('can physically delete an inactive cuadrilla', function () {
    $user = User::factory()->create();
    $cuadrilla = Cuadrilla::create([
        'codigo' => 'CUA-001', 'nombre' => 'Grupo Norte',
        'supervisor_id' => 'EMP-0001', 'empleados' => ['EMP-0010'],
        'estado' => 'inactivo', 'created_by' => $user->id,
    ]);

    $this->actingAs($user)->delete("/huachipa/cuadrillas/{$cuadrilla->id}");
    $this->assertDatabaseMissing('cuadrillas', ['id' => $cuadrilla->id]);
});

// ── Employee search endpoints ─────────────────────────────────────────

it('empleados search returns 401 without auth', function () {
    $this->get('/huachipa/empleados?q=juan')->assertRedirect('/login');
});

it('empleados search returns empty array for query shorter than 2 chars', function () {
    $user = User::factory()->create();
    $this->mock(ERPNextService::class, fn($m) =>
        $m->shouldReceive('searchEmpleadosHuachipa')->never()
    );

    $response = $this->actingAs($user)->getJson('/huachipa/empleados?q=j');
    $response->assertStatus(200)->assertJson([]);
});

it('supervisores endpoint returns employee list', function () {
    $user = User::factory()->create();
    $this->mock(ERPNextService::class, fn($m) =>
        $m->shouldReceive('getEmpleadosHuachipa')
          ->once()
          ->andReturn([['name' => 'EMP-0001', 'employee_name' => 'Juan', 'custom_nro_documento' => '12345678']])
    );

    $response = $this->actingAs($user)->getJson('/huachipa/supervisores');
    $response->assertStatus(200)->assertJsonCount(1);
});
```

- [ ] **Step 2: Ejecutar tests — deben fallar (TDD rojo)**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan test tests/Feature/CuadrillasTest.php
```

Expected: FAIL — rutas no existen aún.

- [ ] **Step 3: Commit del test en rojo**

```bash
git add tests/Feature/CuadrillasTest.php
git commit -m "test(huachipa): add failing tests for cuadrillas CRUD and employee endpoints"
```

---

## Task 4: Controllers y Rutas

**Files:**
- Create: `app/Http/Controllers/HuachipaController.php`
- Create: `app/Http/Controllers/CuadrillaController.php`
- Create: `app/Http/Controllers/HuachipaEmpleadoController.php`
- Modify: `routes/web.php`

- [ ] **Step 1: Crear `HuachipaController.php`**

```php
<?php

namespace App\Http\Controllers;

use App\Models\Cuadrilla;
use Inertia\Inertia;
use Inertia\Response;

class HuachipaController extends Controller
{
    public function index(): Response
    {
        $stats = [
            'cuadrillas_activas'   => Cuadrilla::activos()->count(),
            'cuadrillas_inactivas' => Cuadrilla::inactivos()->count(),
            'total_empleados'      => Cuadrilla::activos()->get()
                ->sum(fn ($c) => count($c->empleados ?? [])),
        ];

        return Inertia::render('Huachipa/Index', compact('stats'));
    }
}
```

- [ ] **Step 2: Crear `CuadrillaController.php`**

```php
<?php

namespace App\Http\Controllers;

use App\Models\Cuadrilla;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;

class CuadrillaController extends Controller
{
    public function index(): Response
    {
        $estado = request('estado', 'activo');

        $cuadrillas = Cuadrilla::where('estado', $estado)
            ->orderBy('codigo')
            ->paginate(20)
            ->through(fn ($c) => [
                'id'              => $c->id,
                'codigo'          => $c->codigo,
                'nombre'          => $c->nombre,
                'supervisor_id'   => $c->supervisor_id,
                'empleados_count' => $c->empleados_count,
                'estado'          => $c->estado,
            ]);

        return Inertia::render('Huachipa/Cuadrillas/Index', [
            'cuadrillas' => $cuadrillas,
            'estado'     => $estado,
        ]);
    }

    public function create(): Response
    {
        return Inertia::render('Huachipa/Cuadrillas/Form', ['cuadrilla' => null]);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'codigo'          => 'required|max:20|unique:cuadrillas,codigo',
            'nombre'          => 'required|max:100',
            'supervisor_id'   => 'required|string',
            'empleados'       => 'required|array|min:1',
            'empleados.*'     => 'string',
            'move_confirmed'  => 'boolean',
        ]);

        $conflicts = $this->detectConflicts($validated['empleados'], null);

        if ($conflicts->isNotEmpty() && !($validated['move_confirmed'] ?? false)) {
            return response()->json(['conflicts' => $conflicts], 409);
        }

        if ($conflicts->isNotEmpty()) {
            $this->resolveConflicts($conflicts, $validated['empleados']);
        }

        Cuadrilla::create([
            'codigo'       => $validated['codigo'],
            'nombre'       => $validated['nombre'],
            'supervisor_id'=> $validated['supervisor_id'],
            'empleados'    => $validated['empleados'],
            'estado'       => 'activo',
            'created_by'   => $request->user()->id,
        ]);

        return redirect()->route('huachipa.cuadrillas.index')
            ->with('success', 'Cuadrilla creada correctamente.');
    }

    public function edit(Cuadrilla $cuadrilla): Response
    {
        return Inertia::render('Huachipa/Cuadrillas/Form', [
            'cuadrilla' => $cuadrilla,
        ]);
    }

    public function update(Request $request, Cuadrilla $cuadrilla)
    {
        $validated = $request->validate([
            'codigo'         => 'required|max:20|unique:cuadrillas,codigo,' . $cuadrilla->id,
            'nombre'         => 'required|max:100',
            'supervisor_id'  => 'required|string',
            'empleados'      => 'required|array|min:1',
            'empleados.*'    => 'string',
            'move_confirmed' => 'boolean',
        ]);

        $conflicts = $this->detectConflicts($validated['empleados'], $cuadrilla->id);

        if ($conflicts->isNotEmpty() && !($validated['move_confirmed'] ?? false)) {
            return response()->json(['conflicts' => $conflicts], 409);
        }

        if ($conflicts->isNotEmpty()) {
            $this->resolveConflicts($conflicts, $validated['empleados']);
        }

        $cuadrilla->update([
            'codigo'       => $validated['codigo'],
            'nombre'       => $validated['nombre'],
            'supervisor_id'=> $validated['supervisor_id'],
            'empleados'    => $validated['empleados'],
        ]);

        return redirect()->route('huachipa.cuadrillas.index')
            ->with('success', 'Cuadrilla actualizada correctamente.');
    }

    public function disable(Cuadrilla $cuadrilla)
    {
        $cuadrilla->update(['estado' => 'inactivo']);

        return redirect()->route('huachipa.cuadrillas.index')
            ->with('success', 'Cuadrilla deshabilitada.');
    }

    public function destroy(Cuadrilla $cuadrilla)
    {
        if ($cuadrilla->estado === 'activo') {
            return response()->json(
                ['message' => 'Solo se puede eliminar cuadrillas inactivas.'],
                422
            );
        }

        $cuadrilla->delete();

        return redirect()->route('huachipa.cuadrillas.index')
            ->with('success', 'Cuadrilla eliminada.');
    }

    private function detectConflicts(array $empleados, ?int $excludeId)
    {
        return Cuadrilla::when($excludeId, fn ($q) => $q->where('id', '!=', $excludeId))
            ->get()
            ->filter(fn ($c) => !empty(array_intersect($c->empleados ?? [], $empleados)))
            ->map(fn ($c) => [
                'cuadrilla_id'     => $c->id,
                'cuadrilla_codigo' => $c->codigo,
                'cuadrilla_nombre' => $c->nombre,
                'empleados'        => array_values(array_intersect($c->empleados ?? [], $empleados)),
            ])
            ->values();
    }

    private function resolveConflicts($conflicts, array $newEmpleados): void
    {
        foreach ($conflicts as $conflict) {
            $otra = Cuadrilla::find($conflict['cuadrilla_id']);
            if ($otra) {
                $otra->update([
                    'empleados' => array_values(
                        array_diff($otra->empleados ?? [], $newEmpleados)
                    ),
                ]);
            }
        }
    }
}
```

- [ ] **Step 3: Crear `HuachipaEmpleadoController.php`**

```php
<?php

namespace App\Http\Controllers;

use App\Services\ERPNextService;
use Illuminate\Http\JsonResponse;

class HuachipaEmpleadoController extends Controller
{
    public function search(ERPNextService $erp): JsonResponse
    {
        $q = request('q', '');

        if (strlen($q) < 2) {
            return response()->json([]);
        }

        return response()->json($erp->searchEmpleadosHuachipa($q));
    }

    public function supervisores(ERPNextService $erp): JsonResponse
    {
        return response()->json($erp->getEmpleadosHuachipa());
    }
}
```

- [ ] **Step 4: Añadir rutas en `routes/web.php` — insertar antes de `Route::middleware('auth')`**

Localizar la línea:
```php
Route::middleware('auth')->group(function () {
```

Insertar justo antes:
```php
use App\Http\Controllers\HuachipaController;
use App\Http\Controllers\CuadrillaController;
use App\Http\Controllers\HuachipaEmpleadoController;

Route::prefix('huachipa')->middleware(['auth', 'verified'])->name('huachipa.')->group(function () {
    Route::get('/', [HuachipaController::class, 'index'])->name('index');
    Route::resource('cuadrillas', CuadrillaController::class);
    Route::patch('cuadrillas/{cuadrilla}/disable', [CuadrillaController::class, 'disable'])
         ->name('cuadrillas.disable');
    Route::get('empleados', [HuachipaEmpleadoController::class, 'search'])
         ->name('empleados.search');
    Route::get('supervisores', [HuachipaEmpleadoController::class, 'supervisores'])
         ->name('supervisores');
});
```

- [ ] **Step 5: Ejecutar tests — deben pasar (TDD verde)**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan test tests/Feature/CuadrillasTest.php
```

Expected: todos los tests PASS.

- [ ] **Step 6: Ejecutar suite completa — sin regresiones**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 php artisan test
```

Expected: todos los tests PASS.

- [ ] **Step 7: Commit**

```bash
git add app/Http/Controllers/HuachipaController.php \
        app/Http/Controllers/CuadrillaController.php \
        app/Http/Controllers/HuachipaEmpleadoController.php \
        routes/web.php
git commit -m "feat(huachipa): add HuachipaController, CuadrillaController, HuachipaEmpleadoController and routes"
```

---

## Task 5: Archivo de salida (reporte parcial Plan A)

**Files:**
- Create: `C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_012a_cuadrillas-huachipa-backend.md`

- [ ] **Step 1: Crear reporte**

```markdown
# Reporte de Ejecución: Cuadrillas Huachipa — Backend (Plan A)

**Fecha:** 2026-04-29
**Agente:** [nombre]
**Proyecto:** Agente Tareo RRHH

## Progreso de Tareas

### Fundación
- [x] Migration `cuadrillas` creada y ejecutada
- [x] Model `Cuadrilla` con casts, scopes y accessor `empleados_count`

### ERPNextService
- [x] `getEmpleadosHuachipa()` añadido
- [x] `searchEmpleadosHuachipa()` añadido

### Controllers y Rutas
- [x] `HuachipaController` creado
- [x] `CuadrillaController` con CRUD + disable + lógica de conflictos
- [x] `HuachipaEmpleadoController` con search y supervisores
- [x] Rutas registradas en `routes/web.php`

## Resultado de Pruebas
[Output de `php artisan test tests/Feature/CuadrillasTest.php`]
[Output de `php artisan test` — suite completa]

## Observaciones
[Decisiones técnicas]

---
**Estado Plan A: COMPLETADO — proceder con Plan B (Frontend)**
```

- [ ] **Step 2: Commit**

```bash
git add "C:/jarcrow/Trabajo/Agente-Tareo-RRHH/agentes/respuestas/2026-04-29_012a_cuadrillas-huachipa-backend.md"
git commit -m "docs(agente): add Plan A execution report for cuadrillas-huachipa backend"
```

---

## Verificación final Plan A

- [ ] `php artisan migrate:status` muestra `cuadrillas` table
- [ ] `php artisan test tests/Feature/CuadrillasTest.php` — todos PASS
- [ ] `php artisan test` — suite completa sin regresiones
- [ ] `php artisan route:list --path=huachipa` muestra las 7 rutas
