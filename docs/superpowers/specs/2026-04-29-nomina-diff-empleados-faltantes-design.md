# Spec: Nómina Diff — Empleados sin Nómina Generada

**Fecha:** 2026-04-29
**Proyecto:** Agente Tareo RRHH (`C:\dev\agente-tareo-rrhh`)
**Archivo de plan:** `docs/superpowers/plans/2026-04-29-nomina-diff-empleados-faltantes-plan.md`

---

## Problema

La vista `/nomina` muestra la diferencia entre `total_deben` y `nominas_generadas` pero no identifica qué empleados específicos carecen de nómina. El usuario necesita saber quién falta para actuar.

## Fuentes de datos

| Campo | Origen | Valor |
|-------|--------|-------|
| `employee_id` local | `colaboradores.employee_id` | Nombre del doctype `Employee` en ERPNext (ej. `EMP-0042`) |
| Salary Slip existentes | ERPNext `Salary Slip.employee` | Mismo formato que `employee_id` |
| Criterio `total_deben` | `colaboradores` local | `estado IN ('Activo','No Reportado')` + `estado='Inactivo' AND fecha_de_relevo BETWEEN mesInicio AND mesFin` |

## Arquitectura

### Backend

**Nuevo método `ERPNextService::getSalarySlipEmployees(string $startDate): array`**
- `GET /api/resource/Salary%20Slip`
- `fields: ["employee"]`
- `filters: [["start_date","=","$startDate"]]`
- `limit_page_length: None`
- Retorna array plano de strings: `["EMP-0001", "EMP-0042", ...]`

**Nuevo endpoint `GET /api/nomina/diff`** (en `routes/web.php`, con middleware `auth`)
```
1. $mesInicio = Carbon::now('America/Lima')->startOfMonth()->toDateString()
2. $mesFin    = Carbon::now('America/Lima')->endOfMonth()->toDateString()

3. $empleadosDeben = Colaborador::query()
     ->where(function($q) use ($mesInicio, $mesFin) {
         $q->whereIn('estado', ['Activo', 'No Reportado'])
           ->orWhere(function($q2) use ($mesInicio, $mesFin) {
               $q2->where('estado', 'Inactivo')
                  ->whereBetween('fecha_de_relevo', [$mesInicio, $mesFin]);
           });
     })
     ->select('employee_id', 'nombre', 'apellido', 'estado')
     ->get();

4. $conNomina = ERPNextService::getSalarySlipEmployees($mesInicio);

5. $sinNomina = $empleadosDeben->filter(
     fn($c) => !in_array($c->employee_id, $conNomina)
   )->values();

6. return response()->json($sinNomina);
```

Complejidad: 2 queries totales (1 local, 1 ERP) — sin N+1.

### Frontend (`Nomina.vue`)

**Nuevos refs:**
```js
const missingEmployees = ref([])
const loadingDiff = ref(false)
const showDiff = ref(false)
```

**Badge clickeable (solo cuando `diferencia > 0`):**
```html
<button @click="fetchDiff">
  Faltan {{ diferencia }} nóminas  [▼ Ver detalle]
</button>
```

**Función `fetchDiff`:**
```js
const fetchDiff = async () => {
  if (showDiff.value) { showDiff.value = false; return; }
  if (missingEmployees.value.length > 0) { showDiff.value = true; return; } // cache
  loadingDiff.value = true;
  try {
    const res = await fetch('/api/nomina/diff');
    missingEmployees.value = await res.json();
    showDiff.value = true;
  } finally {
    loadingDiff.value = false;
  }
};
```

**Tabla expandible (debajo de las cards):**
```
Empleados sin nómina generada               [×]
┌──────────────┬──────────────────┬──────────────┐
│ ID           │ Nombre           │ Estado       │
├──────────────┼──────────────────┼──────────────┤
│ EMP-0042     │ García, Juan     │ Activo       │
└──────────────┴──────────────────┴──────────────┘
```

Cache local: si `missingEmployees` ya tiene datos, no re-fetcha. Se invalida al hacer "Actualizar" en el botón principal.

**Reset al refrescar stats:** `refreshStats` debe limpiar `missingEmployees.value = []` y `showDiff.value = false`.

## Skill del agente ejecutor

Para los cambios en `Nomina.vue` (Vue 3 + Tailwind), el agente debe cargar:
```
C:\dev\agente-tareo-rrhh\skill\ui-ux-designer\skill.md
```

El backend (PHP en `ERPNextService.php` y `web.php`) sigue los patrones ya establecidos en el proyecto — no requiere skill adicional.

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `app/Services/ERPNextService.php` | Añadir `getSalarySlipEmployees()` |
| `routes/web.php` | Añadir `GET /api/nomina/diff` |
| `resources/js/Pages/Nomina.vue` | Badge clickeable + tabla expandible |

## Criterios de aceptación

1. Con diferencia > 0: badge "Faltan X nóminas" es clickeable, al hacer click muestra tabla con empleados faltantes
2. Con diferencia = 0: badge "✓ Completo" no es clickeable, sin tabla
3. Segunda click en badge colapsa la tabla (toggle)
4. Click en "Actualizar" limpia el estado diff y fuerza re-fetch al próximo click
5. La tabla muestra: `employee_id`, nombre completo, estado
6. Sin N+1: exactamente 2 queries para obtener el diff (1 local DB + 1 ERP API)

## Archivo de salida

Al terminar todo el desarrollo, el agente debe crear:

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_007_nomina-diff-empleados-faltantes.md
```

Contenido mínimo del reporte:

```markdown
# Reporte de Ejecución: Nómina Diff — Empleados sin Nómina Generada

**Fecha:** YYYY-MM-DD
**Agente:** [nombre]
**Proyecto:** Agente Tareo RRHH

## Progreso de Tareas

### Backend
- [ ] Método `getSalarySlipEmployees()` añadido a `ERPNextService`
- [ ] Endpoint `GET /api/nomina/diff` registrado en `routes/web.php`

### Frontend
- [ ] Badge "Faltan X nóminas" convertido en botón clickeable
- [ ] Función `fetchDiff` implementada con cache local
- [ ] Tabla expandible de empleados faltantes
- [ ] Reset de estado diff al refrescar stats

## Resultado de Pruebas
[Describir resultado al probar con diferencia > 0 y diferencia = 0]

## Observaciones
[Cualquier decisión técnica tomada durante la implementación]

---
**Estado Final: [COMPLETADO / PARCIAL / BLOQUEADO]**
```
