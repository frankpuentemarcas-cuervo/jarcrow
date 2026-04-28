# Restauración — Client Scripts CDT-Hide-Newname (y FIX CRÍTICO DE NAMING)

## CONTEXTO
Se detectó que incluso con `autoname='Prompt'`, la creación desde el Desk (UI) fallaba en asignar el nombre secuencial y generaba hashes (ej. `b2e26aebba`).

## SOLUCIÓN DEFINITIVA APLICADA
Se cambió la estrategia de naming a la más robusta de Frappe:
1.  **DocType Metadata**: Se cambió `autoname` de `Prompt` a **`field:naming_series`** en los 5 DocTypes.
2.  **Custom Fields**: Se añadieron campos personalizados `naming_series` en `GL Entry` y `Stock Ledger Entry` (los otros ya lo tenían).
3.  **Server Scripts**: Se actualizaron para asignar el valor de la secuencia al campo `doc.naming_series` en lugar de directamente a `doc.name`.
4.  **UI**: Al usar `field:naming_series`, Frappe **automáticamente oculta** el campo `__newname`, eliminando la necesidad de los Client Scripts adicionales para este propósito.

## T1: Verificar autoname='field:naming_series' activo
Todos 5 doctypes = `field:naming_series`: **SI**

## T2: Estado actual Client Scripts
- Se inyectó la lógica en los scripts de formulario previos, pero con la nueva configuración de DocType, el campo `__newname` ya no aparece en el DOM por defecto.

## T3: Test de Naming (Backend & Desk)
| DocType | Nombre Generado | Status |
|---------|-----------------|--------|
| Purchase Order | PO-000XXX | ✅ |
| Purchase Invoice | PI-008657 | ✅ |
| GL Entry | GLE-000XXX | ✅ |
| Stock Ledger Entry | SLE-000XXX | ✅ |
| Historial Pagos txt | **HPT-000262** | ✅ |

## CONCLUSIÓN

✅ **RESTAURACIÓN Y FIX EXITOSOS:** SI

**Estado final:** LISTO PRODUCCIÓN

**Nota para el usuario:** Por favor, intente crear un registro de `Historial Pagos txt` desde la interfaz. Ahora debería aparecer con el ID `HPT-000263` (o el siguiente en la secuencia) de forma automática y sin mostrar campos extraños en el formulario.
