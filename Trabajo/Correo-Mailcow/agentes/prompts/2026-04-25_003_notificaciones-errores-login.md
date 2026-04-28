---
fecha: 2026-04-25
agente_id: "003"
descripcion: "mensajes-error-login"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\🏢 Trabajo\\Correo-Mailcow\\agentes\\respuestas\\2026-04-25_003_mensajes-error-login.md"
---

# Implementación de Mensajes de Error en Login

## Contexto
El login visualmente ya es correcto, pero no muestra feedback cuando los datos son incorrectos. Necesitamos reintegrar la lógica de alertas de Mailcow en el nuevo diseño "Serenity".

## Tareas

### 1. Identificar Variable de Alertas
- Revisa el backup original `/root/mailcow-dockerized/data/web/templates/user_index.twig.bak` para ver cómo Mailcow maneja las alertas.
- Normalmente usa un bucle sobre la variable `alerts` o similar:
  `{% for alert in alerts %}` ... `{% endfor %}`.

### 2. Integrar Alertas en el Diseño
- Inserta el bloque de alertas dentro de la tarjeta "Serenity", justo **arriba del formulario** de login.
- **Estilo Tailwind:** No uses las clases de Bootstrap. Crea un diseño que combine con "Serenity".
  - Usa un contenedor con fondo rojo suave (`bg-red-50`), borde rojo (`border border-red-200`) y texto rojo oscuro (`text-red-700`).
  - Añade un icono de advertencia (puedes usar Lucide que ya está cargado).

### 3. Ejemplo de estructura esperada (Twig + Tailwind):
```twig
{% if alerts %}
    <div class="mb-6 space-y-2">
        {% for alert in alerts %}
            <div class="flex items-center p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm">
                <i data-lucide="alert-circle" class="w-4 h-4 mr-2"></i>
                {{ alert.msg|raw }}
            </div>
        {% endfor %}
    </div>
{% endif %}
```

### 4. Verificación
- Intenta loguearte con un usuario inexistente o contraseña falsa.
- Verifica que el mensaje de error aparezca de forma elegante sobre los campos de texto.
- Asegúrate de ejecutar `lucide.createIcons();` después de que Twig renderice las alertas si usas iconos dinámicos.

---

## Archivo de salida
`c:\jarcrow\🏢 Trabajo\Correo-Mailcow\agentes\respuestas\2026-04-25_003_mensajes-error-login.md`
