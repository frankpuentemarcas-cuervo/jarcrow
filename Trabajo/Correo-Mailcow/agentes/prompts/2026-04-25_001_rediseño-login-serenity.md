---
fecha: 2026-04-25
agente_id: "001"
descripcion: "rediseño-login-serenity"
proyecto: "Correo Mailcow"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\🏢 Trabajo\\Correo-Mailcow\\agentes\\respuestas\\2026-04-25_001_rediseño-login-serenity.md"
---

# Rediseño de Login Mailcow — Serenity Theme

## Contexto para el agente

### Proyecto
- **Nombre**: Correo Mailcow (Shalom)
- **Stack**: Docker, Mailcow, HTML/CSS.
- **Situación actual**: El servidor de correo corporativo tiene un diseño de login personalizado. Se ha diseñado una nueva versión llamada "Serenity" que debe ser aplicada.

### Problema a resolver
Implementar el diseño contenido en `c:\dev\correo-docker\login_preview_serenity.html` en el servidor de producción.

---

## ⚠️ REGLA CRÍTICA — Reporte completo obligatorio

**El archivo de salida se genera y actualiza después de CADA tarea, no solo al final.**

Ante cualquier situación — éxito, error, bloqueo o impedimento:
1. **Genera o actualiza el archivo de salida** con lo ejecutado hasta ese momento.
2. Documenta CADA paso con su resultado (✅/❌), output relevante, y si falló: error EXACTO + alternativas probadas.
3. **Nunca termines sin el archivo de salida.** Aunque sea parcial.

## 📲 Notificaciones Telegram — obligatorio después de CADA tarea

Después de cada tarea, enviar notificación:

```bash
TBOT_TOKEN="8610126794:AAFcmZUxmq9swtkOMH7Ez-vbLFOvTelLFOs"
TBOT_CHAT="1412266627"

tg_notify() {
  curl -s -X POST "https://api.telegram.org/bot${TBOT_TOKEN}/sendMessage" \
    -d chat_id="${TBOT_CHAT}" \
    -d parse_mode="Markdown" \
    -d text="$1" > /dev/null
}
```

---

## Tareas a ejecutar

### 1. Conexión y Exploración
- Conéctate al servidor `167.71.253.104` usando el usuario `root` y la llave SSH `c:\dev\correo-docker\id_rsa_deploy`.
- Ubica la carpeta de instalación de Mailcow (probablemente `/opt/mailcow-dockerized`).
- Identifica dónde se encuentra el archivo de login actual. Revisa `data/web/index.php` o carpetas de templates custom.

### 2. Backup
- Realiza una copia de seguridad del archivo de login actual antes de cualquier modificación.

### 3. Aplicación del nuevo diseño
- Lee el contenido de `c:\dev\correo-docker\login_preview_serenity.html` localmente.
- Sube o aplica este contenido al archivo correspondiente en el servidor. 
- Asegúrate de que las rutas a los recursos (imágenes, logos como `Capa_1.svg`) sean correctas y que el logo esté disponible en el servidor si es necesario.

### 4. Verificación
- Accede a `https://mail.shalom.com.pe` y verifica que el nuevo diseño se visualice correctamente y que el formulario de login siga funcionando (los nombres de los campos `email` y `password` deben coincidir con lo que Mailcow espera).

---

## Archivo de salida

**El agente DEBE crear este archivo al terminar:**
```
c:\jarcrow\🏢 Trabajo\Correo-Mailcow\agentes\respuestas\2026-04-25_001_rediseño-login-serenity.md
```

### Estructura obligatoria
- Estado de ejecución (✅/❌ por tarea).
- Ruta del archivo modificado en el servidor.
- Resumen de cambios realizados.
- Bloqueos y errores encontrados.
