---
titulo: Control Remoto via Telegram
proyecto: CrowBot
estado: configuracion
ultima_actualizacion: 2026-04-25
---

# 🤖 Control Remoto de Antigravity via Telegram

Este flujo permite controlar CrowBot y otros agentes de Antigravity de forma remota utilizando un bot de Telegram.

## 🚀 Capacidades

- **Chat Directo**: Envía mensajes a los agentes desde Telegram.
- **Captura de Pantalla**: Comando `/screenshot` para ver qué está haciendo el agente.
- **Cambio de Modelos**: Comando `/model` para alternar entre Gemini y Claude.
- **Gestión de Workspaces**: Comando `/workspace` para cambiar de proyecto.
- **Auto-Accept**: El bot puede aceptar automáticamente botones de "Run", "Allow", etc.

## 📁 Ubicación del Proyecto

El código se encuentra en: `🤖 CrowBot/antigravity-telegram-suite/`

## ⚙️ Configuración

Para que el bot funcione, se requieren las siguientes variables en el archivo `.env`:

1. **BOT_TOKEN**: El token obtenido de [@BotFather](https://t.me/BotFather).
2. **ALLOWED_CHAT_ID**: Tu ID de chat de Telegram (envía `/start` al bot para obtenerlo).
3. **DEBUGGING_PORT**: Por defecto `9333`.

### Archivo .env actual
Ubicación: `🤖 CrowBot/antigravity-telegram-suite/.env`

## 🛠️ Cómo Iniciar

### 1. Iniciar Antigravity con Debugging Remoto
Para que el bot pueda comunicarse con la IDE, esta debe iniciarse con el puerto de depuración abierto:

```powershell
# En Windows
Antigravity.exe --remote-debugging-port=9333
```

### 2. Iniciar el Bot
Desde la terminal en la carpeta del proyecto:

```powershell
cd "c:\jarcrow\🤖 CrowBot\antigravity-telegram-suite"
npm start
```

Para mantenerlo corriendo 24/7 (usando PM2):
```powershell
pm2 start src/index.js --name antigravity-bot
pm2 save
```

## 📱 Comandos Principales

| Comando | Acción |
|---|---|
| `/status` | Verifica conexión con la IDE |
| `/screenshot` | Recibe una captura de pantalla actual |
| `/model` | Cambia el modelo de la IA |
| `/workspace` | Cambia de proyecto |
| `/autoaccept` | Activa/Desactiva clics automáticos |

---
*Configurado por CrowBot | 2026-04-25*
