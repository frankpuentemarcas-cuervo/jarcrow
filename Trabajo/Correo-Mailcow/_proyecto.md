---
nombre: Correo Mailcow
cliente: shalom
categoria: trabajo
estado: activo
stack:
  backend: mailcow
  frontend: html/css (login custom)
  database: none
  infra: docker
repo: ""
ruta_local: "c:\\dev\\correo-docker"
servidor: 167.71.253.104
dominio: mail.shalom.com.pe
skills_asignados:
  - ui-ux-designer
  - ui-ux-pro-max
ia_principal: crowbot
fecha_inicio: 2024-01-01
ultima_actividad: 2026-04-24
---

# Correo Mailcow

## Descripción
Servidor de correo empresarial de Shalom basado en Mailcow, desplegado en Docker. Incluye rediseño de la página de login con branding corporativo.

## Arquitectura
- **Runtime**: Docker (Mailcow stack completo)
- **Server**: DigitalOcean VPS (`167.71.253.104`)
- **Dominio**: `mail.shalom.com.pe`
- **Login customizado**: HTML/CSS con logo Shalom (`Capa_1.svg`)
- **Color primario**: `#ee2a2f` (rojo Shalom)

## Skills asignados
| Skill | Uso | IA |
|---|---|---|
| ui-ux-designer | Rediseño de login page | Claude Code |
| ui-ux-pro-max | Paletas de color, tipografía para login | Claude Code |

## Archivos importantes
| Archivo | Descripción |
|---|---|
| `login_preview.html` | Preview del login rediseñado (dark) |
| `login_preview_light.html` | Preview light theme |
| `login_preview_serenity.html` | Preview serenity theme |
| `login_preview_system.html` | Preview system theme |
| `Capa_1.svg` | Logo de Shalom |
| `theme-shalom.md` | Documentación del tema |

## Accesos
- **Servidor**: `167.71.253.104` (root, SSH key: `c:\dev\correo-docker\id_rsa_deploy`)

## Tareas Pendientes
- [ ] Cambiar el login usando el diseño `login_preview_serenity.html`.

