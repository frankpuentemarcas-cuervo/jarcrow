---
fecha: 2026-04-27
agente_id: "006"
descripcion: "conexion-erpnext-conteo-empleados-activos"
proyecto: "Agente Tareo RRHH"
ia_destino: claude-code
tipo: ejecucion
estado: pendiente
archivo_salida: "c:\\jarcrow\\Trabajo\\Agente-Tareo-RRHH\\agentes\\respuestas\\2026-04-27_006_conexion-erp-conteo-empleados.md"
---

# Fase 5: Conexión con ERPNext y Validación de Datos

## Contexto
Debemos validar la comunicación con el ERP de Shalom (ERPNext) y obtener el primer dato operativo: la cantidad total de empleados con estado "Active".

## Tareas

### 1. Verificación de Credenciales ERP
- Asegura que el `.env` contenga las llaves correctas:
  ```env
  ERP_URL=https://erp.shalom.com.pe
  ERP_API_KEY=********
  ERP_API_SECRET=********
  ```

### 2. Implementación de Conteo en ERPNextService
- Utiliza el servicio `App\Services\ERPNextService`.
- Implementa o refina el método `getActiveEmployeesCount()` que realice una petición GET a `/api/resource/Employee` con:
    - Filtro: `[["status", "=", "Active"]]`
    - Parámetro: `limit_page_length=1` (solo necesitamos el conteo inicial o la metadata).
    - Alternativa: Usar el endpoint `/api/method/frappe.client.get_count` para mayor eficiencia.

### 3. Creación de Comando de Sincronización Inicial
- Crea un comando: `php artisan erp:test-connection`.
- El comando debe:
    1. Intentar conectar al ERP.
    2. Recuperar la cantidad de empleados activos.
    3. Imprimir en consola: `[SUCCESS] Conexión establecida. Empleados activos encontrados: {count}`.

### 4. Sincronización Local (Mapeo)
- Asegura que los empleados activos se registren en la tabla local `colaboradores` (evitando duplicados usando el `employee_id` del ERP).

---

## Archivo de salida
`c:\jarcrow\Trabajo\Agente-Tareo-RRHH\agentes\respuestas\2026-04-27_006_conexion-erp-conteo-empleados.md`
