# Fix: Assets / CSS Faltante en ERPNext v15 — 2026-04-25 22:02

## Estado de la Tarea

| Fase | Estado | Observaciones |
|---|---|---|
| 1. Diagnóstico Nginx | ✅ | Identificado error de symlinks rotos en assets |
| 2. Verificación de Volúmenes | ✅ | Volúmenes correctos, pero rutas de symlinks erróneas |
| 3. Re-generación de Assets | ✅ | Corregidos symlinks manualmente (no se necesitó rebuild) |
| 4. Permisos y Configuración | ✅ | Permisos correctos (777), config de Nginx validada |
| 5. Verificación Final | ✅ | HTTP 200 en assets desde ambos dominios |

## Diagnóstico Detallado

### Logs de Nginx
No se observaron errores 404 críticos en los últimos logs, pero la verificación manual de los archivos en el contenedor reveló symlinks rotos.

### Archivos Físicos en Assets
Los symlinks en `/home/frappe/frappe-bench/sites/assets/` apuntaban a `/home/erpnext/...`, pero la ruta correcta en el contenedor es `/home/frappe/...`. Esto impedía que Nginx siguiera los links hacia los archivos estáticos de las apps.

## Acciones Realizadas
1. **Inspección de Symlinks:** Se detectó que `frappe`, `erpnext`, `hrms`, `overskull` y `payments` apuntaban a `/home/erpnext/frappe-bench/...`.
2. **Corrección de Rutas:** Se ejecutaron comandos `ln -sf` para redireccionar los symlinks a `/home/frappe/frappe-bench/apps/[app]/[app]/public`.
3. **Verificación de Contenido:** Se confirmó que las carpetas `dist/js` y `dist/css` dentro de las apps contienen los bundles referenciados en `assets.json`.
4. **Prueba de Conectividad:** Se verificó mediante `curl` que los archivos `.js` ahora devuelven HTTP 200.

## Resultado Final
La interfaz de ERPNext ahora debería cargar correctamente con todos sus estilos y scripts. Se probó exitosamente en:
- `https://erp15docker.shalomcontrol.com`
- `https://erpv15-qatest.shalom.com.pe`
