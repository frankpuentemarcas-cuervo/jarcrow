---
fecha: 2026-04-29
agente_id: "008"
descripcion: "salary-slip-modificados-hoy-tercera-card-nomina"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "C:\\jarcrow\\Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-29_008_salary-slip-modificados-hoy.md"
---

# Fase 8: Salary Slips Modificados Hoy — 3ra Card en Vista Nómina

## Contexto

La vista `/nomina` en `C:\dev\agente-tareo-rrhh` muestra 2 cards (nóminas que deben generarse y nóminas generadas). Esta tarea añade una 3ra card amber que muestra cuántos Salary Slips en ERPNext tuvieron su campo `modified` actualizado durante el día actual (zona horaria America/Lima).

**Proyecto local:** `C:\dev\agente-tareo-rrhh`
**Stack:** Laravel 11, Vue 3, Tailwind CSS, Pest PHP, ERPNext REST API, Carbon

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
C:\jarcrow\docs\superpowers\plans\2026-04-29-salary-slip-modificados-hoy-plan.md
```

El plan contiene 5 tareas con código completo, comandos exactos y criterios de éxito. **No saltear ningún step — incluye TDD.**

### 3. Resumen de lo que debes implementar

#### Backend

**`app/Services/ERPNextService.php`** — Añadir método al final de la clase:
- `getSalarySlipsModifiedToday(): array`
- `GET /api/resource/Salary%20Slip` con `fields=["name","employee","modified"]`
- `filters=[["modified",">=","$hoy 00:00:00"],["modified","<=","$hoy 23:59:59"]]`
- `$hoy = Carbon::now('America/Lima')->toDateString()`
- Retorna `['count' => int, 'ultima_modificacion' => 'H:i:s'|null]`
- `ultima_modificacion`: hora Lima del `modified` más reciente del grupo. `null` si count=0.

**`routes/web.php`** — Modificar `/api/nomina/stats`:
- Llamar `$erpService->getSalarySlipsModifiedToday()` después de `getSalarySlipsCount()`
- Añadir al response: `slips_modificados_hoy` (int) y `ultima_modificacion_hoy` (string|null)

#### Tests

**`tests/Feature/NominaStatsModifiedTodayTest.php`** — Crear con Pest PHP:
- Test que stats incluye `slips_modificados_hoy` y `ultima_modificacion_hoy` cuando hay slips
- Test que `ultima_modificacion_hoy` es null cuando count=0
- Test que los campos existentes siguen presentes junto a los nuevos

#### Frontend

**`resources/js/Pages/Nomina.vue`** — Modificar:
- Añadir `slips_modificados_hoy: 0` y `ultima_modificacion_hoy: null` al objeto `stats` ref
- Grid: `md:grid-cols-2` → `md:grid-cols-3`
- Nueva card amber (3ra posición) con:
  - Título: "Salary Slips actualizados hoy"
  - Número grande: amber cuando > 0, gris cuando = 0
  - Sub-texto cuando > 0: `Último: {ultima_modificacion_hoy}`
  - Sub-texto cuando = 0: "Ninguno hoy"

#### Build

Después de modificar `Nomina.vue`, compilar el frontend:
```bash
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
```
Si falla por permisos en `public/build`:
```bash
docker exec -u root agente-tareo-rrhh-laravel.test-1 chown -R sail:sail /var/www/html/public/build
docker exec agente-tareo-rrhh-laravel.test-1 npm run build
```

---

## Criterios de Éxito

1. `php artisan test tests/Feature/NominaStatsModifiedTodayTest.php` → 3 tests PASS
2. `php artisan test` → suite completa sin regresiones
3. `npm run build` → sin errores, nuevo hash de `Nomina-XXXXXXXX.js`
4. En `/nomina`: 3 cards visibles en fila (pantalla mediana/grande)
5. Card amber muestra número en amber + hora cuando hay slips modificados hoy
6. Card amber muestra número en gris + "Ninguno hoy" cuando count = 0
7. Botón "Actualizar" refresca las 3 cards simultáneamente

---

## Archivo de Salida

Al completar **todas** las tareas, crear el reporte en:

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_008_salary-slip-modificados-hoy.md
```

Incluir:
- Checklist de tareas completadas (marcadas con `[x]`)
- Output real de `php artisan test tests/Feature/NominaStatsModifiedTodayTest.php`
- Output real de `php artisan test` (suite completa)
- Resultado del build
- Decisiones técnicas tomadas
- Estado final: `COMPLETADO` / `PARCIAL` / `BLOQUEADO`
