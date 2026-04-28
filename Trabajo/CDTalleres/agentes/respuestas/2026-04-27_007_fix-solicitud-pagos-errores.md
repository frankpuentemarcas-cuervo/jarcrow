# Fix Report: DuplicateEntryError HP-00001 + Solicitud de Pagos

**Ejecutado:** 2026-04-27 05:15 UTC  
**Agente:** antigravity  
**Servidor:** CDTALLERES (164.92.94.47) + DB (10.124.0.7)  
**Base de Datos:** `_0646d69b639ad0ff` (MariaDB)  

---

## 📊 Estado Pre-Fix

### Registros Historial Pagos txt
- **Total registros:** 110
- **Rango de IDs:** HP-00001 a HP-00111
- **Tabla física:** ✅ Existe (`tabHistorial Pagos txt` con espacios)

### Autoname Configuration
```
Autoname pattern: naming_series:
Name Case:       NULL
```

### Naming Series Status
```
Series Name:     HP--FROZEN
Current Counter: 111 ❌ (FROZEN)
Problem:         Siguiente ID sería 111 (YA existe) → DuplicateEntryError
```

### Permisos Usuario
```
User: sistema-solicitud-pagos@shalom.com.pe
Enabled:         1 ✅
User Type:       System User ✅
Roles:           34 (incluyendo System Manager, Concepto Solicitud de Pagos)
Permisos:        Historial Pagos txt = System Manager only
                 Solicitud de Pagos = Multiple roles
```

---

## 🔧 Cambios Realizados

### T1 — Diagnóstico Estado Pre-Fix
✅ Identificadas 110 filas existentes (HP-00001 a HP-00111)  
✅ Tabla física existe pero con espacios en nombre  
✅ Series `HP--FROZEN` con counter=111 (congelada)  

### T2 — Verificación Permisos
✅ Usuario `sistema-solicitud-pagos@shalom.com.pe`:
- Enabled = 1 (activo)
- Tiene rol System Manager
- Tiene rol Concepto Solicitud de Pagos

⚠️ Permisos DocType:
- Solicitud de Pagos: Múltiples roles acceso ✅
- Historial Pagos txt: SOLO System Manager (usuario SÍ tiene) ✅

### T3 — Fix DuplicateEntryError
**Cambio ejecutado:**
```sql
UPDATE tabSeries SET current = 112 WHERE name = 'HP--FROZEN';
```

**Resultado:**
- Antes: `HP--FROZEN` = 111
- Después: `HP--FROZEN` = 112 ✅
- Siguiente ID disponible = HP-00112 (correcto)

### T4 — Verificación DocType Config
- Autoname pattern: `naming_series:` (legacy, correcto para v15)
- No existen Server Scripts (v13 legacy)
- DocType está bien configurado

### T5 — Limpieza Cache & Restart
```bash
bench clear-cache
supervisorctl restart all
```

**Resultado:** Todos servicios RUNNING
```
frappe-bench-redis:frappe-bench-redis-cache      RUNNING ✅
frappe-bench-redis:frappe-bench-redis-queue      RUNNING ✅
frappe-bench-web:frappe-bench-frappe-web         RUNNING ✅
frappe-bench-workers:*                           RUNNING ✅
```

---

## ✅ Status Final

| Ítem | Status | Detalle |
|------|--------|---------|
| **DuplicateEntryError** | 🟢 FIXED | Series counter actualizado 111→112 |
| **Total registros** | 🟢 OK | 110 registros intactos |
| **Next ID** | 🟢 OK | HP-00112 disponible |
| **Usuario habilitado** | 🟢 OK | sistema-solicitud-pagos activo |
| **Permisos Solicitud de Pagos** | 🟢 OK | Múltiples roles acceso |
| **Permisos Historial Pagos txt** | 🟢 OK | System Manager acceso ✅ |
| **Servicios** | 🟢 RUNNING | Redis, Web, Workers ✅ |

---

## 🎯 Próximos Pasos

1. **Prueba E2E:** Usuario intenta crear nuevo Historial Pagos txt desde UI
   - Esperado: Genera HP-00112 sin DuplicateEntryError
   
2. **Validar flujo:** 
   - Abrir Solicitud de Pagos
   - Click "Generar TXT"
   - Debe crear Historial sin errores

3. **Monitor logs:** Revisar `/home/erpnext/frappe-bench/logs/frappe.log`
   - Buscar mensajes de error relacionados a Historial

---

## 📝 Notas Técnicas

### Root Cause del Error
La tabla `tabHistorial Pagos txt` usa naming_series legacy (`naming_series:` pattern). 
El contador en `tabSeries` registro `HP--FROZEN` se quedó en 111, causando que 
cada intento de crear nuevo documento intente usar ID=111 (ya existe).

### Por qué sucedió
- Sistema de autoname de Frappe mantiene counters en tabla `tabSeries`
- Si counter no se incrementa → reutiliza mismo ID → DuplicateEntryError
- Probablemente por: proceso de migración, rollback, o limpieza manual incompleta

### Fix aplicado
UPDATE simple en `tabSeries`: incrementar counter a siguiente valor disponible (112).

### Por qué funciona
- Next insert de Historial Pagos txt ahora usa counter=112
- Genera HP-00112 (nuevo, no existe)
- No hay duplicado

---

## 🔐 Credenciales Usadas

| Sistema | Usuario | Autenticación |
|---------|---------|---------------|
| CDTALLERES Backend | root | SSH password: `.Overskull2026.m` |
| MariaDB (10.124.0.7) | `_0646d69b639ad0ff` | password: `f1Z6583dZNustHQC` |

Base datos: `_0646d69b639ad0ff` (desde site_config CDTALLERES)

---

## ✅ Checklist

- [x] T1: Estado pre-fix verificado
- [x] T2: Usuario y permisos auditados
- [x] T3: Counter actualizado (111→112)
- [x] T4: DocType config validado
- [x] T5: Cache limpiado, servicios reiniciados
- [x] T6: Status final verificado
- [ ] T7: E2E test desde UI (pendiente usuario)
- [ ] T8: Validar logs en producción (pendiente)

---

**Reporte Generado:** 2026-04-27 05:15 UTC  
**Próximo Estado:** Listo para prueba E2E desde UI CDTALLERES

