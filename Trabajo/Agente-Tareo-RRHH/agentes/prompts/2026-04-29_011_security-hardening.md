---
fecha: 2026-04-29
agente_id: "011"
descripcion: "security-hardening-env-headers"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "C:\\jarcrow\\Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-29_011_security-hardening.md"
---

# Fase 11: Security Hardening

## Contexto

Proyecto en `C:\dev\agente-tareo-rrhh`. Dos problemas de seguridad a corregir:

1. `.env.example` tiene valores de desarrollo (`APP_DEBUG=true`, `APP_ENV=local`) que si se copian sin modificar a producción exponen stack traces y deshabilitan optimizaciones.
2. Ninguna respuesta HTTP incluye security headers estándar (X-Frame-Options, X-Content-Type-Options, Referrer-Policy, X-XSS-Protection).

**IMPORTANTE:** `.env` de desarrollo NO debe modificarse — los cambios son solo en `.env.example`.

**Stack:** Laravel 11, PHP 8.2, Pest PHP

---

## Instrucciones para el Agente

### Ejecutar el Plan de Implementación

Lee y ejecuta el plan completo paso a paso:

```
C:\jarcrow\docs\superpowers\plans\2026-04-29-security-hardening-plan.md
```

3 tareas, 2 con TDD. No saltear ningún step.

### Resumen de cambios

#### Task 1 — `.env.example`

Aplicar 4 cambios (NO tocar `.env`):
```env
APP_ENV=production       # era local
APP_DEBUG=false          # era true
SESSION_ENCRYPT=true     # era false
SESSION_SECURE_COOKIE=true  # no existía — añadir después de SESSION_DOMAIN=null
```

Verificar que `.env` sigue con `APP_ENV=local` y `APP_DEBUG=true`.

#### Task 2 — Middleware `SecurityHeaders`

**Crear `app/Http/Middleware/SecurityHeaders.php`:**
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

**Modificar `bootstrap/app.php`** — añadir al stack web:
```php
->withMiddleware(function (Middleware $middleware) {
    $middleware->web(append: [
        \App\Http\Middleware\HandleInertiaRequests::class,
        \Illuminate\Http\Middleware\AddLinkHeadersForPreloadedAssets::class,
        \App\Http\Middleware\SecurityHeaders::class,
    ]);
    //
})
```

**Crear `tests/Feature/SecurityHeadersTest.php`** con 5 tests Pest que verifican cada header en `/login` y en ruta autenticada `/dashboard`.

#### Verificación con curl

```bash
docker exec agente-tareo-rrhh-laravel.test-1 curl -s -I http://localhost/login | grep -E "X-Frame|X-Content|Referrer|X-XSS"
```

Expected:
```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
X-XSS-Protection: 1; mode=block
```

---

## Criterios de Éxito

1. `.env.example` tiene los 4 valores de producción
2. `.env` de desarrollo sin cambios
3. `php artisan test tests/Feature/SecurityHeadersTest.php` → 5 tests PASS
4. `php artisan test` → suite completa sin regresiones
5. curl muestra los 4 headers en `/login`

---

## Archivo de Salida

```
C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_011_security-hardening.md
```

Incluir: checklist `[x]`, output tests, output curl, estado final.
