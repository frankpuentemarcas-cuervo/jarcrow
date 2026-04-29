# Security Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir configuración insegura de producción en `.env.example` y añadir security headers HTTP a todas las respuestas.

**Architecture:** Dos cambios independientes: (1) actualizar 4 variables en `.env.example` como referencia para futuros deploys; (2) crear middleware `SecurityHeaders` y registrarlo en el stack web global de `bootstrap/app.php`. Los headers se inyectan en cada response sin lógica condicional.

**Tech Stack:** Laravel 11, PHP 8.2, Pest PHP, `Illuminate\Http\Middleware`

---

## File Map

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `.env.example` | Modificar | Valores de producción correctos |
| `app/Http/Middleware/SecurityHeaders.php` | Crear | Inyectar 4 security headers en cada response |
| `bootstrap/app.php` | Modificar | Registrar `SecurityHeaders` en stack web |
| `tests/Feature/SecurityHeadersTest.php` | Crear | Verificar presencia de headers en responses |

---

## Task 1: Actualizar `.env.example` con valores de producción

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Aplicar los 4 cambios en `.env.example`**

Localizar y reemplazar línea por línea:

```env
# CAMBIO 1 — línea 2
APP_ENV=local
# →
APP_ENV=production

# CAMBIO 2 — línea 4
APP_DEBUG=true
# →
APP_DEBUG=false

# CAMBIO 3 — línea 33
SESSION_ENCRYPT=false
# →
SESSION_ENCRYPT=true

# CAMBIO 4 — añadir después de SESSION_DOMAIN=null (línea 35)
SESSION_SECURE_COOKIE=true
```

El archivo resultante en la sección de APP y SESSION debe quedar:

```env
APP_NAME=Laravel
APP_ENV=production
APP_KEY=
APP_DEBUG=false
APP_TIMEZONE=UTC
APP_URL=http://localhost

...

SESSION_DRIVER=redis
SESSION_LIFETIME=120
SESSION_ENCRYPT=true
SESSION_PATH=/
SESSION_DOMAIN=null
SESSION_SECURE_COOKIE=true
```

- [ ] **Step 2: Verificar que `.env` de desarrollo NO fue modificado**

```bash
grep "APP_ENV\|APP_DEBUG\|SESSION_ENCRYPT" C:/dev/agente-tareo-rrhh/.env
```

Expected: los valores de desarrollo siguen igual (no `production`, no `false` para DEBUG). Si `.env` fue modificado accidentalmente, restaurar:
```
APP_ENV=local
APP_DEBUG=true
SESSION_ENCRYPT=false
```

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "security: update .env.example with production-safe defaults"
```

---

## Task 2: Crear middleware `SecurityHeaders`

**Files:**
- Create: `app/Http/Middleware/SecurityHeaders.php`
- Create: `tests/Feature/SecurityHeadersTest.php`

- [ ] **Step 1: Crear test que verifica los 4 headers — debe fallar (TDD rojo)**

```php
<?php
// tests/Feature/SecurityHeadersTest.php

use App\Models\User;

it('adds X-Frame-Options header to responses', function () {
    $response = $this->get('/login');
    $response->assertHeader('X-Frame-Options', 'SAMEORIGIN');
});

it('adds X-Content-Type-Options header to responses', function () {
    $response = $this->get('/login');
    $response->assertHeader('X-Content-Type-Options', 'nosniff');
});

it('adds Referrer-Policy header to responses', function () {
    $response = $this->get('/login');
    $response->assertHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
});

it('adds X-XSS-Protection header to responses', function () {
    $response = $this->get('/login');
    $response->assertHeader('X-XSS-Protection', '1; mode=block');
});

it('adds security headers to authenticated responses too', function () {
    $user = User::factory()->create();
    $response = $this->actingAs($user)->get('/dashboard');
    $response->assertHeader('X-Frame-Options', 'SAMEORIGIN');
    $response->assertHeader('X-Content-Type-Options', 'nosniff');
});
```

- [ ] **Step 2: Ejecutar tests — deben fallar (TDD rojo)**

```bash
cd C:\dev\agente-tareo-rrhh
php artisan test tests/Feature/SecurityHeadersTest.php
```

Expected: FAIL — headers not present in response.

- [ ] **Step 3: Crear el middleware**

```php
<?php
// app/Http/Middleware/SecurityHeaders.php

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

- [ ] **Step 4: Registrar middleware en `bootstrap/app.php`**

Localizar:
```php
    ->withMiddleware(function (Middleware $middleware) {
        $middleware->web(append: [
            \App\Http\Middleware\HandleInertiaRequests::class,
            \Illuminate\Http\Middleware\AddLinkHeadersForPreloadedAssets::class,
        ]);

        //
    })
```

Reemplazar por:
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

- [ ] **Step 5: Ejecutar tests — deben pasar (TDD verde)**

```bash
php artisan test tests/Feature/SecurityHeadersTest.php
```

Expected: 5 tests PASS.

- [ ] **Step 6: Ejecutar suite completa — sin regresiones**

```bash
php artisan test
```

Expected: todos los tests PASS.

- [ ] **Step 7: Verificar headers en browser/curl**

```bash
docker exec agente-tareo-rrhh-laravel.test-1 curl -s -I http://localhost/login | grep -E "X-Frame|X-Content|Referrer|X-XSS"
```

Expected output (en cualquier orden):
```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
X-XSS-Protection: 1; mode=block
```

- [ ] **Step 8: Commit**

```bash
git add app/Http/Middleware/SecurityHeaders.php bootstrap/app.php tests/Feature/SecurityHeadersTest.php
git commit -m "security: add SecurityHeaders middleware with X-Frame-Options, X-Content-Type-Options, Referrer-Policy, X-XSS-Protection"
```

---

## Task 3: Archivo de salida del agente

**Files:**
- Create: `C:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-29_011_security-hardening.md`

- [ ] **Step 1: Crear reporte**

```markdown
# Reporte de Ejecución: Security Hardening

**Fecha:** 2026-04-29
**Agente:** [nombre]
**Proyecto:** Agente Tareo RRHH

## Progreso de Tareas

### C1 — .env.example
- [x] APP_ENV=production
- [x] APP_DEBUG=false
- [x] SESSION_ENCRYPT=true
- [x] SESSION_SECURE_COOKIE=true añadido
- [x] .env de desarrollo NO modificado

### C2 — Security Headers
- [x] `SecurityHeaders` middleware creado
- [x] Registrado en bootstrap/app.php
- [x] 5 tests pasando
- [x] Headers verificados con curl

## Resultado de Pruebas
[Output de `php artisan test tests/Feature/SecurityHeadersTest.php`]
[Output de `php artisan test` — suite completa]
[Output de curl con headers]

## Observaciones
[Decisiones técnicas]

---
**Estado Final: COMPLETADO**
```

- [ ] **Step 2: Commit del reporte**

```bash
git add "C:/jarcrow/Trabajo/Agente-Tareo-RRHH/agentes/respuestas/2026-04-29_011_security-hardening.md"
git commit -m "docs(agente): add execution report for security-hardening"
```

---

## Verificación final

- [ ] `.env.example` tiene `APP_ENV=production`, `APP_DEBUG=false`, `SESSION_ENCRYPT=true`, `SESSION_SECURE_COOKIE=true`
- [ ] `.env` de desarrollo sin cambios
- [ ] `php artisan test` — todos PASS (suite completa)
- [ ] `curl -I http://localhost/login` muestra los 4 headers
