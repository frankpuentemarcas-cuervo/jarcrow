# Spec: Security Hardening

**Fecha:** 2026-04-29
**Proyecto:** Agente Tareo RRHH (`C:\dev\agente-tareo-rrhh`)
**Archivo de plan:** `docs/superpowers/plans/2026-04-29-security-hardening-plan.md`

---

## Contexto

Auditoría de seguridad post-deploy inicial. Rate limiting y CSRF ya están cubiertos por Laravel/Breeze. Los issues pendientes son configuración de producción incorrecta y ausencia de security headers HTTP.

## Issues a Corregir

### C1 — `.env.example` production-ready

El `.env.example` actual tiene valores de desarrollo que, si se copian sin modificar a producción, crean vulnerabilidades:

| Variable | Valor actual | Valor correcto | Riesgo |
|----------|-------------|----------------|--------|
| `APP_ENV` | `local` | `production` | Modo local desactiva optimizaciones y puede activar features de debug |
| `APP_DEBUG` | `true` | `false` | Expone stack traces, variables de entorno y rutas de archivos al usuario |
| `SESSION_ENCRYPT` | `false` | `true` | Datos de sesión en Redis almacenados en texto plano |
| `SESSION_SECURE_COOKIE` | no existe | `true` | Sin esta flag, la cookie de sesión se envía por HTTP permitiendo intercepción |

**Archivo:** `.env.example`

```env
APP_ENV=production
APP_DEBUG=false
SESSION_ENCRYPT=true
SESSION_SECURE_COOKIE=true
```

Nota: `.env` actual de desarrollo NO se modifica — estos cambios son solo en `.env.example` como referencia para deploys futuros.

### C2 — Security Headers HTTP

Actualmente ninguna respuesta incluye headers de seguridad HTTP estándar. Sin ellos:
- `X-Frame-Options` ausente → app embebible en iframes de terceros (clickjacking)
- `X-Content-Type-Options` ausente → browser puede interpretar respuestas con MIME incorrecto
- `Referrer-Policy` ausente → URL completa enviada a terceros en links externos
- `X-XSS-Protection` ausente → sin capa adicional en browsers legacy

**Nuevo middleware:** `App\Http\Middleware\SecurityHeaders`

```php
<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class SecurityHeaders
{
    public function handle(Request $request, Closure $next): Response
    {
        $response = $next($request);

        $response->headers->set('X-Frame-Options', 'SAMEORIGIN');
        $response->headers->set('X-Content-Type-Options', 'nosniff');
        $response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin');
        $response->headers->set('X-XSS-Protection', '1; mode=block');

        return $response;
    }
}
```

**Registro en `bootstrap/app.php`** — añadir al stack web global:

```php
->withMiddleware(function (Middleware $middleware) {
    $middleware->web(append: [
        \App\Http\Middleware\HandleInertiaRequests::class,
        \Illuminate\Http\Middleware\AddLinkHeadersForPreloadedAssets::class,
        \App\Http\Middleware\SecurityHeaders::class,
    ]);
})
```

## Exclusiones Deliberadas

- **CSP (Content-Security-Policy):** Requiere configuración por dominio específica y rompe Vite HMR sin whitelisting explícito. Excluido.
- **HSTS (Strict-Transport-Security):** Debe configurarse en el reverse proxy/nginx, no en la app. Excluido.
- **`.env` de desarrollo:** No se modifica — los cambios son solo en `.env.example`.

## Archivos a Modificar/Crear

| Archivo | Acción | Cambio |
|---------|--------|--------|
| `.env.example` | Modificar | 4 variables de producción |
| `app/Http/Middleware/SecurityHeaders.php` | Crear | Middleware con 4 headers |
| `bootstrap/app.php` | Modificar | Registrar `SecurityHeaders` en stack web |

## Criterios de Aceptación

1. `.env.example` tiene `APP_ENV=production`, `APP_DEBUG=false`, `SESSION_ENCRYPT=true`, `SESSION_SECURE_COOKIE=true`
2. Todas las respuestas HTTP incluyen los 4 security headers
3. `php artisan test` — suite completa sin regresiones
4. Verificación manual: `curl -I http://localhost` muestra los 4 headers en la response

## Archivo de salida del agente

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_011_security-hardening.md
```
