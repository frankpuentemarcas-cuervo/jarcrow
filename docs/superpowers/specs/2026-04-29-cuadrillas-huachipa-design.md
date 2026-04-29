# Spec: Módulo Cuadrillas Huachipa

**Fecha:** 2026-04-29
**Proyecto:** Agente Tareo RRHH (`C:\dev\agente-tareo-rrhh`)
**Archivo de plan:** `docs/superpowers/plans/2026-04-29-cuadrillas-huachipa-plan.md`

---

## Objetivo

Nuevo módulo "Huachipa" en la app de tareo. Contiene una card "Cuadrillas" que lleva a gestión CRUD completa de cuadrillas de trabajo del branch HUACHIPA CO. Los empleados se obtienen en tiempo real desde ERPNext.

## Regla de negocio clave

**Un empleado = una cuadrilla.** Si se intenta agregar un empleado que ya pertenece a otra cuadrilla, se muestra modal de confirmación para *moverlo* (se elimina de la cuadrilla anterior y se agrega a la nueva).

---

## Base de Datos

### Migration `create_cuadrillas_table`

```php
Schema::create('cuadrillas', function (Blueprint $table) {
    $table->id();
    $table->string('codigo', 20)->unique();
    $table->string('nombre', 100);
    $table->string('supervisor_id', 50)->nullable(); // employee_name de ERPNext (ej. EMP-0042)
    $table->json('empleados')->default('[]');         // array de employee_ids
    $table->enum('estado', ['activo', 'inactivo'])->default('activo');
    $table->foreignId('created_by')->nullable()->constrained('users')->nullOnDelete();
    $table->timestamps();
    $table->index('estado');
    $table->index('supervisor_id');
});
```

### Model `App\Models\Cuadrilla`

```php
protected $fillable = ['codigo', 'nombre', 'supervisor_id', 'empleados', 'estado', 'created_by'];
protected $casts    = ['empleados' => 'array'];

public function getEmpleadosCountAttribute(): int { return count($this->empleados ?? []); }
public function scopeActivos($q)   { return $q->where('estado', 'activo'); }
public function scopeInactivos($q) { return $q->where('estado', 'inactivo'); }
public function createdBy()        { return $this->belongsTo(User::class, 'created_by'); }
```

---

## Backend

### Archivos a crear

| Archivo | Responsabilidad |
|---------|-----------------|
| `app/Http/Controllers/HuachipaController.php` | Index del módulo (Inertia render) |
| `app/Http/Controllers/CuadrillaController.php` | CRUD + disable completo |
| `app/Http/Controllers/HuachipaEmpleadoController.php` | JSON endpoints para búsqueda ERP |
| `app/Models/Cuadrilla.php` | Model con casts y scopes |
| `database/migrations/2026_04_29_create_cuadrillas_table.php` | Schema |

### Rutas (`routes/web.php`)

```php
Route::prefix('huachipa')->middleware(['auth', 'verified'])->name('huachipa.')->group(function () {
    Route::get('/', [HuachipaController::class, 'index'])->name('index');
    Route::resource('cuadrillas', CuadrillaController::class);
    Route::patch('cuadrillas/{cuadrilla}/disable', [CuadrillaController::class, 'disable'])
         ->name('cuadrillas.disable');
    // JSON endpoints
    Route::get('empleados', [HuachipaEmpleadoController::class, 'search'])
         ->name('empleados.search');
    Route::get('supervisores', [HuachipaEmpleadoController::class, 'supervisores'])
         ->name('supervisores');
});
```

### `HuachipaController::index()`

```php
public function index(): Response
{
    $stats = [
        'cuadrillas_activas'   => Cuadrilla::activos()->count(),
        'cuadrillas_inactivas' => Cuadrilla::inactivos()->count(),
        'total_empleados'      => Cuadrilla::activos()->get()->sum(fn($c) => count($c->empleados)),
    ];
    return Inertia::render('Huachipa/Index', compact('stats'));
}
```

### `CuadrillaController`

**`index()`**
```php
$estado = request('estado', 'activo');
$cuadrillas = Cuadrilla::where('estado', $estado)
    ->orderBy('codigo')
    ->paginate(20)
    ->through(fn($c) => [
        'id'               => $c->id,
        'codigo'           => $c->codigo,
        'nombre'           => $c->nombre,
        'supervisor_id'    => $c->supervisor_id,
        'empleados_count'  => $c->empleados_count,
        'estado'           => $c->estado,
    ]);
return Inertia::render('Huachipa/Cuadrillas/Index', [
    'cuadrillas' => $cuadrillas,
    'estado'     => $estado,
]);
```

**`create()` / `edit()`**
```php
// create():
return Inertia::render('Huachipa/Cuadrillas/Form', ['cuadrilla' => null]);

// edit():
return Inertia::render('Huachipa/Cuadrillas/Form', [
    'cuadrilla' => $cuadrilla->load([]), // pass full model including empleados
]);
```

**`store()` / `update()` — lógica de conflictos**

Validación base:
```php
$validated = $request->validate([
    'codigo'         => 'required|max:20|unique:cuadrillas,codigo,' . ($cuadrilla->id ?? 'NULL'),
    'nombre'         => 'required|max:100',
    'supervisor_id'  => 'required|string',
    'empleados'      => 'required|array|min:1',
    'empleados.*'    => 'string',
    'move_confirmed' => 'boolean',
]);
```

Detección de conflictos: para cada `employee_id` en `$validated['empleados']`, buscar si existe en `cuadrillas.empleados` JSON de otra cuadrilla:
```php
$conflicts = Cuadrilla::where('id', '!=', $cuadrilla->id ?? 0)
    ->get()
    ->filter(fn($c) => !empty(array_intersect($c->empleados, $validated['empleados'])))
    ->map(fn($c) => [
        'cuadrilla_id'     => $c->id,
        'cuadrilla_codigo' => $c->codigo,
        'cuadrilla_nombre' => $c->nombre,
        'empleados'        => array_intersect($c->empleados, $validated['empleados']),
    ])
    ->values();
```

Si `$conflicts->isNotEmpty()` y `move_confirmed !== true` → return `response()->json(['conflicts' => $conflicts], 409)`.

Si `move_confirmed === true` → remover los employee_ids en conflicto de sus cuadrillas anteriores:
```php
foreach ($conflicts as $conflict) {
    $otraCuadrilla = Cuadrilla::find($conflict['cuadrilla_id']);
    $otraCuadrilla->update([
        'empleados' => array_values(array_diff($otraCuadrilla->empleados, $validated['empleados']))
    ]);
}
```

**`disable()`**
```php
$cuadrilla->update(['estado' => 'inactivo']);
return redirect()->route('huachipa.cuadrillas.index')->with('success', 'Cuadrilla deshabilitada.');
```

**`destroy()`**
```php
if ($cuadrilla->estado === 'activo') {
    return back()->withErrors(['delete' => 'Solo se puede eliminar cuadrillas inactivas.']);
}
$cuadrilla->delete();
return redirect()->route('huachipa.cuadrillas.index')->with('success', 'Cuadrilla eliminada.');
```

### `HuachipaEmpleadoController`

**`search()`** — JSON, no Inertia:
```php
$q = request('q', '');
if (strlen($q) < 2) return response()->json([]);
$empleados = app(ERPNextService::class)->searchEmpleadosHuachipa($q);
return response()->json($empleados);
```

**`supervisores()`**:
```php
$empleados = app(ERPNextService::class)->getEmpleadosHuachipa();
return response()->json($empleados);
```

### ERPNextService — 2 nuevos métodos

**`getEmpleadosHuachipa(): array`**
```php
// GET /api/resource/Employee
// fields: ["name","employee_name","custom_nro_documento"]
// filters: [["branch","=","HUACHIPA CO"],["status","=","Active"]]
// limit_page_length: None
// retorna: [{ name, employee_name, custom_nro_documento }]
```

**`searchEmpleadosHuachipa(string $q): array`**
```php
// GET /api/resource/Employee
// fields: ["name","employee_name","custom_nro_documento"]
// filters: [
//   ["branch","=","HUACHIPA CO"],
//   ["status","=","Active"],
//   [["employee_name","like","%$q%"],"or",["name","like","%$q%"],"or",["custom_nro_documento","like","%$q%"]]
// ]
// limit_page_length: 20
```

Ambos métodos siguen el patrón existente: try/catch, Log::error en fallo, retornan `[]` en error.

---

## Frontend

### Nuevos archivos Vue

| Archivo | Tipo |
|---------|------|
| `resources/js/Pages/Huachipa/Index.vue` | Página — cards del módulo |
| `resources/js/Pages/Huachipa/Cuadrillas/Index.vue` | Página — lista paginada |
| `resources/js/Pages/Huachipa/Cuadrillas/Form.vue` | Página — crear/editar |
| `resources/js/Components/Huachipa/EmpleadoModal.vue` | Modal búsqueda + selección |
| `resources/js/Components/Huachipa/ConflictModal.vue` | Modal confirmación mover empleado |
| `resources/js/Composables/useToast.js` | Toast notifications (si no existe) |

### `AppLayout.vue` — añadir nav item

```js
{ name: 'Huachipa', href: '/huachipa', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z' }
```

### `Huachipa/Index.vue`

Card "Cuadrillas" con:
- Conteo de cuadrillas activas (de `stats.cuadrillas_activas`)
- Sub-texto: `{stats.total_empleados} empleados asignados`
- Link a `/huachipa/cuadrillas`
- Estilo: gradiente `from-blue-50 to-indigo-50`, borde `border-indigo-200`

### `Huachipa/Cuadrillas/Index.vue`

```
[Tabs: Activos (N) | Inactivos (N)]           [+ Agregar]

┌──────────┬───────────┬──────────┬────────────┬─────────┬──────────┐
│ Código   │ Nombre    │ Empleados│ Supervisor │ Estado  │ Acciones │
├──────────┼───────────┼──────────┼────────────┼─────────┼──────────┤
│ CUA-001  │ Grupo Norte│    12   │ Juan García│ Activo  │ ✏ 🚫 🗑  │
│ CUA-002  │ Grupo Sur  │     8   │ María López│ Inactivo│ ✏    🗑  │
└──────────┴───────────┴──────────┴────────────┴─────────┴──────────┘
[Paginación]
```

- Tab activo cambia query param `?estado=activo|inactivo` → Inertia visit preserve scroll
- Filas inactivas: `bg-gray-50 opacity-75`
- Botón Deshabilitar: solo en filas activas. Botón Eliminar: solo en filas inactivas.
- Confirmación JS nativa antes de Deshabilitar y Eliminar

### `Huachipa/Cuadrillas/Form.vue`

```
Código de Cuadrilla: [____________]   Nombre: [________________________]
Supervisor:          [▼ Seleccionar supervisor]

── Personal de la Cuadrilla (3 empleados) ──────────────────────────
[+ Agregar Personal]

┌────────────┬──────────────┬──────────────────────────────┬────┐
│ ID         │ Documento    │ Nombre                       │    │
├────────────┼──────────────┼──────────────────────────────┼────┤
│ EMP-0001   │ 72123456     │ Juan García                  │ ×  │
└────────────┴──────────────┴──────────────────────────────┴────┘

                              [Cancelar]  [Guardar Cuadrilla]
```

- Supervisor select se carga al montar con `/huachipa/supervisores`
- Remover empleado: check que no sea el supervisor asignado (si lo es → error inline)
- Al remover supervisor del personal → limpiar campo supervisor también
- `useForm` de Inertia para manejo de estado y errores

### `EmpleadoModal.vue`

```
┌─ Agregar Personal ─────────────────────────────── [×] ─────────────┐
│ 🔍 [Buscar por documento, nombre o ID...          ]                 │
│                                                                     │
│ Resultados:                                                         │
│ ☐ EMP-0042 · 45678901 · Carlos Ruiz                                │
│ ☐ EMP-0043 · 56789012 · Ana Torres                                 │
│                    [Spinner / "No se encontraron resultados"]       │
│                                                                     │
│ ── Ya en cuadrilla (readonly) ──────────────────────               │
│ EMP-0001 · 72123456 · Juan García                                   │
│                                                                     │
│              [Cancelar]  [Agregar seleccionados (2)]               │
└─────────────────────────────────────────────────────────────────────┘
```

- Debounce 300ms en búsqueda, min 2 chars
- Max 3 reintentos con backoff exponencial (1s, 2s, 4s) si falla ERP
- Si falla tras 3 intentos: "Error al conectar con ERPNext" + botón "Reintentar"
- No permite seleccionar empleados ya en la cuadrilla actual

### `ConflictModal.vue`

```
┌─ Empleado ya asignado ──────────────────────────────────────────────┐
│                                                                     │
│  El empleado "Carlos Ruiz (EMP-0042, Doc: 45678901)"               │
│  pertenece a la cuadrilla "CUA-005 – Grupo Este".                  │
│                                                                     │
│  ¿Desea moverlo a esta cuadrilla?                                   │
│  (Será removido automáticamente de la cuadrilla anterior)           │
│                                                                     │
│                    [Cancelar]   [Sí, mover]                        │
└─────────────────────────────────────────────────────────────────────┘
```

Si hay múltiples conflictos → mostrar todos en lista antes de confirmar.

### `useToast.js`

```js
// Composable global para notificaciones toast
// toast.success('Cuadrilla guardada correctamente')
// toast.error('Error al guardar')
// Duración: 3s auto-dismiss
// Posición: top-right
```

---

## Validaciones de Negocio

| Escenario | Comportamiento |
|-----------|----------------|
| Crear cuadrilla sin empleados | Error: "Se requiere al menos 1 empleado" |
| Código duplicado | Error: "El código ya existe" |
| Sin supervisor | Error: "El supervisor es requerido" |
| Empleado duplicado en misma cuadrilla | Bloqueado en frontend (ya está en lista) |
| Empleado en otra cuadrilla | `ConflictModal` → si confirma: mover |
| Remover supervisor del personal | Error: "No puede remover al supervisor del equipo" |
| Eliminar cuadrilla activa | Error 422: "Solo se pueden eliminar cuadrillas inactivas" |
| ERP timeout (3 intentos fallidos) | Mensaje de error + botón Reintentar |
| Empleado no encontrado en búsqueda | "No se encontraron resultados" |

---

## Archivos a crear/modificar

| Archivo | Acción |
|---------|--------|
| `database/migrations/2026_04_29_create_cuadrillas_table.php` | Crear |
| `app/Models/Cuadrilla.php` | Crear |
| `app/Http/Controllers/HuachipaController.php` | Crear |
| `app/Http/Controllers/CuadrillaController.php` | Crear |
| `app/Http/Controllers/HuachipaEmpleadoController.php` | Crear |
| `app/Services/ERPNextService.php` | Modificar (añadir 2 métodos) |
| `routes/web.php` | Modificar (añadir grupo huachipa) |
| `resources/js/Layouts/AppLayout.vue` | Modificar (añadir nav item) |
| `resources/js/Pages/Huachipa/Index.vue` | Crear |
| `resources/js/Pages/Huachipa/Cuadrillas/Index.vue` | Crear |
| `resources/js/Pages/Huachipa/Cuadrillas/Form.vue` | Crear |
| `resources/js/Components/Huachipa/EmpleadoModal.vue` | Crear |
| `resources/js/Components/Huachipa/ConflictModal.vue` | Crear |
| `resources/js/Composables/useToast.js` | Crear |
| `tests/Feature/CuadrillasTest.php` | Crear |

## Criterios de Aceptación

1. `/huachipa` carga con card Cuadrillas y stats correctos
2. `/huachipa/cuadrillas` lista paginada con tabs activo/inactivo
3. Crear cuadrilla con empleados y supervisor → guarda correctamente
4. Editar cuadrilla → datos pre-poblados, guardar actualiza
5. Mover empleado entre cuadrillas → ConflictModal → confirmar → empleado removido de anterior
6. Deshabilitar → estado=inactivo, fila aparece en tab Inactivos
7. Eliminar cuadrilla activa → error. Eliminar inactiva → eliminada físicamente
8. Búsqueda ERP con texto < 2 chars → sin request. ≥ 2 chars → resultados
9. ERP falla → retry 3 veces → mensaje de error + botón reintentar
10. `php artisan test` suite completa PASS

## Archivo de salida del agente

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_012_cuadrillas-huachipa.md
```
