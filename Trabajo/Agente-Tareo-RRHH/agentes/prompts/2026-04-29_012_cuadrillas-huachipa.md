---
fecha: 2026-04-29
agente_id: "012"
descripcion: "cuadrillas-huachipa-modulo-completo"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "C:\\jarcrow\\Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-29_012_cuadrillas-huachipa.md"
---

# Fase 12: Módulo Cuadrillas Huachipa

## Contexto

Proyecto en `C:\dev\agente-tareo-rrhh`. Crear módulo completo "Huachipa" con gestión CRUD de cuadrillas de trabajo. Los empleados se obtienen de ERPNext filtrados por `branch='HUACHIPA CO'`.

**Regla clave:** Un empleado solo puede pertenecer a UNA cuadrilla. Si ya está en otra, se muestra modal de confirmación para moverlo.

**Stack:** Laravel 11, Vue 3 Composition API, Inertia.js, Tailwind CSS, Pest PHP, ERPNext REST API

---

## Instrucciones para el Agente

### Cargar Skill UI/UX

Antes de crear cualquier archivo `.vue`:
```
C:\dev\agente-tareo-rrhh\skill\ui-ux-designer\skill.md
```

### Ejecutar Plan A (Backend) PRIMERO

```
C:\jarcrow\docs\superpowers\plans\2026-04-29-cuadrillas-huachipa-backend-plan.md
```

Verifica que `php artisan test tests/Feature/CuadrillasTest.php` pase antes de continuar.

### Ejecutar Plan B (Frontend) DESPUÉS de Plan A

```
C:\jarcrow\docs\superpowers\plans\2026-04-29-cuadrillas-huachipa-frontend-plan.md
```

---

## Resumen de lo que se debe implementar

### Plan A — Backend (5 tasks)

**Task 1 — Migration + Model:**
- Migration `create_cuadrillas_table` con campos: `id, codigo(20,unique), nombre(100), supervisor_id(50,nullable), empleados(json,default:[]), estado(enum activo/inactivo,default:activo), created_by(fk users), timestamps`
- Model `App\Models\Cuadrilla` con `$casts=['empleados'=>'array']`, accessor `empleados_count`, scopes `activos()`/`inactivos()`

**Task 2 — ERPNextService:**
- `getEmpleadosHuachipa(): array` — GET Employee con `branch=HUACHIPA CO`, `status=Active`, fields `name,employee_name,custom_nro_documento`
- `searchEmpleadosHuachipa(string $q): array` — mismos campos + filtros de búsqueda por nombre/doc/id, limit 20

**Task 3 — Tests (escribir ANTES de los controllers):**
- Archivo `tests/Feature/CuadrillasTest.php` con 12 tests: auth, list, store, validación sin empleados, código duplicado, 409 conflict, move employee, disable, delete activo (fail), delete inactivo (ok), search auth, search <2 chars vacío, supervisores endpoint

**Task 4 — Controllers y Rutas:**
- `HuachipaController::index()` → stats + `Inertia::render('Huachipa/Index')`
- `CuadrillaController` resourceful con disable extra + lógica de conflictos 409
- `HuachipaEmpleadoController` con `search()` y `supervisores()` (JSON puro)
- Rutas en `routes/web.php` bajo prefix `huachipa`, middleware `auth,verified`

**Lógica de conflictos en store/update:**
```
1. Validar campos básicos
2. Buscar employee_ids del request que ya existen en OTRAS cuadrillas
3. Si hay conflictos Y move_confirmed=false → return JSON 409 con conflicts array
4. Si hay conflictos Y move_confirmed=true → remover employee_ids de cuadrillas anteriores → continuar
5. Guardar cuadrilla
```

**Reglas destroy:** si `estado=activo` → 422. Si `estado=inactivo` → eliminar físico.

### Plan B — Frontend (7 tasks)

**Task 1 — AppLayout + useToast:**
- Añadir nav item `{ name: 'Huachipa', href: '/huachipa', icon: '[SVG path grupos]' }`
- Crear `resources/js/Composables/useToast.js` — `success(msg)`, `error(msg)`, 3s auto-dismiss
- Toast container en AppLayout arriba del `<slot />`

**Task 2 — `Huachipa/Index.vue`:**
- Grid de cards, una card "Cuadrillas" con stats, link a `/huachipa/cuadrillas`
- Gradiente `from-blue-50 to-indigo-50`, borde `border-indigo-200`

**Task 3 — `Cuadrillas/Index.vue`:**
- Tabs Activos | Inactivos → query param `?estado=activo|inactivo`
- Tabla: Código, Nombre, Empleados (count), Supervisor, Estado, Acciones
- Filas inactivas: `bg-gray-50 opacity-75`
- Acciones: Editar (siempre), Deshabilitar (solo activos), Eliminar (solo inactivos)
- Paginación con Inertia links

**Task 4 — `EmpleadoModal.vue` + `ConflictModal.vue`:**
- `EmpleadoModal`: búsqueda live debounce 300ms, min 2 chars, max 3 reintentos con backoff 1s/2s/4s, checkboxes, sección "ya en cuadrilla" readonly
- `ConflictModal`: lista conflictos, botones Cancelar | Sí mover

**Task 5 — `Cuadrillas/Form.vue`:**
- Campos: Código, Nombre, Supervisor (select desde `/huachipa/supervisores`)
- Personal list con tabla, botón remover (bloquear si es supervisor)
- Submit con manejo de 409 → abre ConflictModal → si confirma, reenvía con `move_confirmed=true`
- Toast éxito/error al guardar

**Task 6 — Build + Vite restart:**
```bash
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
docker exec agente-tareo-rrhh-laravel.test-1 pkill -f vite
docker exec -d agente-tareo-rrhh-laravel.test-1 bash -c "cd /var/www/html && npm run dev > /tmp/vite.log 2>&1"
```

---

## Criterios de Éxito

1. `php artisan test tests/Feature/CuadrillasTest.php` → 12 tests PASS
2. `php artisan test` → suite completa sin regresiones
3. `php artisan route:list --path=huachipa` → 7 rutas visibles
4. `GET /huachipa` → carga con card Cuadrillas
5. `GET /huachipa/cuadrillas` → lista con tabs
6. Crear cuadrilla sin empleados → error visible
7. Agregar empleado de otra cuadrilla → ConflictModal → mover funciona
8. Deshabilitar cuadrilla → tab Inactivos
9. Eliminar cuadrilla activa → error. Inactiva → eliminada
10. Build OK, Vite corriendo

---

## Archivos de Salida

**Plan A (backend):**
```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_012a_cuadrillas-huachipa-backend.md
```

**Plan B (frontend) — reporte final:**
```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_012_cuadrillas-huachipa.md
```
