---
fecha: 2026-04-29
agente_id: "009"
descripcion: "salary-slip-pendientes-hoy-badge-tabla-card-amber"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "C:\\jarcrow\\Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-29_009_salary-slip-pendientes-hoy.md"
---

# Fase 9: Salary Slips Pendientes de Actualizar Hoy

## Contexto

La card amber "Salary Slips actualizados hoy" en `/nomina` (`C:\dev\agente-tareo-rrhh`) muestra cuántos slips se modificaron hoy. Esta tarea añade un badge en la parte inferior de esa card con el count de slips del mes **no actualizados hoy**, y una tabla lazy expandible que lista cada slip pendiente.

**Pendiente de actualizar** = Salary Slip con `start_date = mesInicio` cuya fecha de `modified` (en zona horaria `America/Lima`) NO es el día actual.

**Proyecto local:** `C:\dev\agente-tareo-rrhh`
**Stack:** Laravel 11, Vue 3, Tailwind CSS, Pest PHP, ERPNext REST API, Carbon

---

## Instrucciones para el Agente

### 1. Cargar Skill de UI/UX

Antes de modificar cualquier archivo `.vue`:

```
C:\dev\agente-tareo-rrhh\skill\ui-ux-designer\skill.md
```

### 2. Ejecutar el Plan de Implementación

Lee y ejecuta el plan completo paso a paso:

```
C:\jarcrow\docs\superpowers\plans\2026-04-29-salary-slip-pendientes-hoy-plan.md
```

5 tareas con código completo. **No saltear ningún step — incluye TDD y reinicio de Vite al final.**

### 3. Resumen de lo que debes implementar

#### Backend — `app/Services/ERPNextService.php`

**`getSalarySlipsPendientesHoyCount(string $mesInicio): int`**
- `GET /api/resource/Salary%20Slip` con `fields=["name","modified"]` y `filters=[["start_date","=","$mesInicio"]]`
- PHP: filtrar con `Carbon::parse(modified)->setTimezone('America/Lima')->toDateString() !== $hoy`
- Retorna count de pendientes

**`getSalarySlipsPendientesHoy(string $mesInicio): array`**
- Misma call con `fields=["name","employee","employee_name","modified"]`
- Mismo filtro PHP
- Retorna `[{name, employee, employee_name, modified_fecha, modified_hora}]`

#### Backend — `routes/web.php`

**Modificar `/api/nomina/stats`:**
- Añadir `$pendientesCount = $erpService->getSalarySlipsPendientesHoyCount($mesInicio);`
- Añadir al response: `'slips_pendientes_hoy' => $pendientesCount`

**Nuevo `GET /api/nomina/slips-pendientes`** (middleware `auth`):
- Llama `getSalarySlipsPendientesHoy($mesInicio)` y retorna JSON

#### Tests — `tests/Feature/NominaSlipsPendientesTest.php`

5 tests Pest:
- Stats incluye `slips_pendientes_hoy` con valor correcto
- Stats retorna 0 cuando todos actualizados hoy
- Slips-pendientes retorna 302 sin auth
- Slips-pendientes retorna lista con campos correctos
- Slips-pendientes retorna array vacío cuando todos actualizados

#### Frontend — `resources/js/Pages/Nomina.vue`

- Añadir `slips_pendientes_hoy: 0` al objeto `stats` ref
- Añadir refs: `pendientesSlips`, `loadingPendientes`, `showPendientes`
- Función `fetchPendientes()` con caché local (igual patrón que `fetchDiff`)
- Reset en `refreshStats()`: limpiar `pendientesSlips` y `showPendientes`
- Badge amber en card amber (después del sub-texto "Último/Ninguno hoy"), solo cuando `slips_pendientes_hoy > 0`
- Tabla expandible con `<transition name="fade">` después del bloque del diff, con 4 columnas: Slip ID, Employee ID, Nombre, Última modif. (`modified_fecha + modified_hora`)
- Build + reinicio Vite al finalizar

#### Reinicio obligatorio de Vite

```bash
docker exec agente-tareo-rrhh-laravel.test-1 pkill -f vite
docker exec -d agente-tareo-rrhh-laravel.test-1 bash -c "cd /var/www/html && npm run dev > /tmp/vite.log 2>&1"
```

---

## Criterios de Éxito

1. `php artisan test tests/Feature/NominaSlipsPendientesTest.php` → 5 tests PASS
2. `php artisan test` → suite completa sin regresiones
3. `npm run build` → sin errores
4. Vite reiniciado
5. Badge "X pendientes ▼ Ver detalle" visible en card amber cuando > 0
6. Badge no visible cuando = 0
7. Click → tabla amber con 4 columnas
8. Toggle: click cierra, `×` cierra
9. "Actualizar" limpia caché y estado

---

## Archivo de Salida

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_009_salary-slip-pendientes-hoy.md
```

Incluir: checklist `[x]`, output tests, resultado visual, estado final (`COMPLETADO` / `PARCIAL` / `BLOQUEADO`).
