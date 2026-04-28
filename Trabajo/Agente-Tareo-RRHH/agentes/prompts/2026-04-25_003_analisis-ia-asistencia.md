---
fecha: 2026-04-25
agente_id: "003"
descripcion: "analisis-ia-asistencia-openrouter-free"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\🏢 Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-25_003_analisis-ia-asistencia.md"
---

# Fase 3: Integración del Motor de IA vía OpenRouter (Modelos Gratuitos)

## Contexto
Integraremos el análisis de asistencia usando modelos gratuitos a través de OpenRouter para mantener el costo en cero durante el desarrollo.

## Configuración de OpenRouter (Añadir al .env)
```env
OPENROUTER_API_KEY=sk-S1BMnJyfM3Ea2HoKHPUskdPRWePMpitIzZz5LNt6qyuGOPY6vRwvsacsOTuFFMDv
OPENROUTER_MODEL=google/gemini-flash-1.5-free
```

## Tareas

### 1. Configuración del Cliente de IA
- Crea un Service Class `App\Services\AIAnalyzerService`.
- Implementa conexión HTTP a `https://openrouter.ai/api/v1/chat/completions`.
- Asegúrate de enviar la cabecera `X-Title: Agente Tareo RRHH` para identificar la aplicación.

### 2. Diseño del System Prompt (Optimizado para modelos Flash)
Diseña un prompt conciso para análisis cronológico:
- "Analiza estas marcaciones de Shalom. Detecta: Faltas de entrada/salida, duplicados y ausencias."
- "Formato de respuesta: Únicamente un JSON puro sin explicaciones extra."
- Campos JSON: `tipo`, `fecha`, `mensaje`, `accion`.

### 3. Modelo y Tabla de Alertas
- Crea migración y modelo `AlertaTareo`: `colaborador_id`, `fecha_inicio`, `fecha_fin`, `data_ia` (JSON), `estado` (pendiente/corregido).

### 4. Comando de Análisis
- Crea `php artisan analyze:tareo {colaborador_id} {--days=15}`.
- El comando debe recolectar la data local, enviarla al modelo gratuito de OpenRouter y guardar los resultados.

### 5. Verificación
- Prueba con el modelo gratuito y verifica que la estructura JSON sea procesada correctamente por Laravel.

---

## 📲 Notificaciones Telegram — obligatorio después de cada hito

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

## Archivo de salida
`c:\jarcrow\🏢 Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-25_003_analisis-ia-asistencia.md`
