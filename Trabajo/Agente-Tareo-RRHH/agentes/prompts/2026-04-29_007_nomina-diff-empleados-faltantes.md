---
fecha: 2026-04-29
agente_id: "007"
descripcion: "nomina-diff-empleados-sin-nomina-generada"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "C:\\jarcrow\\Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-29_007_nomina-diff-empleados-faltantes.md"
---

# Fase 7: Nómina Diff — Identificar Empleados sin Nómina Generada

## Contexto

La vista `/nomina` en `C:\dev\agente-tareo-rrhh` muestra el total de nóminas que deben generarse vs. las ya generadas en ERPNext. Cuando hay diferencia, el usuario no sabe qué empleados específicos faltan. Esta tarea implementa esa detección.

**Proyecto local:** `C:\dev\agente-tareo-rrhh`
**Stack:** Laravel 11, Vue 3, Tailwind CSS, Pest PHP, ERPNext REST API

---

## Instrucciones para el Agente

### 1. Cargar Skill de UI/UX

Antes de modificar cualquier archivo `.vue`, lee y aplica el skill:

```
C:\dev\agente-tareo-rrhh\skill\ui-ux-designer\skill.md
```

### 2. Ejecutar el Plan de Implementación

Lee y ejecuta el plan completo paso a paso:

```
C:\jarcrow\docs\superpowers\plans\2026-04-29-nomina-diff-empleados-faltantes-plan.md
```

El plan contiene 5 tareas con código completo, comandos exactos y criterios de éxito para cada step. **No saltear ningún step — incluye TDD (escribir test que falla antes de implementar).**

### 3. Resumen de lo que debes implementar

#### Backend

**`app/Services/ERPNextService.php`** — Añadir al final de la clase:
- Método `getSalarySlipEmployees(string $startDate): array`
- Llama a `GET /api/resource/Salary%20Slip` con `fields=["employee"]` y `filters=[["start_date","=","$startDate"]]`
- Retorna array plano de strings: `["EMP-0001", "EMP-0042", ...]`

**`routes/web.php`** — Añadir ruta después de `/api/nomina/stats`:
- `GET /api/nomina/diff` con middleware `['auth', 'verified']`
- Obtiene empleados del grupo `total_deben` desde tabla `colaboradores` local (estado = Activo, No Reportado, o Inactivo con `fecha_de_relevo` en el mes actual)
- Obtiene employee IDs con Salary Slip desde ERPNext via `getSalarySlipEmployees()`
- Retorna JSON con empleados faltantes (`employee_id`, `nombre`, `apellido`, `estado`)
- **Exactamente 2 queries — sin N+1**

#### Tests

**`tests/Feature/NominaDiffTest.php`** — Crear con Pest PHP:
- Test 401 sin auth
- Test retorna vacío cuando todos tienen nómina
- Test retorna faltantes correctos
- Test incluye inactivos del mes actual
- Test excluye inactivos de meses anteriores

#### Frontend

**`resources/js/Pages/Nomina.vue`** — Modificar:
- Badge "Faltan X nóminas" → `<button>` clickeable que dispara `fetchDiff()`
- `fetchDiff()` fetch a `/api/nomina/diff`, caché local (no re-fetcha si ya tiene datos)
- Tabla expandible con `employee_id`, nombre (apellido, nombre), estado coloreado
- Toggle click en badge: abre/cierra tabla
- `refreshStats()` invalida caché del diff
- Transición CSS fade en tabla

---

## Criterios de Éxito

1. `php artisan test tests/Feature/NominaDiffTest.php` → todos PASS
2. `php artisan test` → suite completa sin regresiones
3. `npm run build` → sin errores
4. En `/nomina` con diferencia > 0: badge clickeable despliega tabla con empleados faltantes
5. En `/nomina` con diferencia = 0: badge "✓ Completo" no es clickeable
6. Toggle funciona: click abre, click cierra, botón "×" cierra
7. "Actualizar" limpia la lista y fuerza re-fetch en el próximo click

---

## Archivo de Salida

Al completar **todas** las tareas, crea el reporte en:

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_007_nomina-diff-empleados-faltantes.md
```

Incluir:
- Checklist de tareas completadas (marcadas con `[x]`)
- Output real de `php artisan test tests/Feature/NominaDiffTest.php`
- Descripción del resultado visual al probar con diferencia > 0 y = 0
- Cualquier decisión técnica o ajuste realizado
- Estado final: `COMPLETADO` / `PARCIAL` / `BLOQUEADO`
