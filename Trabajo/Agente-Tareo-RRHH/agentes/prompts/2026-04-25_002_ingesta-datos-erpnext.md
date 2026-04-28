---
fecha: 2026-04-25
agente_id: "002"
descripcion: "ingesta-datos-erpnext"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\🏢 Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-25_002_ingesta-datos-erpnext.md"
---

# Fase 2: Ingesta de Datos desde ERPNext (Shalom)

## Contexto
El sistema ya tiene la estructura base. Ahora debemos conectar con el ERP de Shalom para traer los datos de los colaboradores y sus marcaciones de asistencia.

## Datos de Conexión (Añadir al .env)
```env
APP_TIMEZONE=America/Lima
ERP_URL=https://erp-test.shalom.com.pe
ERP_API_KEY=5867d8ac905cfaa
ERP_API_SECRET=4de033693c40891
```

## Tareas a ejecutar

### 1. Configuración de Cliente API
- Crea un Service Class en Laravel (ej. `App\Services\ERPNextService`) que maneje la autenticación por cabeceras `Authorization: token 5867d8ac905cfaa:4de033693c40891`.
- Implementa métodos para obtener:
  - **Employee**: Traer campos `name` (ID), `employee_name`, `attendance_device_id` (codigo_reloj), `department`.
  - **Attendance**: Traer registros filtrando por fecha.

### 2. Comandos de Sincronización (Artisan)
Crea comandos de Artisan para realizar la ingesta:
- `php artisan sync:colaboradores`: Trae empleados activos del ERP y los guarda en la tabla `colaboradores`.
- `php artisan sync:marcaciones {--days=7}`: Trae asistencias recientes y las inserta en la tabla `marcaciones`, vinculándolas por ID de colaborador.

### 3. Lógica de Mapeo
- Asegúrate de manejar correctamente la zona horaria `America/Lima`.
- Evita duplicados en la tabla `marcaciones` usando el ID único del registro de asistencia del ERP.

### 4. Verificación
- Ejecuta los comandos y verifica que las tablas tengan datos reales.

---

## ⚠️ REGLA CRÍTICA — Reporte completo obligatorio
**El archivo de salida se genera y actualiza después de CADA tarea, no solo al final.**

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
**El agente DEBE crear este archivo al terminar:**
```
c:\jarcrow\🏢 Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-25_002_ingesta-datos-erpnext.md
```
