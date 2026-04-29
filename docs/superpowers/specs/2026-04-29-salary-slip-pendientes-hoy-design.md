# Spec: Salary Slips Pendientes de Actualizar Hoy

**Fecha:** 2026-04-29
**Proyecto:** Agente Tareo RRHH (`C:\dev\agente-tareo-rrhh`)
**Archivo de plan:** `docs/superpowers/plans/2026-04-29-salary-slip-pendientes-hoy-plan.md`

---

## Problema

La card amber "Salary Slips actualizados hoy" muestra cuántos slips se modificaron hoy, pero no indica cuántos del mes actual siguen sin actualizar. El equipo de planillas necesita saber qué slips quedan pendientes y quiénes son los empleados afectados.

## Definición

**Pendientes de actualizar** = Salary Slips con `start_date = mesInicio` (mes en curso) cuya fecha de `modified` NO corresponde al día actual (zona horaria `America/Lima`).

## Fuente de datos

| Campo | Valor |
|-------|-------|
| Doctype | `Salary Slip` |
| Filtro de mes | `start_date = Carbon::now('America/Lima')->startOfMonth()->toDateString()` |
| Criterio de exclusión | `date(modified, 'America/Lima') == Carbon::now('America/Lima')->toDateString()` |
| Campos del listado | `name`, `employee`, `employee_name`, `modified` |

## Arquitectura

### Backend — Dos nuevos métodos en `ERPNextService`

**`getSalarySlipsPendientesHoyCount(string $mesInicio): int`**
```php
// GET /api/resource/Salary%20Slip
// fields: ["name","modified"]
// filters: [["start_date","=","$mesInicio"]]
// limit_page_length: None
// PHP filter: excluir donde date(Carbon::parse(modified)->tz('America/Lima')) == hoy
// retorna: int (count de pendientes)
```
Usado por `/api/nomina/stats` para mostrar el badge con count.

**`getSalarySlipsPendientesHoy(string $mesInicio): array`**
```php
// GET /api/resource/Salary%20Slip
// fields: ["name","employee","employee_name","modified"]
// filters: [["start_date","=","$mesInicio"]]
// limit_page_length: None
// PHP filter: excluir donde date(modified, Lima) == hoy
// retorna: [
//   {
//     name: string,           // ej. "SAL-SLIP-00042"
//     employee: string,       // ej. "EMP-0001"
//     employee_name: string,  // ej. "Juan García"
//     modified_fecha: string, // ej. "2026-04-28"
//     modified_hora: string,  // ej. "09:14:05"
//   }
// ]
```
Usado por el endpoint lazy `/api/nomina/slips-pendientes`.

Ambos métodos hacen **una sola call ERP**. Sin N+1.

### Backend — Cambios en `routes/web.php`

**Modificar `/api/nomina/stats`:** añadir una llamada a `getSalarySlipsPendientesHoyCount($mesInicio)` y exponer el resultado:
```json
{
  "slips_pendientes_hoy": 4658
}
```

**Nuevo endpoint `GET /api/nomina/slips-pendientes`** (middleware `auth`):
```php
$mesInicio = Carbon::now('America/Lima')->startOfMonth()->toDateString();
return response()->json(
    app(ERPNextService::class)->getSalarySlipsPendientesHoy($mesInicio)
);
```

### Frontend — `Nomina.vue`

**Nuevos refs:**
```js
const pendientesSlips = ref([])
const loadingPendientes = ref(false)
const showPendientes = ref(false)
```

**`fetchPendientes()`** — idéntico al patrón de `fetchDiff`:
```js
const fetchPendientes = async () => {
    if (showPendientes.value) { showPendientes.value = false; return; }
    if (pendientesSlips.value.length > 0) { showPendientes.value = true; return; }
    loadingPendientes.value = true;
    try {
        const res = await fetch('/api/nomina/slips-pendientes');
        pendientesSlips.value = await res.json();
        showPendientes.value = true;
    } finally {
        loadingPendientes.value = false;
    }
};
```

**Stats ref** — añadir campo:
```js
slips_pendientes_hoy: 0,
```

**Reset en `refreshStats()`:**
```js
pendientesSlips.value = [];
showPendientes.value = false;
```

**Badge en card amber** (solo cuando `slips_pendientes_hoy > 0`):
```html
<button @click="fetchPendientes" :disabled="loadingPendientes">
  <span v-if="loadingPendientes">Buscando...</span>
  <span v-else>
    {{ stats.slips_pendientes_hoy }} pendientes
    {{ showPendientes ? '▲' : '▼' }} Ver detalle
  </span>
</button>
```
Color: amber (`bg-amber-100 text-amber-700`), hover `bg-amber-200`.

**Tabla expandible** debajo de las 3 cards (misma zona que la tabla del diff):

```
Salary Slips pendientes de actualizar ({n})          [×]
┌──────────────┬──────────────┬──────────────────┬──────────────────┐
│ Slip ID      │ Employee ID  │ Nombre           │ Última modif.    │
├──────────────┼──────────────┼──────────────────┼──────────────────┤
│ SAL-SLIP-042 │ EMP-0001     │ Juan García      │ 2026-04-28 09:14 │
└──────────────┴──────────────┴──────────────────┴──────────────────┘
```
- Borde y header: amber
- `modified_fecha` + `modified_hora` mostrados juntos: `2026-04-28 09:14`

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `app/Services/ERPNextService.php` | Añadir `getSalarySlipsPendientesHoyCount()` y `getSalarySlipsPendientesHoy()` |
| `routes/web.php` | Añadir `slips_pendientes_hoy` a stats + nuevo endpoint `/api/nomina/slips-pendientes` |
| `resources/js/Pages/Nomina.vue` | Badge amber + tabla expandible + nuevos refs + reset |

## Criterios de aceptación

1. `/api/nomina/stats` retorna `slips_pendientes_hoy` (int)
2. Badge "X pendientes ▼ Ver detalle" visible en card amber cuando count > 0
3. Badge no visible cuando todos los slips del mes fueron modificados hoy
4. Click en badge → fetch lazy → tabla con columnas: Slip ID, Employee ID, Nombre, Última modif.
5. Toggle: segundo click cierra, `×` cierra
6. "Actualizar" limpia caché de pendientes y fuerza re-fetch en siguiente click
7. Sin N+1: 1 call ERP para el count en stats, 1 call ERP separada para la lista (lazy)

## Archivo de salida del agente

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_009_salary-slip-pendientes-hoy.md
```

Contenido mínimo: checklist con `[x]`, output de tests, resultado visual, estado final.
