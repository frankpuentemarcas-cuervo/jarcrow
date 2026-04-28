---
fecha: 2026-04-25
agente_id: "004"
descripcion: "traduccion-y-claridad-errores"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\🏢 Trabajo\\Correo-Mailcow\\agentes\\respuestas\\2026-04-25_004_traduccion-errores-login.md"
---

# Traducción y Refinamiento de Mensajes de Error

## Problema
Los errores actuales aparecen en inglés (ej. "Login error") y son poco descriptivos. El usuario necesita que sean en español y más específicos (ej. "Usuario o contraseña incorrecto").

## Tareas

### 1. Implementar Mapeo de Traducción en Twig
Modifica el bloque de alertas en `data/web/templates/user_index.twig` para interceptar los mensajes de Mailcow y traducirlos manualmente si coinciden con ciertos patrones.

**Lógica sugerida:**
```twig
{% if alerts %}
    <div class="mb-6 space-y-2">
        {% for alert in alerts %}
            {% set original_msg = alert.msg|raw %}
            {% set display_msg = original_msg %}

            {# Mapeo de traducciones manuales #}
            {% if "Login error" in original_msg or "Invalid user or password" in original_msg or "Authentication failed" in original_msg %}
                {% set display_msg = "Usuario o contraseña incorrecto" %}
            {% elseif "CSRF" in original_msg %}
                {% set display_msg = "Sesión expirada, por favor intenta de nuevo" %}
            {% elseif "Empty" in original_msg %}
                {% set display_msg = "Por favor completa todos los campos" %}
            {% endif %}

            <div class="flex items-center p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm">
                <i data-lucide="alert-circle" class="w-4 h-4 mr-2"></i>
                {{ display_msg }}
            </div>
        {% endfor %}
    </div>
{% endif %}
```

### 2. Verificar Mensajes Genéricos
Si Mailcow envía mensajes muy cortos o códigos, asegúrate de que el mapeo sea robusto para capturar el error de "Login error" y transformarlo en la frase solicitada por el usuario: "Usuario o contraseña incorrecto".

### 3. Verificación
- Provoca un error de login y confirma que ahora dice en español: **"Usuario o contraseña incorrecto"**.
- Verifica que el diseño siga siendo centrado y responsivo.

---

## Archivo de salida
`c:\jarcrow\🏢 Trabajo\Correo-Mailcow\agentes\respuestas\2026-04-25_004_traduccion-errores-login.md`
