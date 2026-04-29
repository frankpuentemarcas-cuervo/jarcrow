# Spec: Salary Slips Modificados Hoy — Card en Vista Nómina

**Fecha:** 2026-04-29
**Proyecto:** Agente Tareo RRHH (`C:\dev\agente-tareo-rrhh`)
**Archivo de plan:** `docs/superpowers/plans/2026-04-29-salary-slip-modificados-hoy-plan.md`

---

## Problema

La vista `/nomina` no muestra actividad en tiempo real sobre qué Salary Slips están siendo procesados hoy. El equipo de planillas necesita ver cuántos slips fueron modificados durante el día actual.

## Fuente de datos

| Campo | Valor |
|-------|-------|
| Doctype ERPNext | `Salary Slip` |
| Campo de filtro | `modified` (datetime, Frappe estándar — última modificación del documento) |
| Criterio de fecha | `modified >= hoy 00:00:00` AND `modified <= hoy 23:59:59` |
| Zona horaria | `America/Lima` via `Carbon::now('America/Lima')` |

## Arquitectura

### Backend

**Nuevo método `ERPNextService::getSalarySlipsModifiedToday(): array`**

```php
// GET /api/resource/Salary%20Slip
// fields: ["name", "employee", "modified"]
// filters: [
//   ["modified", ">=", "$hoy 00:00:00"],
//   ["modified", "<=", "$hoy 23:59:59"]
// ]
// limit_page_length: None
```

Retorna:
```php
[
  'count'               => int,   // cantidad de slips modificados hoy
  'ultima_modificacion' => string|null  // hora Lima del modified más reciente, formato "H:i:s". null si count=0
]
```

**Modificación de `/api/nomina/stats`** (en `routes/web.php`)

Añadir al response JSON existente:
```json
{
  "slips_modificados_hoy": 42,
  "ultima_modificacion_hoy": "14:35:22"
}
```

### Frontend (`Nomina.vue`)

**Stats ref** — añadir campos al estado inicial:
```js
const stats = ref({
  total_deben: 0,
  nominas_generadas: 0,
  activos: 0,
  no_reportado: 0,
  inactivos: 0,
  slips_modificados_hoy: 0,
  ultima_modificacion_hoy: null,
})
```

**Layout** — grid cambia de 2 a 3 columnas:
```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
```

**3ra card** — amber/yellow, alineada con el estilo de las otras dos:
```
┌────────────────────────────────────────┐
│  Salary Slips actualizados hoy         │
│                                        │
│              42                        │  ← amber-600, text-6xl font-bold
│                                        │
│  Último: 14:35:22                      │  ← gris pequeño, null → "Ninguno hoy"
└────────────────────────────────────────┘
```

- Gradiente: `from-amber-50 to-yellow-50` (light) / `from-gray-700 to-gray-600` (dark)
- Borde: `border-amber-200` (light) / `border-amber-800` (dark)
- Número: `text-amber-600` cuando count > 0, `text-gray-400` cuando count = 0
- Sub-texto cuando count > 0: `Último: {ultima_modificacion_hoy}`
- Sub-texto cuando count = 0: `Ninguno hoy`

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `app/Services/ERPNextService.php` | Añadir `getSalarySlipsModifiedToday()` |
| `routes/web.php` | Añadir `slips_modificados_hoy` y `ultima_modificacion_hoy` al response de `/api/nomina/stats` |
| `resources/js/Pages/Nomina.vue` | Grid 3 columnas + 3ra card amber |

## Criterios de aceptación

1. `/api/nomina/stats` retorna `slips_modificados_hoy` (int) y `ultima_modificacion_hoy` (string HH:MM:SS o null)
2. La vista muestra 3 cards en fila en pantallas medianas y grandes
3. Con slips modificados hoy > 0: número en amber, sub-texto con hora del último
4. Con slips modificados hoy = 0: número en gris, sub-texto "Ninguno hoy"
5. El botón "Actualizar" refresca las 3 cards simultáneamente
6. Una sola call ERP adicional en el endpoint stats (sin N+1)

## Archivo de salida del agente

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_008_salary-slip-modificados-hoy.md
```

Contenido mínimo:
```markdown
# Reporte de Ejecución: Salary Slips Modificados Hoy

**Fecha:** YYYY-MM-DD
**Agente:** [nombre]
**Proyecto:** Agente Tareo RRHH

## Progreso de Tareas

### Backend
- [ ] Método `getSalarySlipsModifiedToday()` añadido a `ERPNextService`
- [ ] Response de `/api/nomina/stats` incluye `slips_modificados_hoy` y `ultima_modificacion_hoy`

### Frontend
- [ ] Grid cambiado a 3 columnas
- [ ] 3ra card amber implementada con estados count > 0 y count = 0
- [ ] `stats` ref inicializado con nuevos campos

## Resultado de Pruebas
[Output de tests + resultado visual]

## Observaciones
[Decisiones técnicas]

---
**Estado Final: [COMPLETADO / PARCIAL / BLOQUEADO]**
```
