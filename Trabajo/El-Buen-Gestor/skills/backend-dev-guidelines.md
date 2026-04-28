---
name: backend-dev-guidelines
ia_target: claude-code
categoria: backend
riesgo: unknown
origen: community
proyectos_asignados:
  - El-Buen-Gestor
fuente_original: "c:\\dev\\correo-docker\\skill\\backend-dev-guidelines\\skill.md"
---

# 📏 Backend Dev Guidelines

Standards estrictos de desarrollo backend para Node.js + Express + TypeScript (adaptable a otros stacks).

## Cuándo usar
- Implementar rutas, controllers, services, repositories
- Asegurar calidad de código en backend
- Code review y refactoring

## Principios no negociables
1. **Layered Architecture**: Routes → Controllers → Services → Repositories → DB
2. **Routes solo rutean** — zero business logic
3. **Controllers coordinan, Services deciden**
4. **Todos los controllers extienden BaseController**
5. **Todos los errores a Sentry** — no console.log
6. **unifiedConfig** es la única fuente de config
7. **Validar todo con Zod** (o equivalente)

## BFRI Score (Backend Feasibility & Risk Index)
```
BFRI = (Architectural Fit + Testability) − (Complexity + Data Risk + Operational Risk)
Range: -10 → +10
≥6: Safe | 3-5: Add tests | 0-2: Refactor | <0: Redesign
```

## Prompt base
> Ver archivo completo en: `c:\dev\correo-docker\skill\backend-dev-guidelines\skill.md`
