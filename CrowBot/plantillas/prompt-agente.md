---
tipo: plantilla
version: 2.0
---

# 🤖 Template: Prompt de Agente

Copia este template para cada prompt que CrowBot elabore para un agente.

```markdown
---
fecha: YYYY-MM-DD
agente_id: "001"                        # número secuencial del día
descripcion: ""                         # descripción corta kebab-case
proyecto: ""                            # proyecto asociado
ia_destino: antigravity                 # antigravity | claude-code | notebooklm
tipo: investigacion                     # investigacion | ejecucion | debug | deploy | review
estado: pendiente                       # pendiente | en-progreso | completado | fallido
falla: ""                               # descripción si estado=fallido
archivo_salida: "ruta/completa/archivo-respuesta.md"
---

# [Título del prompt]

## Contexto para el agente

[El agente NO tiene contexto previo — incluir TODO lo necesario.]

### Proyecto
- **Nombre**: [nombre]
- **Stack**: [tecnologías relevantes]
- **Situación actual**: [estado del proyecto]

### Problema a resolver
[Descripción clara y específica.]

---

## ⚠️ REGLA CRÍTICA — Reporte completo obligatorio

**El archivo de salida se genera y actualiza después de CADA tarea, no solo al final.**

Ante cualquier situación — éxito, error, bloqueo o impedimento:

1. **Genera o actualiza el archivo de salida** con lo ejecutado hasta ese momento
2. Documenta CADA paso con su resultado (✅/❌), output relevante, y si falló: error EXACTO + alternativas probadas
3. **Nunca termines sin el archivo de salida.** Aunque sea parcial.
4. Si un paso falla y no hay alternativa, documentarlo y **continuar con el siguiente paso** — no detenerse.

## 📲 Notificaciones Telegram — obligatorio después de CADA tarea

Después de cada tarea (éxito o fallo), enviar notificación:

```bash
TBOT_TOKEN="8610126794:AAFcmZUxmq9swtkOMH7Ez-vbLFOvTelLFOs"
TBOT_CHAT="1412266627"

tg_notify() {
  curl -s -X POST "https://api.telegram.org/bot${TBOT_TOKEN}/sendMessage" \
    -d chat_id="${TBOT_CHAT}" \
    -d parse_mode="Markdown" \
    -d text="$1" > /dev/null
}

# Uso después de cada tarea:
# tg_notify "✅ *Tarea 1* — descripción breve\n\`resultado clave\`"
# tg_notify "❌ *Tarea 2* — descripción\nError: \`mensaje exacto\`"
# tg_notify "🏁 *Agente terminó* — [proyecto] prompt [N]\nVer: [archivo_salida]"
```

---

## Tareas a ejecutar

### 1. [Primera tarea]
[Descripción + comandos concretos]

### 2. [Segunda tarea]
[...]

---

## Archivo de salida

**El agente DEBE crear este archivo al terminar (aunque sea con resultados parciales):**
```
[ruta completa del archivo de salida]
```

### Estructura obligatoria

```markdown
# [Título] — YYYY-MM-DD HH:MM

## Estado de ejecución
[tabla o lista con ✅/❌ por tarea ejecutada]

## [Sección de resultados 1]
[contenido]

## [Sección de resultados 2]
[contenido]

## Bloqueos y errores
[OBLIGATORIO — vacío si todo fue bien, detallado si hubo problemas]
> - Herramienta/acceso faltante: [nombre + cómo instalarlo]
> - Error exacto: [copiar mensaje de error]
> - Alternativas intentadas: [qué se probó]
> - Qué se necesita para resolver: [acción requerida]
```
```
