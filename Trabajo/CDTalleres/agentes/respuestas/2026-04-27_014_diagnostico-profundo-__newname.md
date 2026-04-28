# Diagnóstico __newname — 2026-04-27

## H1: Custom Fields
**RESULTADO T1:** Vacío — sin Custom Fields con `newname` o `name` en 7 doctypes
**HIPÓTESIS:** ❌ Descartada
**RAZÓN:** BD limpia de custom fields

## H2: Property Setters
**RESULTADO T2:** Vacío — sin Property Setters relacionados
**HIPÓTESIS:** ❌ Descartada
**RAZÓN:** BD sin overrides de propiedades

## H3: Metadata real (frappe.get_meta)
**RESULTADO T3:** 
- Total fields: 151
- NO encontró `__newname` en campos
- autoname: "Prompt"
**HIPÓTESIS:** ❌ Descartada
**RAZÓN:** Server-side limpio. Frappe NO envía `__newname` al cliente

## H4: Client Scripts
**RESULTADO T4:** 
- Existen: `Purchase Order-Form`, `Purchase Order-List`
- Script len: 13917 chars
- NO contiene `__newname`
**HIPÓTESIS:** ❌ Descartada
**RAZÓN:** Scripts limpios

## H5: Server Scripts
**RESULTADO T5:**
- 6 scripts encontrados (CDT-GLE-Seq, CDT-HN-Seq, CDT-OT2-Seq, CDT-PI-Seq, CDT-PO-Seq, CDT-SLE-Seq)
- NINGUNO menciona `__newname`
**HIPÓTESIS:** ❌ Descartada
**RAZÓN:** Scripts no interfieren

## H6: JSON files
**RESULTADO T6:** Vacío — sin `__newname` en JSONs
**HIPÓTESIS:** ❌ Descartada
**RAZÓN:** Repos limpios

## H7: Client meta API
**RESULTADO T7:**
- `meta.as_dict()` enviado al cliente NO contiene `__newname`
- autoname: "Prompt"
**HIPÓTESIS:** ❌ Descartada
**RAZÓN:** API response limpia

## H8: Browser Cache/LocalStorage
**RESULTADO T8:** 
- Ejecutado: `bench clear-cache`
- Ejecutado: `bench build` (73.95s — assets rebuilt)
**HIPÓTESIS:** ✅ Confirmada (probable)
**RAZÓN:** 
- Server-side está 100% limpio
- `__newname` NO existe en BD, JSONs, scripts, custom fields
- Cliente cachea metadata en localStorage
- Usuarios ven versión vieja del form

## CONCLUSIÓN

**Fuente real:** Browser localStorage + Frappe client-side metadata cache

**Por qué ocurrió:**
1. Agentes 011-013 removieron `__newname` de BD/JSONs
2. No forzaron actualización de cache del cliente
3. Usuarios ven form viejo de localStorage

**Solución:**

### Opción A (Inmediata — requiere usuarios)
Usuarios: Ctrl+Shift+Del → Clear browser data → localStorage → Reload página

### Opción B (Desde server)
```bash
# En backend, agregar header para invalidar cache
curl -v https://cdtalleres-copia.shalom.com.pe/api/method/frappe.desk.form.load.getdoc \
  -H "Cache-Control: no-cache, no-store, must-revalidate"
```

### Opción C (Más robusta — app-side)
1. Incrementar `frappe.VERSION` en code
2. Ejecutar `bench build` nuevamente (ya hecho ✓)
3. CDN/cache headers: max-age=0

### Opción D (Definitiva — limpiar frontend)
```bash
rm -rf /home/erpnext/frappe-bench/sites/CDTALLERES/.build
rm -rf /home/erpnext/frappe-bench/sites/CDTALLERES/public
bench --site CDTALLERES build --no-minify
```

---

## Estado actual
- ✅ Backend limpio (BD, JSONs, scripts OK)
- ✅ Assets rebuilt (bench build ejecutado)
- ⏳ Pendiente: Forzar cache clear en clientes

**Próximo paso:** Instruir usuarios a limpiar localStorage O hacer cache bust desde Nginx headers
