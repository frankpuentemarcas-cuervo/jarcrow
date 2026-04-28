# Fix AuthenticationError Generar TXT

## T1: Config Laravel
- **Credenciales en:** `.env`
- **Variables:** `TOKEN_KEY_CDTALLERES`, `TOKEN_SECRET_CDTALLERES`

## T2: api_key actual usada
- **api_key:** `42571ea328dcc8a`
- **api_secret (en Laravel):** `eb15c1852486fd8`
- **Storage:** Archivo `.env` en `P-SERVICE`

## T3: Estado users Frappe
- **User identificado:** `sistema-solicitud-pagos@shalom.com.pe`
- **Estado inicial __Auth:** `❌ MISSING` (Registro de `api_secret` no existía para este usuario).

## T4: Decrypt test
- **encryption_key:** `xeU0Uo94BA80UNHGEEflotvXsc1DjA73fvOyQ_a95Us=`
- **Estado:** Consistente. Otros secrets se decifran correctamente (verificado vía bench execute).

## T5: Tabla __Auth
- Antes del fix: Sin registro para el usuario API.
- Después del fix: Registro presente y verificado.

## T6: Usuario Laravel
- **User identificado:** `sistema-solicitud-pagos@shalom.com.pe`
- **Línea código:** `NominaSalarialController.php` usa las variables del `.env`.

## T7: Regeneración secret
- **Acción:** Se restauró el `api_secret` en Frappe para que coincida con el valor de Laravel (`eb15c1852486fd8`).
- **verify decrypt:** `OK` (Verificado con script de prueba que decifra el valor y lo compara).

## T8: Update Laravel
- **Acción:** No fue necesario actualizar Laravel, ya que se sincronizó Frappe con las credenciales existentes en Laravel.

## T9: Test E2E
- **curl response:** `{"message":"sistema-solicitud-pagos@shalom.com.pe"}`
- **Resultado:** Autenticación exitosa desde el servidor Laravel hacia el API de Frappe.

## T10: BD final
- **Todos users OK:** `si` (El usuario API ya tiene su secret correctamente cifrado en `__Auth`).

## CONCLUSIÓN
**Causa raíz:** H1 — El registro de `api_secret` en la tabla `__Auth` para el usuario `sistema-solicitud-pagos@shalom.com.pe` había desaparecido o no fue migrado correctamente, provocando el error `Password not found`.
**Fix aplicado:** Se re-estableció el `api_secret` en Frappe usando el valor que Laravel ya tenía configurado, asegurando que el cifrado en `__Auth` sea válido para la `encryption_key` actual.
**Estado final:** ✅ **RESUELTO**
