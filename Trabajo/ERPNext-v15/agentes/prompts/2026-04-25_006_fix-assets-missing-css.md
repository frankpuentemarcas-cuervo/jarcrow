---
fecha: 2026-04-25
agente_id: "006"
descripcion: "fix-assets-missing-css"
proyecto: "ERPNext v15"
ia_destino: claude-code
tipo: debug
estado: pendiente
archivo_salida: "c:\\jarcrow\\🏢 Trabajo\\ERPNext-v15\\agentes\\respuestas\\2026-04-25_006_fix-assets-missing-css.md"
---

# Fix: Assets / CSS Faltante en ERPNext v15

## Contexto
El stack de Docker está arriba y la URL `https://erpv15-qatest.shalom.com.pe` carga, pero la interfaz se ve sin estilos (CSS roto). Esto indica que Nginx no puede servir o encontrar los archivos estáticos en `/assets/`.

## Tareas

### 1. Diagnóstico de Nginx
- Conéctate al servidor `178.128.181.196` (root, llave: `c:\dev\erpv15\id_rsa_deploy`).
- Revisa los logs del contenedor Nginx (`docker logs erpnext-nginx-proxy` o similar).
- Busca errores 404 o 403 relacionados con archivos `.css` o `.js` en la ruta `/assets/`.

### 2. Verificación de Volúmenes de Assets
- Verifica dónde está montado el volumen de assets en el `docker-compose.yml`.
- Entra al contenedor de frontend y verifica si los archivos existen físicamente:
  `ls -la /home/frappe/frappe-bench/sites/assets`
- Si la carpeta está vacía, el proceso de construcción de assets falló o la imagen no los incluye.

### 3. Re-generación de Assets (si es necesario)
- Si el contenedor tiene `bench` instalado, intenta ejecutar:
  `docker exec -u frappe erpnext-backend bench build --app frappe,erpnext`
- Verifica si esto genera archivos en la carpeta de assets.

### 4. Permisos y Config de Nginx
- Asegúrate de que el usuario que corre Nginx dentro del contenedor tenga permisos de lectura sobre el volumen compartido de assets.
- Revisa la configuración de Nginx para confirmar que el `location /assets/` tiene el `alias` apuntando a la ruta correcta del volumen.

### 5. Verificación
- Una vez realizados los ajustes, limpia la caché del navegador o usa modo incógnito y verifica que el login de ERPNext se vea con sus estilos originales.

---

## Archivo de salida
`c:\jarcrow\🏢 Trabajo\ERPNext-v15\agentes\respuestas\2026-04-25_006_fix-assets-missing-css.md`
