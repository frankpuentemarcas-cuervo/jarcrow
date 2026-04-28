---
fecha: 2026-04-25
agente_id: "002"
descripcion: "correccion-urgente-login-serenity"
ia_destino: claude-code
tipo: debug
estado: pendiente
archivo_salida: "c:\\jarcrow\\🏢 Trabajo\\Correo-Mailcow\\agentes\\respuestas\\2026-04-25_002_correccion-login-serenity.md"
---

# CORRECCIÓN URGENTE: Centrado y Estilos de Login Mailcow

## 🚨 Falla en implementación anterior
El agente anterior (001) falló en la implementación. El resultado actual en `https://mail.shalomcontrol.com` es:
- El formulario está alineado a la izquierda (NO centrado).
- Hay errores de codificación (caracteres `???`).
- Los estilos de Bootstrap de Mailcow están interfiriendo con Tailwind.

## Objetivo
Lograr que el login sea EXACTAMENTE igual al preview `c:\dev\correo-docker\login_preview_serenity.html`, centrado vertical y horizontalmente, sin interferencias del layout base de Mailcow.

---

## Tareas Críticas

### 1. Limpieza de Layout
- Abre `data/web/templates/user_index.twig` en el servidor `167.71.253.104`.
- **IMPORTANTE:** Para que el diseño funcione, NO debes usar la estructura estándar de Mailcow que hereda de `base.twig` si esto limita el contenedor o impone estilos que no se pueden anular fácilmente.
- Debes asegurarte de que el contenedor principal tenga las clases de Tailwind: `min-h-screen flex items-center justify-center p-4`.

### 2. Solución de Centrado
- El problema es que probablemente hay un div padre (de `base.twig`) con clase `container` o `row` que limita el ancho.
- Debes forzar que el contenedor de tu login ocupe el 100% del ancho y alto disponible (`w-full h-full`) y usar Flexbox para centrar la tarjeta "Serenity".
- Si es necesario, anula los estilos de `body` o `html` que Mailcow pone por defecto.

### 3. Codificación UTF-8
- Asegúrate de incluir `<meta charset="UTF-8">` en el bloque de encabezado.
- Verifica que el archivo se guarde con codificación UTF-8 sin BOM.

### 4. Sincronización de Campos y Lógica
- Los nombres de los campos DEBEN ser `login_user` y `pass_user`.
- No olvides incluir el token CSRF de Mailcow: `{{ csrf_token()|raw }}` dentro del formulario.
- Asegúrate de que el logo `Capa_1.svg` se cargue correctamente (verifica la ruta en el servidor).

---

## Verificación Final
- La tarjeta DEBE estar en el centro exacto de la pantalla (vertical y horizontal).
- No debe haber textos con `???`.
- El diseño debe ser responsivo (probar redimensionando la ventana).

---

## Archivo de salida

**El agente DEBE crear este archivo al terminar:**
```
c:\jarcrow\🏢 Trabajo\Correo-Mailcow\agentes\respuestas\2026-04-25_002_correccion-login-serenity.md
```
