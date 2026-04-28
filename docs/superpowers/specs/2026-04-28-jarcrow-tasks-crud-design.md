# JarCrow Tasks CRUD - Design Specification

**Date:** 2026-04-28  
**Status:** Approved  
**Component:** Task Management UI  
**Framework:** Vue 3 + Express.js  
**Integration:** Subsystem in jarcrow  

---

## 1. OVERVIEW

Web-based CRUD interface for managing tasks with state transitions. Single-page dashboard with:
- Project selector (dropdown from config)
- Task table with inline state management
- Modal-based create/edit with rich text description editor
- Persistent storage: JSON files in dedicated folder
- Design: Green color scheme with crow iconography

---

## 2. ARCHITECTURE

### Backend (Node.js/Express)

**API Endpoints:**

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/projects` | Read `config.json`, return project list |
| GET | `/api/tasks?project=X` | Read `tasks.json`, filter by project |
| POST | `/api/tasks` | Create new task |
| PUT | `/api/tasks/:id` | Update task (title, description, status, project) |
| DELETE | `/api/tasks/:id` | Delete task |

**Data Files:**

- **`config.json`** (jarcrow root):
  ```json
  [
    {
      "id": "trabajo",
      "name": "Trabajo",
      "projectPath": "C:/path/to/proyecto",
      "parentPath": "C:/path/to/padre"
    },
    {
      "id": "personal",
      "name": "Personal",
      "projectPath": "C:/path/to/personal",
      "parentPath": "C:/path/to/padre"
    }
  ]
  ```

- **`tasks.json`** (jarcrow/data folder):
  ```json
  [
    {
      "id": "uuid",
      "title": "Tarea 1",
      "description": "Descripción con formato",
      "status": "Abierto",
      "project": "trabajo",
      "createdAt": "2026-04-28T10:00:00Z",
      "updatedAt": "2026-04-28T10:00:00Z"
    }
  ]
  ```

### Frontend (Vue 3)

**Component Structure:**
- `TaskManager.vue` - Main container, state management
- `TaskTable.vue` - Table display, inline state selector
- `TaskForm.vue` - Modal for create/edit, rich text editor
- `ProjectSelector.vue` - Dropdown to filter by project

**State Management:** Vue Composition API (ref, computed, provide/inject for modals)

---

## 3. LAYOUT & UI COMPONENTS

### Screen Structure

```
┌─────────────────────────────────────────┐
│  🐦 TAREAS - JARCROW                    │
├─────────────────────────────────────────┤
│  Proyecto: [Dropdown ▼]  [+ Nueva Tarea]│  ← Header
├─────────────────────────────────────────┤
│  Título │ Descripción │ Estado │ Acciones│  ← Table Header
├─────────────────────────────────────────┤
│ Tarea 1 │ Preview...  │[Estado▼]│📝 🗑️ │
│ Tarea 2 │ Preview...  │[Estado▼]│📝 🗑️ │
│ Tarea 3 │ Preview...  │[Estado▼]│📝 🗑️ │
└─────────────────────────────────────────┘
```

### Components

**Header:**
- Logo + "TAREAS" (crow icon SVG)
- Project dropdown (populated from config.json)
- "+ Nueva Tarea" button (green, crow icon)

**Task Table:**
- 4 columns: Título | Descripción Preview (100 chars) | Estado | Acciones
- Row hover: light gray background
- Estado: `<select>` inline (Abierto, Trabajando, Pendiente de confirmación, Completado)
- Acciones: Edit (pencil icon) + Delete (trash icon)

**Modal (TaskForm):**
- Title: "Nueva Tarea" or "Editar Tarea"
- Fields:
  - Título: text input
  - Descripción: rich text editor (Quill.js or Tiptap)
  - Estado: select (default: Abierto for new)
  - Proyecto: dropdown (pre-selected from filter)
- Buttons: Guardar (green), Cancelar

---

## 4. DATA FLOW & STATE TRANSITIONS

### Task States

Valid state sequence:
```
Abierto → Trabajando → Pendiente de confirmación → Completado
```

States can transition in any order (no strict validation).

### Operations

**Create Task:**
1. Click "+ Nueva Tarea" → Modal opens (empty)
2. User fills: title, description, project, status (default: Abierto)
3. Click "Guardar" → POST `/api/tasks` → tasks.json writes → table refreshes

**Edit Task:**
1. Click edit icon (pencil) → Modal opens (prepopulated)
2. User modifies fields
3. Click "Guardar" → PUT `/api/tasks/:id` → tasks.json writes → table refreshes

**Change Status (Inline):**
1. Click state select in row → dropdown opens
2. Select new state → PUT `/api/tasks/:id` (only status field)
3. Table updates immediately, no page refresh

**Delete Task:**
1. Click delete icon (trash) → confirmation dialog
2. Confirm → DELETE `/api/tasks/:id` → tasks.json writes → row removed from table

**Filter by Project:**
1. Change project dropdown → GET `/api/tasks?project=X` → table filters
2. "Nueva Tarea" modal remembers selected project

---

## 5. DESIGN SYSTEM

### Color Palette

| Use | Color | Hex |
|-----|-------|-----|
| Primary (buttons, actions) | Verde | `#22C55E` |
| Header background | Verde oscuro | `#16A34A` |
| Text - Primary | Gris oscuro | `#374151` |
| Text - Secondary | Gris medio | `#6B7280` |
| Background | Gris claro | `#F9FAFB` |
| Modal/Card | Blanco | `#FFFFFF` |
| Delete action | Rojo | `#EF4444` |

### Status Colors (State Badges)

| Status | Color | Hex |
|--------|-------|-----|
| Abierto | Azul | `#3B82F6` |
| Trabajando | Ámbar | `#F59E0B` |
| Pendiente de confirmación | Rosa | `#EC4899` |
| Completado | Verde | `#22C55E` |

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Page title | Inter | 18px | Bold |
| Table header | Inter | 14px | Bold |
| Table rows | Inter | 14px | Regular |
| Modal title | Inter | 16px | Bold |
| Form inputs | Inter | 14px | Regular |

### Spacing & Effects

- Padding table cells: 12px
- Modal margin: 24px
- Button padding: 8px 16px
- Border radius: 4px (inputs, buttons)
- Transitions: 150ms ease (hover, focus)
- Table row hover: background fade to grayish
- Modal: fade-in animation, subtle shadow
- Focus state: green border + outline

### Iconography

**Crow Icons (SVG):**
- Header logo: Crow silhouette + "JARCROW" text
- "+ Nueva Tarea" button: Crow + plus symbol
- Edit action: Pencil icon
- Delete action: Trash icon
- Status mini-icons (optional): Small icon per status in select

**Icon Library:** Lucide Icons (pencil, trash) + Custom SVG for crow

---

## 6. ERROR HANDLING & VALIDATION

**Client-side validation:**
- Title required, min 3 characters
- Description optional
- Project required
- Status required

**Server-side:**
- Validate task ID exists before update/delete
- Validate project ID exists in config.json
- Return 400 for invalid payload, 404 for missing resource
- Log errors to console

**User feedback:**
- Toast notifications (success/error)
- Validation error messages in modal
- Confirmation dialog on delete

---

## 7. ACCESSIBILITY & RESPONSIVE

**Accessibility:**
- Semantic HTML (form, button, select)
- ARIA labels on icon buttons
- Keyboard navigation (Tab, Enter, Escape in modal)
- Focus visible states (green outline)
- Color contrast: 4.5:1 minimum (text on background)

**Responsive:**
- Mobile: Stack layout, dropdown for actions
- Tablet: 2-column layout
- Desktop: Full table view
- Breakpoints: 375px, 768px, 1024px

---

## 8. TESTING SCOPE

**Unit tests:**
- API endpoints (mock fs for JSON read/write)
- State transitions (valid/invalid)
- Component rendering (Vue)

**Integration tests:**
- Create task → verify tasks.json updated
- Edit task → verify file + UI sync
- Delete task → confirm dialog, file update
- Project filter → correct tasks returned

**Manual testing:**
- Rich text editor (formatting preserved in JSON)
- Modal keyboard nav (Escape closes)
- Long descriptions (table preview truncates)
- Edge case: empty project list

---

## 9. TECH STACK SUMMARY

| Layer | Technology |
|-------|------------|
| Frontend | Vue 3, Vite |
| Text Editor | Quill.js or Tiptap |
| Styling | Tailwind CSS |
| Backend | Express.js |
| Database | JSON files (fs module) |
| Icons | Lucide Icons + Custom SVG |
| UI Library | shadcn/vue (optional, buttons/modals) |

---

## 10. DELIVERABLES

1. Backend API endpoints (Express router)
2. Frontend components (Vue 3 SFC)
3. config.json template
4. tasks.json initial structure
5. Styling (Tailwind + custom CSS)
6. API documentation (endpoint specs)
7. User guide (basic CRUD instructions)
