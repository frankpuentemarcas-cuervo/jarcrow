---
tipo: credenciales
ultima_actualizacion: 2026-04-25
---

# 🔐 Servidores

> ⚠️ **SENSIBLE**: Este archivo contiene credenciales de acceso a servidores de producción.
> Considerar cifrado con git-crypt o migración a KeePass.

## ERPNext v15 — Producción

| Campo | Valor |
|---|---|
| **IP** | `178.128.181.196` |
| **Usuario** | `root` |
| **Llave SSH** | `c:\dev\erpv15\id_rsa_deploy` |
| **Proveedor** | DigitalOcean |
| **Propósito** | ERPNext v15 producción |

### Conexión rápida
```powershell
ssh -i c:\dev\erpv15\id_rsa_deploy root@178.128.181.196
```

---

## Correo Shalom — Mailcow

| Campo | Valor |
|---|---|
| **IP** | `167.71.253.104` |
| **Usuario** | `root` |
| **Llave SSH** | `c:\dev\correo-docker\id_rsa_deploy` |
| **Proveedor** | DigitalOcean |
| **Propósito** | Mailcow email server |

### Conexión rápida
```powershell
ssh -i c:\dev\correo-docker\id_rsa_deploy root@167.71.253.104
```

---

## CDTalleres — Backend

| Campo | Valor |
|---|---|
| **IP** | `164.92.94.47` |
| **Usuario** | `root` |
| **Password** | `.Overskull2026.m` |
| **Proveedor** | DigitalOcean |
| **Propósito** | ERPNext backend (Gunicorn/Workers) |

```powershell
ssh root@164.92.94.47
```

---

## CDTalleres — Base de datos

| Campo | Valor |
|---|---|
| **IP** | `146.190.42.73` |
| **Usuario** | `root` |
| **Password** | `.Overskull2026.m` |
| **Proveedor** | DigitalOcean |
| **Propósito** | MariaDB database |

```powershell
ssh root@146.190.42.73
```

---

## CDTalleres — Frontend/App

| Campo | Valor |
|---|---|
| **IP** | `209.38.75.235` |
| **Usuario** | `root` |
| **Password** | `.Overskull2026.m` |
| **Proveedor** | DigitalOcean |
| **Propósito** | Nginx + static assets + ERPNext app |

```powershell
ssh root@209.38.75.235
```
