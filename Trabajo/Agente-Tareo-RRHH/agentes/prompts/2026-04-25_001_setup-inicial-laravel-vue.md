---
fecha: 2026-04-25
agente_id: "001"
descripcion: "setup-inicial-laravel-vue"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\🏢 Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-25_001_setup-inicial-laravel-vue.md"
---

# Setup Inicial: Agente Tareo RRHH (Laravel 11 + Vue 3)

## Contexto para el agente
Este es un nuevo proyecto para automatizar el "tareo" (asistencia) de RRHH de la empresa Shalom. El stack elegido es Laravel 11 para el backend y Vue 3 (vía Inertia.js) para el frontend.

## Tareas a ejecutar

### 1. Inicialización del Proyecto
- Crea el directorio del proyecto en: `c:\dev\agente-tareo-rrhh`.
- Instala un nuevo proyecto Laravel 11.
- Instala **Laravel Breeze** con el stack de **Vue + Inertia.js** y **Tailwind CSS**.
- Configura el archivo `.env` inicial (Database name: `tareo_rrhh`).

### 2. Estructura de Base de Datos Inicial
Crea las migraciones necesarias para las siguientes entidades básicas:
- **colaboradores**: id, nombre, apellido, dni, codigo_reloj (ID para vincular con marcaciones), departamento.
- **marcaciones**: id, colaborador_id, fecha_hora, tipo (entrada/salida), dispositivo_id.

### 3. Entorno Docker
- Genera un archivo `docker-compose.yml` básico que incluya:
  - App (PHP 8.3)
  - MariaDB
  - Redis (para futuras colas de procesamiento de IA).

### 4. Verificación
- Asegúrate de que el comando `npm install && npm run build` funcione correctamente.
- Verifica que la aplicación sea accesible localmente.

---

## ⚠️ REGLA CRÍTICA — Reporte completo obligatorio
**El archivo de salida se genera y actualiza después de CADA tarea, no solo al final.**

## 📲 Notificaciones Telegram — obligatorio después de CADA tarea

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
**El agente DEBE crear este archivo al terminar:**
```
c:\jarcrow\🏢 Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-25_001_setup-inicial-laravel-vue.md
```
