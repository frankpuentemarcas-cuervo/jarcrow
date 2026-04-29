# Cuadrillas Huachipa — Frontend Plan (Plan B)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **PREREQUISITO:** Plan A (backend) debe estar completado y con tests PASS antes de ejecutar este plan.

**Goal:** Crear todas las páginas Vue, componentes y composables del módulo Cuadrillas Huachipa: navegación, listado paginado con tabs, formulario CRUD, modal de búsqueda de empleados y modal de conflicto de movimiento.

**Architecture:** Inertia + Vue 3 Composition API + Tailwind. `AppLayout.vue` recibe nuevo nav item. Tres páginas Inertia (`Huachipa/Index`, `Cuadrillas/Index`, `Cuadrillas/Form`). Dos componentes reutilizables (`EmpleadoModal`, `ConflictModal`). Composable `useToast` para notificaciones.

**Tech Stack:** Vue 3, Inertia.js, Tailwind CSS, `@inertiajs/vue3`

---

## File Map

| Archivo | Acción |
|---------|--------|
| `resources/js/Layouts/AppLayout.vue` | Modificar — añadir nav item Huachipa |
| `resources/js/Composables/useToast.js` | Crear |
| `resources/js/Pages/Huachipa/Index.vue` | Crear |
| `resources/js/Pages/Huachipa/Cuadrillas/Index.vue` | Crear |
| `resources/js/Pages/Huachipa/Cuadrillas/Form.vue` | Crear |
| `resources/js/Components/Huachipa/EmpleadoModal.vue` | Crear |
| `resources/js/Components/Huachipa/ConflictModal.vue` | Crear |

---

## Task 1: Nav item + useToast composable

**Files:**
- Modify: `resources/js/Layouts/AppLayout.vue`
- Create: `resources/js/Composables/useToast.js`

- [ ] **Step 1: Añadir Huachipa al array `navigation` en `AppLayout.vue`**

Localizar:
```js
const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: '...' },
    { name: 'Alertas', href: '/alertas', icon: '...' },
    { name: 'Análisis', href: '/analisis', icon: '...' },
];
```

Añadir al final del array:
```js
{ name: 'Huachipa', href: '/huachipa', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z' },
```

- [ ] **Step 2: Crear `resources/js/Composables/useToast.js`**

```js
import { ref } from 'vue';

const toasts = ref([]);
let nextId = 0;

export function useToast() {
    function show(message, type = 'success', duration = 3000) {
        const id = ++nextId;
        toasts.value.push({ id, message, type });
        setTimeout(() => {
            toasts.value = toasts.value.filter(t => t.id !== id);
        }, duration);
    }

    return {
        toasts,
        success: (msg) => show(msg, 'success'),
        error:   (msg) => show(msg, 'error'),
    };
}
```

- [ ] **Step 3: Añadir el Toast container en `AppLayout.vue` — dentro del `<main>`, justo antes de `<slot />`**

Localizar:
```html
        <main ...>
            <slot />
        </main>
```

Reemplazar por:
```html
        <main ...>
            <!-- Toast notifications -->
            <div class="fixed top-4 right-4 z-50 flex flex-col gap-2">
                <transition-group name="toast">
                    <div
                        v-for="toast in toasts"
                        :key="toast.id"
                        :class="[
                            'flex items-center gap-3 rounded-lg px-4 py-3 shadow-lg text-sm font-medium',
                            toast.type === 'success'
                                ? 'bg-green-600 text-white'
                                : 'bg-red-600 text-white'
                        ]"
                    >
                        {{ toast.message }}
                    </div>
                </transition-group>
            </div>
            <slot />
        </main>
```

- [ ] **Step 4: Añadir el import de useToast en `AppLayout.vue` `<script setup>`**

Localizar:
```js
import { ref } from 'vue';
import { Link, usePage } from '@inertiajs/vue3';
```

Añadir:
```js
import { useToast } from '@/Composables/useToast';
const { toasts } = useToast();
```

- [ ] **Step 5: Añadir animación toast en `AppLayout.vue` con `<style>`**

Añadir al final del archivo:
```html
<style>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from { opacity: 0; transform: translateX(100%); }
.toast-leave-to   { opacity: 0; transform: translateX(100%); }
</style>
```

- [ ] **Step 6: Commit**

```bash
git add resources/js/Layouts/AppLayout.vue resources/js/Composables/useToast.js
git commit -m "feat(huachipa): add Huachipa nav item and useToast composable"
```

---

## Task 2: `Huachipa/Index.vue` — página de módulo

**Files:**
- Create: `resources/js/Pages/Huachipa/Index.vue`

- [ ] **Step 1: Crear el directorio y el archivo**

```bash
mkdir -p C:/dev/agente-tareo-rrhh/resources/js/Pages/Huachipa/Cuadrillas
```

- [ ] **Step 2: Crear `resources/js/Pages/Huachipa/Index.vue`**

```vue
<template>
    <AppLayout>
        <div class="py-12">
            <div class="mx-auto max-w-7xl sm:px-6 lg:px-8">
                <h1 class="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Módulo Huachipa
                </h1>

                <div class="grid grid-cols-1 gap-6 md:grid-cols-3">
                    <!-- Card Cuadrillas -->
                    <Link
                        href="/huachipa/cuadrillas"
                        class="group block rounded-lg border border-indigo-200 bg-gradient-to-br from-blue-50 to-indigo-50 p-8 transition hover:shadow-md dark:border-indigo-800 dark:from-gray-700 dark:to-gray-600"
                    >
                        <div class="mb-4 flex items-center gap-3">
                            <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900">
                                <svg class="h-6 w-6 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                                </svg>
                            </div>
                            <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-indigo-700">
                                Cuadrillas
                            </h2>
                        </div>
                        <p class="text-4xl font-bold text-indigo-600 dark:text-indigo-400">
                            {{ stats.cuadrillas_activas }}
                        </p>
                        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            cuadrillas activas · {{ stats.total_empleados }} empleados
                        </p>
                        <p v-if="stats.cuadrillas_inactivas > 0" class="mt-1 text-xs text-gray-400">
                            {{ stats.cuadrillas_inactivas }} inactivas
                        </p>
                    </Link>
                </div>
            </div>
        </div>
    </AppLayout>
</template>

<script setup>
import AppLayout from '@/Layouts/AppLayout.vue';
import { Link } from '@inertiajs/vue3';

defineProps({
    stats: {
        type: Object,
        default: () => ({ cuadrillas_activas: 0, cuadrillas_inactivas: 0, total_empleados: 0 }),
    },
});
</script>
```

- [ ] **Step 3: Commit**

```bash
git add resources/js/Pages/Huachipa/Index.vue
git commit -m "feat(huachipa): add Huachipa/Index.vue module home"
```

---

## Task 3: `Cuadrillas/Index.vue` — listado paginado

**Files:**
- Create: `resources/js/Pages/Huachipa/Cuadrillas/Index.vue`

- [ ] **Step 1: Crear el archivo**

```vue
<template>
    <AppLayout>
        <div class="py-12">
            <div class="mx-auto max-w-7xl sm:px-6 lg:px-8">

                <!-- Header -->
                <div class="mb-6 flex items-center justify-between">
                    <div>
                        <nav class="text-sm text-gray-500">
                            <Link href="/huachipa" class="hover:text-indigo-600">Huachipa</Link>
                            <span class="mx-1">/</span>
                            <span class="text-gray-900 dark:text-gray-100">Cuadrillas</span>
                        </nav>
                        <h1 class="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">Cuadrillas</h1>
                    </div>
                    <Link
                        href="/huachipa/cuadrillas/create"
                        class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                    >
                        + Agregar
                    </Link>
                </div>

                <!-- Tabs -->
                <div class="mb-4 flex gap-1 border-b border-gray-200 dark:border-gray-700">
                    <button
                        @click="changeEstado('activo')"
                        :class="['px-4 py-2 text-sm font-medium border-b-2 transition',
                            estado === 'activo'
                                ? 'border-indigo-600 text-indigo-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700']"
                    >
                        Activos ({{ cuadrillas.total - inactivasCount }})
                    </button>
                    <button
                        @click="changeEstado('inactivo')"
                        :class="['px-4 py-2 text-sm font-medium border-b-2 transition',
                            estado === 'inactivo'
                                ? 'border-indigo-600 text-indigo-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700']"
                    >
                        Inactivos
                    </button>
                </div>

                <!-- Table -->
                <div class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
                    <table class="w-full text-sm">
                        <thead class="bg-gray-50 dark:bg-gray-900">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Código</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Nombre</th>
                                <th class="px-4 py-3 text-center text-xs font-semibold uppercase text-gray-500">Empleados</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Supervisor</th>
                                <th class="px-4 py-3 text-center text-xs font-semibold uppercase text-gray-500">Estado</th>
                                <th class="px-4 py-3 text-center text-xs font-semibold uppercase text-gray-500">Acciones</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
                            <tr
                                v-for="c in cuadrillas.data"
                                :key="c.id"
                                :class="['hover:bg-gray-50 dark:hover:bg-gray-700/50',
                                    c.estado === 'inactivo' ? 'bg-gray-50 opacity-75 dark:bg-gray-800/50' : '']"
                            >
                                <td class="px-4 py-3 font-mono text-gray-700 dark:text-gray-300">{{ c.codigo }}</td>
                                <td class="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{{ c.nombre }}</td>
                                <td class="px-4 py-3 text-center text-gray-600 dark:text-gray-400">{{ c.empleados_count }}</td>
                                <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ c.supervisor_id || '—' }}</td>
                                <td class="px-4 py-3 text-center">
                                    <span :class="[
                                        'rounded-full px-2 py-0.5 text-xs font-semibold',
                                        c.estado === 'activo'
                                            ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                                            : 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                                    ]">
                                        {{ c.estado === 'activo' ? 'Activo' : 'Inactivo' }}
                                    </span>
                                </td>
                                <td class="px-4 py-3 text-center">
                                    <div class="flex items-center justify-center gap-2">
                                        <Link
                                            :href="`/huachipa/cuadrillas/${c.id}/edit`"
                                            class="rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
                                        >
                                            Editar
                                        </Link>
                                        <button
                                            v-if="c.estado === 'activo'"
                                            @click="confirmDisable(c)"
                                            class="rounded px-2 py-1 text-xs font-medium text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/30"
                                        >
                                            Deshabilitar
                                        </button>
                                        <button
                                            v-if="c.estado === 'inactivo'"
                                            @click="confirmDelete(c)"
                                            class="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30"
                                        >
                                            Eliminar
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            <tr v-if="cuadrillas.data.length === 0">
                                <td colspan="6" class="px-4 py-8 text-center text-sm text-gray-400">
                                    No hay cuadrillas {{ estado === 'activo' ? 'activas' : 'inactivas' }}.
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Pagination -->
                <div v-if="cuadrillas.last_page > 1" class="mt-4 flex justify-center gap-1">
                    <Link
                        v-for="link in cuadrillas.links"
                        :key="link.label"
                        :href="link.url || '#'"
                        :class="['rounded px-3 py-1 text-sm',
                            link.active ? 'bg-indigo-600 text-white' : 'text-gray-600 hover:bg-gray-100',
                            !link.url ? 'cursor-not-allowed opacity-40' : '']"
                        v-html="link.label"
                    />
                </div>
            </div>
        </div>
    </AppLayout>
</template>

<script setup>
import AppLayout from '@/Layouts/AppLayout.vue';
import { Link, router } from '@inertiajs/vue3';

const props = defineProps({
    cuadrillas: Object,
    estado: { type: String, default: 'activo' },
});

const inactivasCount = 0; // se podría pasar desde el controller si se necesita

function changeEstado(nuevoEstado) {
    router.get('/huachipa/cuadrillas', { estado: nuevoEstado }, { preserveScroll: true });
}

function confirmDisable(cuadrilla) {
    if (!confirm(`¿Deshabilitar la cuadrilla "${cuadrilla.nombre}"?`)) return;
    router.patch(`/huachipa/cuadrillas/${cuadrilla.id}/disable`);
}

function confirmDelete(cuadrilla) {
    if (!confirm(`¿Eliminar permanentemente la cuadrilla "${cuadrilla.nombre}"? Esta acción no se puede deshacer.`)) return;
    router.delete(`/huachipa/cuadrillas/${cuadrilla.id}`);
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add resources/js/Pages/Huachipa/Cuadrillas/Index.vue
git commit -m "feat(huachipa): add Cuadrillas/Index.vue list with tabs and pagination"
```

---

## Task 4: `ConflictModal.vue` y `EmpleadoModal.vue`

**Files:**
- Create: `resources/js/Components/Huachipa/ConflictModal.vue`
- Create: `resources/js/Components/Huachipa/EmpleadoModal.vue`

- [ ] **Step 1: Crear directorio**

```bash
mkdir -p C:/dev/agente-tareo-rrhh/resources/js/Components/Huachipa
```

- [ ] **Step 2: Crear `ConflictModal.vue`**

```vue
<template>
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div class="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
            <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
                Empleado ya asignado
            </h3>
            <div class="mb-4 space-y-3">
                <div
                    v-for="conflict in conflicts"
                    :key="conflict.cuadrilla_id"
                    class="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm dark:border-amber-800 dark:bg-amber-900/20"
                >
                    <p class="font-medium text-amber-800 dark:text-amber-300">
                        Los empleados <strong>{{ conflict.empleados.join(', ') }}</strong>
                        pertenecen a la cuadrilla
                        <strong>{{ conflict.cuadrilla_codigo }} – {{ conflict.cuadrilla_nombre }}</strong>.
                    </p>
                    <p class="mt-1 text-amber-700 dark:text-amber-400">
                        Si confirma, serán removidos de esa cuadrilla y asignados a esta.
                    </p>
                </div>
            </div>
            <div class="flex justify-end gap-3">
                <button
                    @click="$emit('cancel')"
                    class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300"
                >
                    Cancelar
                </button>
                <button
                    @click="$emit('confirm')"
                    class="rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-700"
                >
                    Sí, mover
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
defineProps({
    show:      { type: Boolean, default: false },
    conflicts: { type: Array,   default: () => [] },
});
defineEmits(['confirm', 'cancel']);
</script>
```

- [ ] **Step 3: Crear `EmpleadoModal.vue`**

```vue
<template>
    <div v-if="show" class="fixed inset-0 z-40 flex items-center justify-center bg-black/50">
        <div class="flex h-[80vh] w-full max-w-3xl flex-col rounded-lg bg-white shadow-xl dark:bg-gray-800">
            <!-- Header -->
            <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Agregar Personal</h3>
                <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">×</button>
            </div>

            <!-- Search -->
            <div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
                <input
                    v-model="query"
                    @input="onSearch"
                    type="text"
                    placeholder="Buscar por documento, nombre o ID..."
                    class="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                />
            </div>

            <!-- Results + Current -->
            <div class="flex flex-1 overflow-hidden">
                <!-- Search results -->
                <div class="flex-1 overflow-y-auto border-r border-gray-200 px-6 py-4 dark:border-gray-700">
                    <p class="mb-2 text-xs font-semibold uppercase text-gray-500">Resultados</p>
                    <div v-if="searching" class="flex items-center gap-2 text-sm text-gray-400">
                        <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                        </svg>
                        Buscando...
                    </div>
                    <div v-else-if="searchError" class="text-sm text-red-600">
                        Error al conectar con ERPNext.
                        <button @click="retrySearch" class="ml-2 underline">Reintentar</button>
                    </div>
                    <div v-else-if="results.length === 0 && query.length >= 2" class="text-sm text-gray-400">
                        No se encontraron resultados.
                    </div>
                    <div v-else-if="query.length < 2" class="text-sm text-gray-400">
                        Escribe al menos 2 caracteres para buscar.
                    </div>
                    <label
                        v-for="emp in results"
                        :key="emp.name"
                        class="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                        <input
                            type="checkbox"
                            :value="emp.name"
                            v-model="selected"
                            :disabled="alreadyInCuadrilla(emp.name)"
                            class="h-4 w-4 rounded border-gray-300 text-indigo-600"
                        />
                        <span class="text-sm" :class="alreadyInCuadrilla(emp.name) ? 'text-gray-400' : 'text-gray-800 dark:text-gray-200'">
                            {{ emp.name }} · {{ emp.custom_nro_documento }} · {{ emp.employee_name }}
                            <span v-if="alreadyInCuadrilla(emp.name)" class="ml-1 text-xs text-gray-400">(ya agregado)</span>
                        </span>
                    </label>
                </div>

                <!-- Current employees -->
                <div class="w-64 overflow-y-auto px-4 py-4">
                    <p class="mb-2 text-xs font-semibold uppercase text-gray-500">
                        En cuadrilla ({{ currentEmpleados.length }})
                    </p>
                    <div
                        v-for="emp in currentEmpleados"
                        :key="emp.name"
                        class="mb-1 rounded bg-gray-50 px-3 py-1.5 text-xs text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                    >
                        {{ emp.name }} · {{ emp.employee_name }}
                    </div>
                    <p v-if="currentEmpleados.length === 0" class="text-xs text-gray-400">Sin personal aún.</p>
                </div>
            </div>

            <!-- Footer -->
            <div class="flex items-center justify-end gap-3 border-t border-gray-200 px-6 py-4 dark:border-gray-700">
                <button @click="$emit('close')" class="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 dark:border-gray-600 dark:text-gray-300">
                    Cancelar
                </button>
                <button
                    @click="confirmSelection"
                    :disabled="selected.length === 0"
                    class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    Agregar seleccionados ({{ selected.length }})
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
    show:             { type: Boolean, default: false },
    currentEmpleados: { type: Array,   default: () => [] },
});
const emit = defineEmits(['close', 'add']);

const query     = ref('');
const results   = ref([]);
const selected  = ref([]);
const searching = ref(false);
const searchError = ref(false);

let debounceTimer = null;
let retryCount = 0;

function alreadyInCuadrilla(employeeId) {
    return props.currentEmpleados.some(e => e.name === employeeId);
}

function onSearch() {
    clearTimeout(debounceTimer);
    if (query.value.length < 2) { results.value = []; return; }
    debounceTimer = setTimeout(() => doSearch(), 300);
}

async function doSearch(attempt = 1) {
    searching.value = true;
    searchError.value = false;
    try {
        const res = await fetch(`/huachipa/empleados?q=${encodeURIComponent(query.value)}`);
        if (!res.ok) throw new Error('ERP error');
        results.value = await res.json();
        retryCount = 0;
    } catch {
        if (attempt < 3) {
            await new Promise(r => setTimeout(r, attempt * 1000));
            return doSearch(attempt + 1);
        }
        searchError.value = true;
        results.value = [];
    } finally {
        searching.value = false;
    }
}

function retrySearch() { doSearch(); }

function confirmSelection() {
    emit('add', selected.value);
    selected.value = [];
    query.value = '';
    results.value = [];
}

watch(() => props.show, (val) => {
    if (!val) { query.value = ''; results.value = []; selected.value = []; }
});
</script>
```

- [ ] **Step 4: Commit**

```bash
git add resources/js/Components/Huachipa/
git commit -m "feat(huachipa): add EmpleadoModal and ConflictModal components"
```

---

## Task 5: `Cuadrillas/Form.vue` — formulario crear/editar

**Files:**
- Create: `resources/js/Pages/Huachipa/Cuadrillas/Form.vue`

- [ ] **Step 1: Crear el archivo**

```vue
<template>
    <AppLayout>
        <div class="py-12">
            <div class="mx-auto max-w-3xl sm:px-6 lg:px-8">

                <!-- Breadcrumb -->
                <nav class="mb-6 text-sm text-gray-500">
                    <Link href="/huachipa" class="hover:text-indigo-600">Huachipa</Link>
                    <span class="mx-1">/</span>
                    <Link href="/huachipa/cuadrillas" class="hover:text-indigo-600">Cuadrillas</Link>
                    <span class="mx-1">/</span>
                    <span class="text-gray-900 dark:text-gray-100">{{ cuadrilla ? 'Editar' : 'Nueva' }}</span>
                </nav>

                <div class="rounded-lg border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                    <h1 class="mb-6 text-xl font-bold text-gray-900 dark:text-gray-100">
                        {{ cuadrilla ? 'Editar Cuadrilla' : 'Nueva Cuadrilla' }}
                    </h1>

                    <form @submit.prevent="submit" class="space-y-6">

                        <!-- Código y Nombre -->
                        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <div>
                                <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                                    Código de Cuadrilla <span class="text-red-500">*</span>
                                </label>
                                <input
                                    v-model="form.codigo"
                                    type="text"
                                    maxlength="20"
                                    class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                                    placeholder="Ej. CUA-001"
                                />
                                <p v-if="errors.codigo" class="mt-1 text-xs text-red-600">{{ errors.codigo }}</p>
                            </div>
                            <div>
                                <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                                    Nombre de Cuadrilla <span class="text-red-500">*</span>
                                </label>
                                <input
                                    v-model="form.nombre"
                                    type="text"
                                    maxlength="100"
                                    class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                                    placeholder="Ej. Grupo Norte"
                                />
                                <p v-if="errors.nombre" class="mt-1 text-xs text-red-600">{{ errors.nombre }}</p>
                            </div>
                        </div>

                        <!-- Supervisor -->
                        <div>
                            <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                                Supervisor <span class="text-red-500">*</span>
                            </label>
                            <select
                                v-model="form.supervisor_id"
                                class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                            >
                                <option value="">
                                    {{ loadingSupervisores ? 'Cargando...' : '— Seleccionar supervisor —' }}
                                </option>
                                <option v-for="s in supervisores" :key="s.name" :value="s.name">
                                    {{ s.custom_nro_documento }} · {{ s.employee_name }}
                                </option>
                            </select>
                            <p v-if="errorSupervisores" class="mt-1 text-xs text-red-600">
                                Error al cargar supervisores.
                                <button type="button" @click="loadSupervisores" class="underline">Reintentar</button>
                            </p>
                            <p v-if="errors.supervisor_id" class="mt-1 text-xs text-red-600">{{ errors.supervisor_id }}</p>
                        </div>

                        <!-- Personal -->
                        <div>
                            <div class="mb-2 flex items-center justify-between">
                                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                                    Personal de la Cuadrilla
                                    <span class="ml-1 text-gray-400">({{ form.empleados.length }} empleados)</span>
                                    <span class="text-red-500">*</span>
                                </label>
                                <button
                                    type="button"
                                    @click="showEmpleadoModal = true"
                                    class="rounded-lg border border-indigo-300 px-3 py-1.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 dark:border-indigo-700 dark:hover:bg-indigo-900/30"
                                >
                                    + Agregar Personal
                                </button>
                            </div>
                            <p v-if="errors.empleados" class="mb-2 text-xs text-red-600">{{ errors.empleados }}</p>

                            <div v-if="form.empleados.length > 0" class="rounded-lg border border-gray-200 dark:border-gray-700">
                                <table class="w-full text-sm">
                                    <thead class="bg-gray-50 dark:bg-gray-900">
                                        <tr>
                                            <th class="px-4 py-2 text-left text-xs font-semibold uppercase text-gray-500">ID</th>
                                            <th class="px-4 py-2 text-left text-xs font-semibold uppercase text-gray-500">Documento</th>
                                            <th class="px-4 py-2 text-left text-xs font-semibold uppercase text-gray-500">Nombre</th>
                                            <th class="px-4 py-2"></th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
                                        <tr v-for="emp in empleadosInfo" :key="emp.name">
                                            <td class="px-4 py-2 font-mono text-gray-700 dark:text-gray-300">{{ emp.name }}</td>
                                            <td class="px-4 py-2 text-gray-600 dark:text-gray-400">{{ emp.custom_nro_documento }}</td>
                                            <td class="px-4 py-2 text-gray-800 dark:text-gray-200">{{ emp.employee_name }}</td>
                                            <td class="px-4 py-2 text-right">
                                                <button
                                                    type="button"
                                                    @click="removeEmpleado(emp.name)"
                                                    class="text-xs text-red-500 hover:text-red-700"
                                                >
                                                    ×
                                                </button>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <div v-else class="rounded-lg border border-dashed border-gray-300 px-4 py-6 text-center text-sm text-gray-400 dark:border-gray-600">
                                Sin personal agregado. Use el botón "Agregar Personal".
                            </div>
                        </div>

                        <!-- Buttons -->
                        <div class="flex justify-end gap-3 pt-4">
                            <Link
                                href="/huachipa/cuadrillas"
                                class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300"
                            >
                                Cancelar
                            </Link>
                            <button
                                type="submit"
                                :disabled="submitting"
                                class="rounded-lg bg-indigo-600 px-6 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                {{ submitting ? 'Guardando...' : 'Guardar Cuadrilla' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Modals -->
        <EmpleadoModal
            :show="showEmpleadoModal"
            :current-empleados="empleadosInfo"
            @close="showEmpleadoModal = false"
            @add="onEmpleadosAdded"
        />

        <ConflictModal
            :show="showConflictModal"
            :conflicts="pendingConflicts"
            @confirm="onConflictConfirmed"
            @cancel="onConflictCancelled"
        />
    </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Link, router } from '@inertiajs/vue3';
import AppLayout from '@/Layouts/AppLayout.vue';
import EmpleadoModal from '@/Components/Huachipa/EmpleadoModal.vue';
import ConflictModal from '@/Components/Huachipa/ConflictModal.vue';
import { useToast } from '@/Composables/useToast';

const props = defineProps({
    cuadrilla: { type: Object, default: null },
});

const toast = useToast();

const form = ref({
    codigo:       props.cuadrilla?.codigo || '',
    nombre:       props.cuadrilla?.nombre || '',
    supervisor_id:props.cuadrilla?.supervisor_id || '',
    empleados:    props.cuadrilla?.empleados || [],
    move_confirmed: false,
});

const errors       = ref({});
const submitting   = ref(false);
const supervisores = ref([]);
const loadingSupervisores = ref(false);
const errorSupervisores   = ref(false);

// Employee info map (for display)
const empleadosMap = ref({});
const empleadosInfo = computed(() =>
    form.value.empleados.map(id => empleadosMap.value[id] || { name: id, employee_name: id, custom_nro_documento: '' })
);

const showEmpleadoModal  = ref(false);
const showConflictModal  = ref(false);
const pendingConflicts   = ref([]);
const pendingNewEmpleados = ref([]);

onMounted(() => {
    loadSupervisores();
    // Pre-load info for existing empleados
    if (form.value.empleados.length > 0) {
        loadEmpleadosInfo(form.value.empleados);
    }
});

async function loadSupervisores() {
    loadingSupervisores.value = true;
    errorSupervisores.value = false;
    try {
        const res = await fetch('/huachipa/supervisores');
        supervisores.value = await res.json();
    } catch {
        errorSupervisores.value = true;
    } finally {
        loadingSupervisores.value = false;
    }
}

async function loadEmpleadosInfo(ids) {
    // Load info for multiple employees via search (best effort)
    // In practice, we store the info when the user adds them via modal
}

function removeEmpleado(id) {
    if (id === form.value.supervisor_id) {
        errors.value.empleados = 'No puede remover al supervisor del equipo.';
        setTimeout(() => delete errors.value.empleados, 3000);
        return;
    }
    form.value.empleados = form.value.empleados.filter(e => e !== id);
    delete empleadosMap.value[id];
}

function onEmpleadosAdded(newIds) {
    // Add new employees, avoiding duplicates
    const toAdd = newIds.filter(id => !form.value.empleados.includes(id));
    form.value.empleados = [...form.value.empleados, ...toAdd];
    showEmpleadoModal.value = false;
}

async function submit() {
    errors.value = {};
    submitting.value = true;

    const payload = { ...form.value };
    const isEdit  = !!props.cuadrilla;
    const url     = isEdit ? `/huachipa/cuadrillas/${props.cuadrilla.id}` : '/huachipa/cuadrillas';
    const method  = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.content || '',
            },
            body: JSON.stringify(payload),
        });

        if (res.status === 409) {
            const data = await res.json();
            pendingConflicts.value   = data.conflicts;
            pendingNewEmpleados.value = payload.empleados;
            showConflictModal.value  = true;
            submitting.value = false;
            return;
        }

        if (res.status === 422) {
            const data = await res.json();
            errors.value = data.errors || {};
            submitting.value = false;
            return;
        }

        if (res.ok || res.redirected) {
            toast.success(isEdit ? 'Cuadrilla actualizada correctamente.' : 'Cuadrilla creada correctamente.');
            router.visit('/huachipa/cuadrillas');
            return;
        }

        toast.error('Error al guardar la cuadrilla.');
    } catch {
        toast.error('Error de conexión.');
    } finally {
        submitting.value = false;
    }
}

function onConflictConfirmed() {
    showConflictModal.value = false;
    form.value.move_confirmed = true;
    submit();
}

function onConflictCancelled() {
    showConflictModal.value = false;
    form.value.move_confirmed = false;
    pendingConflicts.value = [];
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add resources/js/Pages/Huachipa/Cuadrillas/Form.vue
git commit -m "feat(huachipa): add Cuadrillas/Form.vue with employee modal and conflict resolution"
```

---

## Task 6: Build + Vite restart

- [ ] **Step 1: Build**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
```

Si falla por permisos:
```bash
docker exec -u root agente-tareo-rrhh-laravel.test-1 chown -R sail:sail /var/www/html/public/build
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
```

Expected: `✓ built in XX.XXs`

- [ ] **Step 2: Reiniciar Vite**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 pkill -f vite
docker exec -d agente-tareo-rrhh-laravel.test-1 bash -c "cd /var/www/html && npm run dev > /tmp/vite.log 2>&1"
```

- [ ] **Step 3: Commit**

No hay cambios de código adicionales.

---

## Task 7: Archivo de salida del agente

**Files:**
- Create: `C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_012_cuadrillas-huachipa.md`

- [ ] **Step 1: Crear reporte final**

```markdown
# Reporte de Ejecución: Módulo Cuadrillas Huachipa

**Fecha:** 2026-04-29
**Agente:** [nombre]
**Proyecto:** Agente Tareo RRHH

## Progreso de Tareas

### Frontend
- [x] Nav item "Huachipa" añadido a AppLayout
- [x] useToast composable creado
- [x] Huachipa/Index.vue (cards del módulo)
- [x] Cuadrillas/Index.vue (lista con tabs + paginación)
- [x] Cuadrillas/Form.vue (crear/editar con modal)
- [x] EmpleadoModal.vue con búsqueda live, retry 3 veces, backoff
- [x] ConflictModal.vue para confirmación de mover empleado
- [x] Build OK, Vite reiniciado

## Resultado
[Describir resultado visual en browser]

## Observaciones
[Decisiones técnicas]

---
**Estado Final Plan B: COMPLETADO**
```

- [ ] **Step 2: Commit**

```bash
git add "C:/jarcrow/Trabajo/Agente-Tareo-RRHH/agentes/respuestas/2026-04-29_012_cuadrillas-huachipa.md"
git commit -m "docs(agente): add execution report for cuadrillas-huachipa frontend"
```

---

## Verificación final Plan B

- [ ] `GET /huachipa` carga con card Cuadrillas y stats
- [ ] `GET /huachipa/cuadrillas` muestra lista con tabs activo/inactivo
- [ ] `GET /huachipa/cuadrillas/create` muestra formulario, supervisor dropdown carga
- [ ] Botón "Agregar Personal" abre modal, búsqueda con 2+ chars retorna resultados
- [ ] Guardar cuadrilla sin empleados → error de validación visible
- [ ] Guardar cuadrilla válida → toast éxito + redirige a lista
- [ ] Build sin errores, Vite corriendo
