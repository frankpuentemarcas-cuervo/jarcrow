---
fecha: 2026-04-26
agente_id: "004"
descripcion: "integracion-vertex-ai-enterprise-gemini"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-26_004_integracion-vertex-ai-enterprise.md"
---

# Migración a Gemini Enterprise Agent Platform (Vertex AI)

## Contexto
Migraremos el motor de IA de OpenRouter a la plataforma oficial de Google Cloud para el cliente Shalom, utilizando el token de acceso directo proporcionado.

## Tareas

### 1. Configuración de Credenciales
- Actualiza el `.env` con el token de Vertex AI:
  `VERTEX_AI_TOKEN=REDACTED_VERTEX_AI_TOKEN`
- Agrega en `config/services.php`:
  ```php
  'google' => [
      'project_id' => 'shalom-rrhh', // Ajustar según consola
      'location' => 'us-central1',
      'token' => env('VERTEX_AI_TOKEN'),
  ],
  ```

### 2. Implementación del Servicio
- Crea `App\Services\GeminiEnterpriseService.php`.
- Utiliza el endpoint de Vertex AI: `https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/us-central1/publishers/google/models/gemini-1.5-pro:generateContent`.
- Configura la cabecera `Authorization: Bearer [TOKEN]`.

### 3. Refactorización del Analizador
- Modifica `AIAnalyzerService` para que utilice el nuevo `GeminiEnterpriseService` en lugar de OpenRouter.
- Asegura que el prompt del sistema incluya las reglas de negocio de Shalom:
    - Marcaciones huérfanas.
    - Ausencias no corregidas.
    - Duplicados en < 5 min.

### 4. Verificación
- Ejecuta el comando `php artisan analyze:tareo` y verifica que la respuesta provenga de Vertex AI y se guarde correctamente en la tabla `alerta_tareos`.

---

## Archivo de salida
`c:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-26_004_integracion-vertex-ai-enterprise.md`
