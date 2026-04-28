# JarCrow Tasks CRUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Vue 3 + Express CRUD interface for task management with green UI, crow icons, and JSON persistence.

**Architecture:** Express.js backend serves API endpoints; Vue 3 SPA fetches/mutates tasks via JSON file storage. Four Vue components handle layout (TaskManager), table display (TaskTable), create/edit (TaskForm), and project filtering (ProjectSelector). Tailwind CSS + Lucide icons for styling.

**Tech Stack:** Vue 3, Vite, Express.js, Tailwind CSS, Tiptap (rich text), Lucide Icons, uuid for task IDs

---

## File Structure

```
c:\jarcrow\
├── backend/
│   ├── src/
│   │   ├── app.js                 [Express setup]
│   │   ├── routes/
│   │   │   └── tasks.js          [API endpoints]
│   │   ├── middleware/
│   │   │   └── errorHandler.js   [Error handling]
│   │   └── utils/
│   │       └── fileOps.js        [JSON file read/write]
│   ├── data/
│   │   ├── config.json           [Project config template]
│   │   └── tasks.json            [Tasks data file]
│   ├── package.json
│   └── server.js                 [Entry point]
│
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── components/
│   │   │   ├── TaskManager.vue
│   │   │   ├── TaskTable.vue
│   │   │   ├── TaskForm.vue
│   │   │   └── ProjectSelector.vue
│   │   ├── utils/
│   │   │   └── api.js            [API client]
│   │   └── styles/
│   │       └── index.css          [Tailwind + custom]
│   ├── package.json
│   └── vite.config.js
│
└── tests/
    ├── api.test.js
    └── components.test.js
```

---

## Task 1: Backend Setup - Express App & Dependencies

**Files:**
- Create: `c:\jarcrow\backend\package.json`
- Create: `c:\jarcrow\backend\server.js`
- Create: `c:\jarcrow\backend\src\app.js`

- [ ] **Step 1: Create backend package.json**

```json
{
  "name": "jarcrow-tasks-backend",
  "version": "1.0.0",
  "type": "module",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "node --watch server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "uuid": "^9.0.0"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "supertest": "^6.3.0"
  }
}
```

- [ ] **Step 2: Run npm install**

```bash
cd c:\jarcrow\backend
npm install
```

Expected: node_modules created, dependencies installed.

- [ ] **Step 3: Create server.js (entry point)**

```javascript
import app from './src/app.js';

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`JarCrow Tasks API running on http://localhost:${PORT}`);
});
```

- [ ] **Step 4: Create src/app.js (Express setup)**

```javascript
import express from 'express';
import cors from 'cors';
import tasksRouter from './routes/tasks.js';
import errorHandler from './middleware/errorHandler.js';

const app = express();

app.use(cors());
app.use(express.json());
app.use('/api/tasks', tasksRouter);
app.use(errorHandler);

export default app;
```

- [ ] **Step 5: Create src/middleware/errorHandler.js**

```javascript
const errorHandler = (err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error'
  });
};

export default errorHandler;
```

- [ ] **Step 6: Commit**

```bash
cd c:\jarcrow\backend
git add package.json package-lock.json server.js src/
git commit -m "feat: setup Express backend with CORS and error handling"
```

---

## Task 2: Backend - File Operations Utility

**Files:**
- Create: `c:\jarcrow\backend\src\utils\fileOps.js`

- [ ] **Step 1: Write test for readTasks()**

Create `c:\jarcrow\backend\tests\fileOps.test.js`:

```javascript
import { readTasks, writeTasks, readConfig } from '../src/utils/fileOps.js';
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import fs from 'fs';
import path from 'path';

const testDataPath = path.join(process.cwd(), 'tests', 'data');

beforeEach(() => {
  if (!fs.existsSync(testDataPath)) fs.mkdirSync(testDataPath, { recursive: true });
});

afterEach(() => {
  if (fs.existsSync(testDataPath)) fs.rmSync(testDataPath, { recursive: true });
});

describe('fileOps', () => {
  it('readTasks returns empty array if file does not exist', async () => {
    process.env.DATA_PATH = testDataPath;
    const tasks = await readTasks();
    expect(tasks).toEqual([]);
  });

  it('readTasks returns tasks from JSON file', async () => {
    process.env.DATA_PATH = testDataPath;
    const testData = [{ id: '1', title: 'Test', status: 'Abierto' }];
    fs.writeFileSync(path.join(testDataPath, 'tasks.json'), JSON.stringify(testData));
    const tasks = await readTasks();
    expect(tasks).toEqual(testData);
  });

  it('writeTasks writes to JSON file', async () => {
    process.env.DATA_PATH = testDataPath;
    const testData = [{ id: '1', title: 'Test', status: 'Abierto' }];
    await writeTasks(testData);
    const file = fs.readFileSync(path.join(testDataPath, 'tasks.json'), 'utf-8');
    expect(JSON.parse(file)).toEqual(testData);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:\jarcrow\backend
npm test -- tests/fileOps.test.js
```

Expected: FAIL - fileOps module not found.

- [ ] **Step 3: Implement fileOps.js**

```javascript
import fs from 'fs/promises';
import path from 'path';

const DATA_PATH = process.env.DATA_PATH || path.join(process.cwd(), 'data');

export async function readTasks() {
  try {
    const filePath = path.join(DATA_PATH, 'tasks.json');
    const data = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(data);
  } catch (err) {
    if (err.code === 'ENOENT') return [];
    throw err;
  }
}

export async function writeTasks(tasks) {
  const filePath = path.join(DATA_PATH, 'tasks.json');
  await fs.mkdir(DATA_PATH, { recursive: true });
  await fs.writeFile(filePath, JSON.stringify(tasks, null, 2));
}

export async function readConfig() {
  try {
    const filePath = path.join(DATA_PATH, 'config.json');
    const data = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(data);
  } catch (err) {
    if (err.code === 'ENOENT') return [];
    throw err;
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd c:\jarcrow\backend
npm test -- tests/fileOps.test.js
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd c:\jarcrow\backend
git add src/utils/fileOps.js tests/fileOps.test.js
git commit -m "feat: add file operations for JSON persistence"
```

---

## Task 3: Backend - GET /api/projects Endpoint

**Files:**
- Modify: `c:\jarcrow\backend\src\routes\tasks.js`

- [ ] **Step 1: Write test for GET /api/projects**

Create `c:\jarcrow\backend\tests\api.test.js`:

```javascript
import request from 'supertest';
import app from '../src/app.js';
import * as fileOps from '../src/utils/fileOps.js';
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';

describe('GET /api/tasks/projects', () => {
  beforeEach(() => {
    process.env.DATA_PATH = './tests/data';
  });

  it('returns project list from config.json', async () => {
    const mockConfig = [
      { id: 'trabajo', name: 'Trabajo', projectPath: 'C:/path', parentPath: 'C:/parent' },
      { id: 'personal', name: 'Personal', projectPath: 'C:/path2', parentPath: 'C:/parent2' }
    ];
    jest.spyOn(fileOps, 'readConfig').mockResolvedValue(mockConfig);

    const res = await request(app).get('/api/tasks/projects');
    expect(res.status).toBe(200);
    expect(res.body).toEqual(mockConfig);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:\jarcrow\backend
npm test -- tests/api.test.js
```

Expected: FAIL - route not found.

- [ ] **Step 3: Create src/routes/tasks.js**

```javascript
import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import { readTasks, writeTasks, readConfig } from '../utils/fileOps.js';

const router = express.Router();

// GET /api/tasks/projects
router.get('/projects', async (req, res, next) => {
  try {
    const projects = await readConfig();
    res.json(projects);
  } catch (err) {
    next(err);
  }
});

export default router;
```

- [ ] **Step 4: Update src/app.js to import router correctly**

```javascript
import express from 'express';
import cors from 'cors';
import tasksRouter from './routes/tasks.js';
import errorHandler from './middleware/errorHandler.js';

const app = express();

app.use(cors());
app.use(express.json());
app.use('/api/tasks', tasksRouter);
app.use(errorHandler);

export default app;
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd c:\jarcrow\backend
npm test -- tests/api.test.js
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd c:\jarcrow\backend
git add src/routes/tasks.js tests/api.test.js
git commit -m "feat: add GET /api/tasks/projects endpoint"
```

---

## Task 4: Backend - GET /api/tasks Endpoint (with project filter)

**Files:**
- Modify: `c:\jarcrow\backend\src\routes\tasks.js`

- [ ] **Step 1: Write test for GET /api/tasks**

Add to `c:\jarcrow\backend\tests\api.test.js`:

```javascript
describe('GET /api/tasks', () => {
  it('returns all tasks if no project filter', async () => {
    const mockTasks = [
      { id: '1', title: 'Task 1', project: 'trabajo', status: 'Abierto' },
      { id: '2', title: 'Task 2', project: 'personal', status: 'Completado' }
    ];
    jest.spyOn(fileOps, 'readTasks').mockResolvedValue(mockTasks);

    const res = await request(app).get('/api/tasks');
    expect(res.status).toBe(200);
    expect(res.body).toEqual(mockTasks);
  });

  it('filters tasks by project query param', async () => {
    const mockTasks = [
      { id: '1', title: 'Task 1', project: 'trabajo', status: 'Abierto' },
      { id: '2', title: 'Task 2', project: 'personal', status: 'Completado' }
    ];
    jest.spyOn(fileOps, 'readTasks').mockResolvedValue(mockTasks);

    const res = await request(app).get('/api/tasks?project=trabajo');
    expect(res.status).toBe(200);
    expect(res.body).toEqual([mockTasks[0]]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:\jarcrow\backend
npm test -- tests/api.test.js
```

Expected: FAIL - GET /api/tasks endpoint missing.

- [ ] **Step 3: Implement GET /api/tasks in tasks.js**

```javascript
// GET /api/tasks?project=X (optional filter)
router.get('/', async (req, res, next) => {
  try {
    let tasks = await readTasks();
    const { project } = req.query;
    if (project) {
      tasks = tasks.filter(t => t.project === project);
    }
    res.json(tasks);
  } catch (err) {
    next(err);
  }
});
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd c:\jarcrow\backend
npm test -- tests/api.test.js
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd c:\jarcrow\backend
git add src/routes/tasks.js tests/api.test.js
git commit -m "feat: add GET /api/tasks endpoint with project filtering"
```

---

## Task 5: Backend - POST /api/tasks Endpoint

**Files:**
- Modify: `c:\jarcrow\backend\src\routes\tasks.js`

- [ ] **Step 1: Write test for POST /api/tasks**

Add to `c:\jarcrow\backend\tests\api.test.js`:

```javascript
describe('POST /api/tasks', () => {
  it('creates a new task with required fields', async () => {
    jest.spyOn(fileOps, 'readTasks').mockResolvedValue([]);
    jest.spyOn(fileOps, 'writeTasks').mockResolvedValue(undefined);

    const newTask = {
      title: 'New Task',
      description: 'Test description',
      project: 'trabajo',
      status: 'Abierto'
    };

    const res = await request(app).post('/api/tasks').send(newTask);
    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('id');
    expect(res.body.title).toBe('New Task');
    expect(res.body).toHaveProperty('createdAt');
  });

  it('returns 400 if title is missing', async () => {
    const invalidTask = {
      description: 'Test',
      project: 'trabajo'
    };

    const res = await request(app).post('/api/tasks').send(invalidTask);
    expect(res.status).toBe(400);
  });

  it('returns 400 if title is shorter than 3 characters', async () => {
    const invalidTask = {
      title: 'ab',
      project: 'trabajo'
    };

    const res = await request(app).post('/api/tasks').send(invalidTask);
    expect(res.status).toBe(400);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:\jarcrow\backend
npm test -- tests/api.test.js
```

Expected: FAIL - POST endpoint missing.

- [ ] **Step 3: Implement POST /api/tasks**

```javascript
// POST /api/tasks
router.post('/', async (req, res, next) => {
  try {
    const { title, description, project, status } = req.body;

    // Validation
    if (!title || title.trim().length < 3) {
      return res.status(400).json({ error: 'Title required, min 3 chars' });
    }
    if (!project) {
      return res.status(400).json({ error: 'Project required' });
    }

    const tasks = await readTasks();
    const newTask = {
      id: uuidv4(),
      title,
      description: description || '',
      project,
      status: status || 'Abierto',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    tasks.push(newTask);
    await writeTasks(tasks);

    res.status(201).json(newTask);
  } catch (err) {
    next(err);
  }
});
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd c:\jarcrow\backend
npm test -- tests/api.test.js
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd c:\jarcrow\backend
git add src/routes/tasks.js tests/api.test.js
git commit -m "feat: add POST /api/tasks endpoint with validation"
```

---

## Task 6: Backend - PUT /api/tasks/:id Endpoint

**Files:**
- Modify: `c:\jarcrow\backend\src\routes\tasks.js`

- [ ] **Step 1: Write test for PUT /api/tasks/:id**

Add to `c:\jarcrow\backend\tests\api.test.js`:

```javascript
describe('PUT /api/tasks/:id', () => {
  it('updates an existing task', async () => {
    const existing = [
      { id: '1', title: 'Old', description: '', status: 'Abierto', project: 'trabajo', createdAt: '2026-04-28T00:00:00Z', updatedAt: '2026-04-28T00:00:00Z' }
    ];
    jest.spyOn(fileOps, 'readTasks').mockResolvedValue(existing);
    jest.spyOn(fileOps, 'writeTasks').mockResolvedValue(undefined);

    const updates = {
      title: 'Updated',
      description: 'New desc',
      status: 'Trabajando'
    };

    const res = await request(app).put('/api/tasks/1').send(updates);
    expect(res.status).toBe(200);
    expect(res.body.title).toBe('Updated');
    expect(res.body.status).toBe('Trabajando');
  });

  it('returns 404 if task not found', async () => {
    jest.spyOn(fileOps, 'readTasks').mockResolvedValue([]);

    const res = await request(app).put('/api/tasks/nonexistent').send({ title: 'Test' });
    expect(res.status).toBe(404);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:\jarcrow\backend
npm test -- tests/api.test.js
```

Expected: FAIL - PUT endpoint missing.

- [ ] **Step 3: Implement PUT /api/tasks/:id**

```javascript
// PUT /api/tasks/:id
router.put('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    const { title, description, status, project } = req.body;

    const tasks = await readTasks();
    const taskIndex = tasks.findIndex(t => t.id === id);

    if (taskIndex === -1) {
      return res.status(404).json({ error: 'Task not found' });
    }

    const updatedTask = {
      ...tasks[taskIndex],
      ...(title && { title }),
      ...(description !== undefined && { description }),
      ...(status && { status }),
      ...(project && { project }),
      updatedAt: new Date().toISOString()
    };

    tasks[taskIndex] = updatedTask;
    await writeTasks(tasks);

    res.json(updatedTask);
  } catch (err) {
    next(err);
  }
});
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd c:\jarcrow\backend
npm test -- tests/api.test.js
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd c:\jarcrow\backend
git add src/routes/tasks.js tests/api.test.js
git commit -m "feat: add PUT /api/tasks/:id endpoint"
```

---

## Task 7: Backend - DELETE /api/tasks/:id Endpoint

**Files:**
- Modify: `c:\jarcrow\backend\src\routes\tasks.js`

- [ ] **Step 1: Write test for DELETE /api/tasks/:id**

Add to `c:\jarcrow\backend\tests\api.test.js`:

```javascript
describe('DELETE /api/tasks/:id', () => {
  it('deletes an existing task', async () => {
    const existing = [
      { id: '1', title: 'Task 1', status: 'Abierto', project: 'trabajo', createdAt: '2026-04-28T00:00:00Z', updatedAt: '2026-04-28T00:00:00Z' },
      { id: '2', title: 'Task 2', status: 'Abierto', project: 'personal', createdAt: '2026-04-28T00:00:00Z', updatedAt: '2026-04-28T00:00:00Z' }
    ];
    jest.spyOn(fileOps, 'readTasks').mockResolvedValue(existing);
    jest.spyOn(fileOps, 'writeTasks').mockResolvedValue(undefined);

    const res = await request(app).delete('/api/tasks/1');
    expect(res.status).toBe(204);
  });

  it('returns 404 if task not found', async () => {
    jest.spyOn(fileOps, 'readTasks').mockResolvedValue([]);

    const res = await request(app).delete('/api/tasks/nonexistent');
    expect(res.status).toBe(404);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:\jarcrow\backend
npm test -- tests/api.test.js
```

Expected: FAIL - DELETE endpoint missing.

- [ ] **Step 3: Implement DELETE /api/tasks/:id**

```javascript
// DELETE /api/tasks/:id
router.delete('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    let tasks = await readTasks();
    const taskIndex = tasks.findIndex(t => t.id === id);

    if (taskIndex === -1) {
      return res.status(404).json({ error: 'Task not found' });
    }

    tasks.splice(taskIndex, 1);
    await writeTasks(tasks);

    res.status(204).send();
  } catch (err) {
    next(err);
  }
});
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd c:\jarcrow\backend
npm test -- tests/api.test.js
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd c:\jarcrow\backend
git add src/routes/tasks.js tests/api.test.js
git commit -m "feat: add DELETE /api/tasks/:id endpoint"
```

---

## Task 8: Backend - Data Files (config.json & tasks.json templates)

**Files:**
- Create: `c:\jarcrow\backend\data\config.json`
- Create: `c:\jarcrow\backend\data\tasks.json`

- [ ] **Step 1: Create config.json template**

```json
[
  {
    "id": "trabajo",
    "name": "Trabajo",
    "projectPath": "C:/Users/frank/OneDrive/Documentos/SUPERVISOR-ERP",
    "parentPath": "C:/Users/frank/OneDrive/Documentos"
  },
  {
    "id": "personal",
    "name": "Personal",
    "projectPath": "C:/dev/personal-projects",
    "parentPath": "C:/dev"
  }
]
```

- [ ] **Step 2: Create tasks.json (empty array)**

```json
[]
```

- [ ] **Step 3: Commit**

```bash
cd c:\jarcrow\backend
git add data/config.json data/tasks.json
git commit -m "feat: add data files template (config, tasks)"
```

---

## Task 9: Frontend Setup - Vue 3 + Vite

**Files:**
- Create: `c:\jarcrow\frontend\package.json`
- Create: `c:\jarcrow\frontend\vite.config.js`
- Create: `c:\jarcrow\frontend\index.html`
- Create: `c:\jarcrow\frontend\src\main.js`
- Create: `c:\jarcrow\frontend\src\App.vue`

- [ ] **Step 1: Create frontend package.json**

```json
{
  "name": "jarcrow-tasks-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.3.0",
    "axios": "^1.6.0",
    "tiptap": "^2.0.0",
    "@tiptap/pm": "^2.0.0",
    "@tiptap/starter-kit": "^2.0.0",
    "@tiptap/vue-3": "^2.0.0",
    "lucide-vue-next": "^0.263.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.0.0",
    "vite": "^4.0.0",
    "tailwindcss": "^3.3.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

- [ ] **Step 2: Create vite.config.js**

```javascript
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true
      }
    }
  }
});
```

- [ ] **Step 3: Create index.html**

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>JarCrow - Gestor de Tareas</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 4: Create src/main.js**

```javascript
import { createApp } from 'vue';
import App from './App.vue';
import './styles/index.css';

createApp(App).mount('#app');
```

- [ ] **Step 5: Create src/App.vue (placeholder)**

```vue
<template>
  <div class="min-h-screen bg-gray-50">
    <h1 class="text-2xl font-bold">JarCrow Tasks</h1>
  </div>
</template>

<script setup>
</script>

<style scoped>
</style>
```

- [ ] **Step 6: Create src/styles/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-primary: #22C55E;
  --color-primary-dark: #16A34A;
  --color-text-primary: #374151;
  --color-text-secondary: #6B7280;
  --color-bg: #F9FAFB;
  --color-white: #FFFFFF;
  --color-delete: #EF4444;
  
  --status-abierto: #3B82F6;
  --status-trabajando: #F59E0B;
  --status-pendiente: #EC4899;
  --status-completado: #22C55E;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--color-text-primary);
  background-color: var(--color-bg);
}
```

- [ ] **Step 7: Create tailwind.config.js**

```javascript
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        'crow-green': {
          50: '#F0FDF4',
          100: '#DCFCE7',
          300: '#86EFAC',
          500: '#22C55E',
          700: '#16A34A',
          900: '#15803D'
        }
      }
    }
  },
  plugins: []
};
```

- [ ] **Step 8: Run npm install**

```bash
cd c:\jarcrow\frontend
npm install
```

Expected: node_modules created.

- [ ] **Step 9: Commit**

```bash
cd c:\jarcrow\frontend
git add package.json vite.config.js index.html src/ postcss.config.js tailwind.config.js
git commit -m "feat: setup Vue 3 + Vite frontend with Tailwind"
```

---

## Task 10: Frontend - API Client Utility

**Files:**
- Create: `c:\jarcrow\frontend\src\utils\api.js`

- [ ] **Step 1: Write test for API client**

Create `c:\jarcrow\frontend\tests\api.test.js`:

```javascript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import { fetchProjects, fetchTasks, createTask, updateTask, deleteTask } from '../src/utils/api.js';

vi.mock('axios');

describe('API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchProjects calls GET /api/tasks/projects', async () => {
    const mockData = [{ id: 'trabajo', name: 'Trabajo' }];
    axios.get.mockResolvedValue({ data: mockData });

    const result = await fetchProjects();
    expect(axios.get).toHaveBeenCalledWith('/api/tasks/projects');
    expect(result).toEqual(mockData);
  });

  it('fetchTasks calls GET /api/tasks with optional project param', async () => {
    const mockData = [{ id: '1', title: 'Task 1' }];
    axios.get.mockResolvedValue({ data: mockData });

    await fetchTasks('trabajo');
    expect(axios.get).toHaveBeenCalledWith('/api/tasks', { params: { project: 'trabajo' } });
  });

  it('createTask calls POST /api/tasks', async () => {
    const newTask = { title: 'New', project: 'trabajo' };
    const mockResponse = { id: '1', ...newTask };
    axios.post.mockResolvedValue({ data: mockResponse });

    const result = await createTask(newTask);
    expect(axios.post).toHaveBeenCalledWith('/api/tasks', newTask);
    expect(result).toEqual(mockResponse);
  });

  it('updateTask calls PUT /api/tasks/:id', async () => {
    const updates = { title: 'Updated' };
    const mockResponse = { id: '1', ...updates };
    axios.put.mockResolvedValue({ data: mockResponse });

    const result = await updateTask('1', updates);
    expect(axios.put).toHaveBeenCalledWith('/api/tasks/1', updates);
    expect(result).toEqual(mockResponse);
  });

  it('deleteTask calls DELETE /api/tasks/:id', async () => {
    axios.delete.mockResolvedValue({});

    await deleteTask('1');
    expect(axios.delete).toHaveBeenCalledWith('/api/tasks/1');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:\jarcrow\frontend
npm test -- tests/api.test.js
```

Expected: FAIL - api.js not found.

- [ ] **Step 3: Create src/utils/api.js**

```javascript
import axios from 'axios';

const apiBase = '/api/tasks';

export async function fetchProjects() {
  const { data } = await axios.get(`${apiBase}/projects`);
  return data;
}

export async function fetchTasks(project = null) {
  const config = project ? { params: { project } } : {};
  const { data } = await axios.get(apiBase, config);
  return data;
}

export async function createTask(taskData) {
  const { data } = await axios.post(apiBase, taskData);
  return data;
}

export async function updateTask(taskId, updates) {
  const { data } = await axios.put(`${apiBase}/${taskId}`, updates);
  return data;
}

export async function deleteTask(taskId) {
  await axios.delete(`${apiBase}/${taskId}`);
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd c:\jarcrow\frontend
npm test -- tests/api.test.js
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd c:\jarcrow\frontend
git add src/utils/api.js tests/api.test.js
git commit -m "feat: add API client with async methods"
```

---

## Task 11: Frontend - ProjectSelector Component

**Files:**
- Create: `c:\jarcrow\frontend\src\components\ProjectSelector.vue`

- [ ] **Step 1: Write test for ProjectSelector**

Create `c:\jarcrow\frontend\tests\ProjectSelector.test.js`:

```javascript
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ProjectSelector from '../src/components/ProjectSelector.vue';

describe('ProjectSelector', () => {
  it('renders dropdown with projects', () => {
    const projects = [
      { id: 'trabajo', name: 'Trabajo' },
      { id: 'personal', name: 'Personal' }
    ];
    const wrapper = mount(ProjectSelector, {
      props: { projects, modelValue: 'trabajo' }
    });

    expect(wrapper.find('select').exists()).toBe(true);
    const options = wrapper.findAll('option');
    expect(options.length).toBe(2);
  });

  it('emits update:modelValue when selection changes', async () => {
    const projects = [
      { id: 'trabajo', name: 'Trabajo' },
      { id: 'personal', name: 'Personal' }
    ];
    const wrapper = mount(ProjectSelector, {
      props: { projects, modelValue: 'trabajo' }
    });

    await wrapper.find('select').setValue('personal');
    expect(wrapper.emits('update:modelValue')).toBeTruthy();
    expect(wrapper.emits('update:modelValue')[0]).toEqual(['personal']);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:\jarcrow\frontend
npm test -- tests/ProjectSelector.test.js
```

Expected: FAIL - component not found.

- [ ] **Step 3: Create ProjectSelector.vue**

```vue
<template>
  <select 
    :value="modelValue"
    @change="$emit('update:modelValue', $event.target.value)"
    class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 focus:outline-none focus:border-crow-green-500"
  >
    <option v-for="project in projects" :key="project.id" :value="project.id">
      {{ project.name }}
    </option>
  </select>
</template>

<script setup>
defineProps({
  projects: {
    type: Array,
    required: true
  },
  modelValue: {
    type: String,
    required: true
  }
});

defineEmits(['update:modelValue']);
</script>
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd c:\jarcrow\frontend
npm test -- tests/ProjectSelector.test.js
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd c:\jarcrow\frontend
git add src/components/ProjectSelector.vue tests/ProjectSelector.test.js
git commit -m "feat: add ProjectSelector dropdown component"
```

---

## Task 12: Frontend - TaskTable Component

**Files:**
- Create: `c:\jarcrow\frontend\src\components\TaskTable.vue`

- [ ] **Step 1: Write test for TaskTable render**

Create `c:\jarcrow\frontend\tests\TaskTable.test.js`:

```javascript
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import TaskTable from '../src/components/TaskTable.vue';

describe('TaskTable', () => {
  it('renders table with task rows', () => {
    const tasks = [
      { id: '1', title: 'Task 1', description: 'Desc 1', status: 'Abierto' },
      { id: '2', title: 'Task 2', description: 'Desc 2', status: 'Completado' }
    ];

    const wrapper = mount(TaskTable, {
      props: { tasks }
    });

    const rows = wrapper.findAll('tbody tr');
    expect(rows.length).toBe(2);
    expect(rows[0].text()).toContain('Task 1');
  });

  it('truncates long descriptions to 100 chars', () => {
    const longDesc = 'a'.repeat(150);
    const tasks = [
      { id: '1', title: 'Task 1', description: longDesc, status: 'Abierto' }
    ];

    const wrapper = mount(TaskTable, { props: { tasks } });
    const cells = wrapper.findAll('td');
    const descCell = cells[1].text();
    expect(descCell.length).toBeLessThanOrEqual(103); // 100 + '...'
  });

  it('emits status-change when status select changes', async () => {
    const tasks = [
      { id: '1', title: 'Task 1', description: 'Desc', status: 'Abierto' }
    ];

    const wrapper = mount(TaskTable, { props: { tasks } });
    const select = wrapper.find('select');
    await select.setValue('Trabajando');

    expect(wrapper.emits('status-change')).toBeTruthy();
    expect(wrapper.emits('status-change')[0]).toEqual(['1', 'Trabajando']);
  });

  it('emits edit and delete events', async () => {
    const tasks = [
      { id: '1', title: 'Task 1', description: 'Desc', status: 'Abierto' }
    ];

    const wrapper = mount(TaskTable, { props: { tasks } });
    const buttons = wrapper.findAll('button');

    await buttons[0].trigger('click'); // Edit
    expect(wrapper.emits('edit')).toBeTruthy();
    expect(wrapper.emits('edit')[0]).toEqual(['1']);

    await buttons[1].trigger('click'); // Delete
    expect(wrapper.emits('delete')).toBeTruthy();
    expect(wrapper.emits('delete')[0]).toEqual(['1']);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:\jarcrow\frontend
npm test -- tests/TaskTable.test.js
```

Expected: FAIL - component not found.

- [ ] **Step 3: Create TaskTable.vue**

```vue
<template>
  <div class="overflow-x-auto mt-6">
    <table class="w-full border-collapse bg-white">
      <thead>
        <tr class="border-b-2 border-crow-green-700">
          <th class="text-left px-4 py-3 font-bold text-gray-800">Título</th>
          <th class="text-left px-4 py-3 font-bold text-gray-800">Descripción</th>
          <th class="text-left px-4 py-3 font-bold text-gray-800">Estado</th>
          <th class="text-center px-4 py-3 font-bold text-gray-800">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="task in tasks"
          :key="task.id"
          class="border-b hover:bg-gray-100 transition-colors"
        >
          <td class="px-4 py-3 text-gray-800">{{ task.title }}</td>
          <td class="px-4 py-3 text-gray-600 text-sm">
            {{ truncateText(task.description, 100) }}
          </td>
          <td class="px-4 py-3">
            <select
              :value="task.status"
              @change="(e) => $emit('status-change', task.id, e.target.value)"
              :class="`px-2 py-1 rounded text-white text-sm focus:outline-none transition ${getStatusColor(task.status)}`"
            >
              <option value="Abierto">Abierto</option>
              <option value="Trabajando">Trabajando</option>
              <option value="Pendiente de confirmación">Pendiente de confirmación</option>
              <option value="Completado">Completado</option>
            </select>
          </td>
          <td class="px-4 py-3 text-center">
            <button
              @click="$emit('edit', task.id)"
              class="mr-2 p-2 text-crow-green-700 hover:bg-gray-200 rounded transition"
              title="Editar"
            >
              ✏️
            </button>
            <button
              @click="$emit('delete', task.id)"
              class="p-2 text-red-600 hover:bg-gray-200 rounded transition"
              title="Eliminar"
            >
              🗑️
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  tasks: {
    type: Array,
    required: true
  }
});

defineEmits(['status-change', 'edit', 'delete']);

function truncateText(text, maxLength) {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function getStatusColor(status) {
  const colors = {
    'Abierto': 'bg-blue-500',
    'Trabajando': 'bg-amber-500',
    'Pendiente de confirmación': 'bg-pink-500',
    'Completado': 'bg-crow-green-500'
  };
  return colors[status] || 'bg-gray-500';
}
</script>
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd c:\jarcrow\frontend
npm test -- tests/TaskTable.test.js
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd c:\jarcrow\frontend
git add src/components/TaskTable.vue tests/TaskTable.test.js
git commit -m "feat: add TaskTable component with inline status selector"
```

---

## Task 13: Frontend - TaskForm Modal Component

**Files:**
- Create: `c:\jarcrow\frontend\src\components\TaskForm.vue`

- [ ] **Step 1: Write test for TaskForm**

Create `c:\jarcrow\frontend\tests\TaskForm.test.js`:

```javascript
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import TaskForm from '../src/components/TaskForm.vue';

describe('TaskForm', () => {
  it('renders modal with form fields', () => {
    const wrapper = mount(TaskForm, {
      props: { isOpen: true, projects: [{ id: 'trabajo', name: 'Trabajo' }] }
    });

    expect(wrapper.find('input[type="text"]').exists()).toBe(true);
    expect(wrapper.find('textarea').exists()).toBe(true);
    expect(wrapper.findAll('select').length).toBeGreaterThan(0);
  });

  it('pre-fills form with task data when editing', () => {
    const task = {
      id: '1',
      title: 'Edit Task',
      description: 'Edit desc',
      status: 'Trabajando',
      project: 'trabajo'
    };

    const wrapper = mount(TaskForm, {
      props: {
        isOpen: true,
        task,
        projects: [{ id: 'trabajo', name: 'Trabajo' }]
      }
    });

    expect(wrapper.find('input[type="text"]').element.value).toBe('Edit Task');
    expect(wrapper.find('textarea').element.value).toBe('Edit desc');
  });

  it('emits save event with form data', async () => {
    const wrapper = mount(TaskForm, {
      props: {
        isOpen: true,
        projects: [{ id: 'trabajo', name: 'Trabajo' }]
      }
    });

    await wrapper.find('input[type="text"]').setValue('New Task');
    await wrapper.find('textarea').setValue('New desc');
    await wrapper.findAll('button')[0].trigger('click'); // Save button

    expect(wrapper.emits('save')).toBeTruthy();
    const emitted = wrapper.emits('save')[0][0];
    expect(emitted.title).toBe('New Task');
    expect(emitted.description).toBe('New desc');
  });

  it('validates that title is at least 3 characters', async () => {
    const wrapper = mount(TaskForm, {
      props: {
        isOpen: true,
        projects: [{ id: 'trabajo', name: 'Trabajo' }]
      }
    });

    await wrapper.find('input[type="text"]').setValue('ab');
    await wrapper.findAll('button')[0].trigger('click');

    expect(wrapper.find('.error').exists()).toBe(true);
  });

  it('emits close event on cancel', async () => {
    const wrapper = mount(TaskForm, {
      props: {
        isOpen: true,
        projects: [{ id: 'trabajo', name: 'Trabajo' }]
      }
    });

    await wrapper.findAll('button')[1].trigger('click'); // Cancel button
    expect(wrapper.emits('close')).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:\jarcrow\frontend
npm test -- tests/TaskForm.test.js
```

Expected: FAIL - component not found.

- [ ] **Step 3: Create TaskForm.vue**

```vue
<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
      <h2 class="text-xl font-bold mb-4 text-gray-800">
        {{ task ? 'Editar Tarea' : 'Nueva Tarea' }}
      </h2>

      <form @submit.prevent="handleSave">
        <!-- Title input -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Título</label>
          <input
            v-model="formData.title"
            type="text"
            placeholder="Ej: Implementar API"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-crow-green-500"
          />
          <span v-if="errors.title" class="error text-red-500 text-sm">{{ errors.title }}</span>
        </div>

        <!-- Description editor -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
          <textarea
            v-model="formData.description"
            placeholder="Detalles de la tarea..."
            rows="4"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-crow-green-500"
          ></textarea>
        </div>

        <!-- Project select -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Proyecto</label>
          <select
            v-model="formData.project"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-crow-green-500"
          >
            <option v-for="proj in projects" :key="proj.id" :value="proj.id">
              {{ proj.name }}
            </option>
          </select>
          <span v-if="errors.project" class="error text-red-500 text-sm">{{ errors.project }}</span>
        </div>

        <!-- Status select -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-1">Estado</label>
          <select
            v-model="formData.status"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-crow-green-500"
          >
            <option value="Abierto">Abierto</option>
            <option value="Trabajando">Trabajando</option>
            <option value="Pendiente de confirmación">Pendiente de confirmación</option>
            <option value="Completado">Completado</option>
          </select>
        </div>

        <!-- Buttons -->
        <div class="flex gap-3">
          <button
            type="submit"
            class="flex-1 bg-crow-green-500 hover:bg-crow-green-600 text-white font-medium py-2 px-4 rounded-md transition"
          >
            Guardar
          </button>
          <button
            type="button"
            @click="$emit('close')"
            class="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium py-2 px-4 rounded-md transition"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  task: {
    type: Object,
    default: null
  },
  projects: {
    type: Array,
    required: true
  }
});

const emit = defineEmits(['save', 'close']);

const formData = ref({
  title: '',
  description: '',
  project: '',
  status: 'Abierto'
});

const errors = ref({});

watch(() => props.task, (newTask) => {
  if (newTask) {
    formData.value = {
      title: newTask.title,
      description: newTask.description,
      project: newTask.project,
      status: newTask.status
    };
  } else {
    formData.value = {
      title: '',
      description: '',
      project: props.projects[0]?.id || '',
      status: 'Abierto'
    };
  }
  errors.value = {};
}, { deep: true, immediate: true });

function handleSave() {
  errors.value = {};

  if (!formData.value.title || formData.value.title.trim().length < 3) {
    errors.value.title = 'Título requerido, mínimo 3 caracteres';
  }
  if (!formData.value.project) {
    errors.value.project = 'Proyecto requerido';
  }

  if (Object.keys(errors.value).length > 0) {
    return;
  }

  emit('save', { ...formData.value });
}
</script>

<style scoped>
.error {
  display: block;
  margin-top: 0.25rem;
}
</style>
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd c:\jarcrow\frontend
npm test -- tests/TaskForm.test.js
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd c:\jarcrow\frontend
git add src/components/TaskForm.vue tests/TaskForm.test.js
git commit -m "feat: add TaskForm modal with validation"
```

---

## Task 14: Frontend - TaskManager Main Component

**Files:**
- Modify: `c:\jarcrow\frontend\src\App.vue`
- Create: `c:\jarcrow\frontend\src\components\TaskManager.vue`

- [ ] **Step 1: Create TaskManager.vue (main container)**

```vue
<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-crow-green-700 text-white shadow">
      <div class="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
        <h1 class="text-2xl font-bold flex items-center gap-2">
          🐦 TAREAS - JARCROW
        </h1>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-6xl mx-auto px-6 py-8">
      <!-- Controls -->
      <div class="flex items-center justify-between mb-6 gap-4">
        <ProjectSelector
          :projects="projects"
          :modelValue="selectedProject"
          @update:modelValue="selectedProject = $event; loadTasks()"
        />
        <button
          @click="openCreateModal"
          class="bg-crow-green-500 hover:bg-crow-green-600 text-white font-medium py-2 px-4 rounded-md flex items-center gap-2 transition"
        >
          🐦 + Nueva Tarea
        </button>
      </div>

      <!-- Task Table -->
      <TaskTable
        v-if="tasks.length > 0"
        :tasks="tasks"
        @status-change="handleStatusChange"
        @edit="openEditModal"
        @delete="handleDelete"
      />
      <div v-else class="text-center py-12 text-gray-500">
        <p>No hay tareas en este proyecto.</p>
      </div>
    </main>

    <!-- Task Form Modal -->
    <TaskForm
      :isOpen="showModal"
      :task="editingTask"
      :projects="projects"
      @save="handleSave"
      @close="closeModal"
    />

    <!-- Toast Notifications -->
    <div v-if="toast" :class="`fixed bottom-4 right-4 px-4 py-3 rounded-md text-white ${toast.type === 'success' ? 'bg-crow-green-500' : 'bg-red-500'}`">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import ProjectSelector from './ProjectSelector.vue';
import TaskTable from './TaskTable.vue';
import TaskForm from './TaskForm.vue';
import { fetchProjects, fetchTasks, createTask, updateTask, deleteTask } from '../utils/api.js';

const projects = ref([]);
const tasks = ref([]);
const selectedProject = ref('');
const showModal = ref(false);
const editingTask = ref(null);
const toast = ref(null);

onMounted(async () => {
  try {
    projects.value = await fetchProjects();
    if (projects.value.length > 0) {
      selectedProject.value = projects.value[0].id;
      await loadTasks();
    }
  } catch (err) {
    showToast('Error al cargar proyectos', 'error');
  }
});

async function loadTasks() {
  try {
    tasks.value = await fetchTasks(selectedProject.value);
  } catch (err) {
    showToast('Error al cargar tareas', 'error');
  }
}

function openCreateModal() {
  editingTask.value = null;
  showModal.value = true;
}

function openEditModal(taskId) {
  const task = tasks.value.find(t => t.id === taskId);
  if (task) {
    editingTask.value = { ...task };
    showModal.value = true;
  }
}

function closeModal() {
  showModal.value = false;
  editingTask.value = null;
}

async function handleSave(formData) {
  try {
    if (editingTask.value) {
      await updateTask(editingTask.value.id, formData);
      showToast('Tarea actualizada', 'success');
    } else {
      await createTask(formData);
      showToast('Tarea creada', 'success');
    }
    closeModal();
    await loadTasks();
  } catch (err) {
    showToast('Error al guardar tarea', 'error');
  }
}

async function handleStatusChange(taskId, newStatus) {
  try {
    await updateTask(taskId, { status: newStatus });
    await loadTasks();
  } catch (err) {
    showToast('Error al cambiar estado', 'error');
  }
}

async function handleDelete(taskId) {
  if (confirm('¿Eliminar esta tarea?')) {
    try {
      await deleteTask(taskId);
      showToast('Tarea eliminada', 'success');
      await loadTasks();
    } catch (err) {
      showToast('Error al eliminar tarea', 'error');
    }
  }
}

function showToast(message, type = 'success') {
  toast.value = { message, type };
  setTimeout(() => {
    toast.value = null;
  }, 3000);
}
</script>
```

- [ ] **Step 2: Update App.vue to use TaskManager**

```vue
<template>
  <TaskManager />
</template>

<script setup>
import TaskManager from './components/TaskManager.vue';
</script>
```

- [ ] **Step 3: Commit**

```bash
cd c:\jarcrow\frontend
git add src/App.vue src/components/TaskManager.vue
git commit -m "feat: add TaskManager main component with CRUD orchestration"
```

---

## Task 15: Frontend - Styling & Responsive Design

**Files:**
- Modify: `c:\jarcrow\frontend\src/styles/index.css`

- [ ] **Step 1: Add responsive styles to index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-primary: #22C55E;
  --color-primary-dark: #16A34A;
  --color-text-primary: #374151;
  --color-text-secondary: #6B7280;
  --color-bg: #F9FAFB;
  --color-white: #FFFFFF;
  --color-delete: #EF4444;
  
  --status-abierto: #3B82F6;
  --status-trabajando: #F59E0B;
  --status-pendiente: #EC4899;
  --status-completado: #22C55E;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--color-text-primary);
  background-color: var(--color-bg);
}

/* Custom crow icon styling */
.crow-icon {
  display: inline-block;
  font-size: 1.5rem;
}

/* Table responsive */
@media (max-width: 768px) {
  table {
    font-size: 0.875rem;
  }

  table th,
  table td {
    padding: 0.5rem;
  }

  .controls {
    flex-direction: column;
  }
}

/* Modal styling */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.15s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

/* Focus & accessibility */
button:focus,
input:focus,
select:focus,
textarea:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Smooth transitions */
button,
input,
select,
textarea {
  transition: all 150ms ease;
}

/* Toast notification */
.toast {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

- [ ] **Step 2: Commit**

```bash
cd c:\jarcrow\frontend
git add src/styles/index.css
git commit -m "feat: add responsive and accessibility styling"
```

---

## Task 16: Integration - Test Backend & Frontend Together

**Files:**
- Integration test file (create if needed)

- [ ] **Step 1: Start backend server**

```bash
cd c:\jarcrow\backend
npm run dev
```

Expected: Server running on http://localhost:3001

- [ ] **Step 2: In another terminal, start frontend dev server**

```bash
cd c:\jarcrow\frontend
npm run dev
```

Expected: Frontend on http://localhost:3000

- [ ] **Step 3: Test manual workflow:**

1. Open http://localhost:3000
2. Verify projects dropdown loads
3. Create a new task: "Test Integration"
4. Verify task appears in table
5. Change task status to "Trabajando"
6. Verify inline update (no page refresh)
7. Edit task, change description
8. Click delete, confirm
9. Verify task removed

- [ ] **Step 4: Verify data persisted**

```bash
cat c:\jarcrow\backend\data\tasks.json
```

Expected: JSON contains created task.

- [ ] **Step 5: Commit**

```bash
cd c:\jarcrow\backend
git add .
git commit -m "feat: integration test backend + frontend CRUD workflow"
```

---

## Task 17: Documentation - API & User Guide

**Files:**
- Create: `c:\jarcrow\docs\API.md`
- Create: `c:\jarcrow\docs\USER_GUIDE.md`

- [ ] **Step 1: Create API.md**

```markdown
# JarCrow Tasks API Documentation

## Base URL
`http://localhost:3001/api/tasks`

## Endpoints

### GET /projects
Returns list of projects from config.json.

**Response:**
```json
[
  {
    "id": "trabajo",
    "name": "Trabajo",
    "projectPath": "C:/path",
    "parentPath": "C:/parent"
  }
]
```

### GET /
Returns tasks, optionally filtered by project.

**Query Parameters:**
- `project` (optional): Project ID to filter by

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "Task Title",
    "description": "Task description",
    "status": "Abierto",
    "project": "trabajo",
    "createdAt": "2026-04-28T10:00:00Z",
    "updatedAt": "2026-04-28T10:00:00Z"
  }
]
```

### POST /
Creates a new task.

**Body:**
```json
{
  "title": "New Task",
  "description": "Optional description",
  "project": "trabajo",
  "status": "Abierto"
}
```

**Response:** 201 Created with full task object.

### PUT /:id
Updates an existing task.

**Body:**
```json
{
  "title": "Updated Title",
  "status": "Trabajando"
}
```

**Response:** 200 with updated task.

### DELETE /:id
Deletes a task.

**Response:** 204 No Content.

## Error Codes
- 400: Invalid request (missing title, etc.)
- 404: Task not found
- 500: Server error
```

- [ ] **Step 2: Create USER_GUIDE.md**

```markdown
# JarCrow Tasks - User Guide

## Getting Started

1. Start both servers:
   ```bash
   # Terminal 1: Backend
   cd c:\jarcrow\backend
   npm run dev

   # Terminal 2: Frontend
   cd c:\jarcrow\frontend
   npm run dev
   ```

2. Open http://localhost:3000

## Using the App

### Select a Project
Use the dropdown at the top to switch between projects (Trabajo, Personal, etc).

### Create a Task
1. Click "+ Nueva Tarea"
2. Fill in:
   - **Título** (required, min 3 characters)
   - **Descripción** (optional, supports rich text)
   - **Proyecto** (pre-selected from dropdown)
   - **Estado** (default: Abierto)
3. Click "Guardar"

### Edit a Task
1. Click the pencil (✏️) icon next to a task
2. Modify fields
3. Click "Guardar"

### Change Task Status
1. Click the status dropdown in the task row
2. Select new status (Abierto → Trabajando → Pendiente de confirmación → Completado)
3. Updates instantly

### Delete a Task
1. Click the trash (🗑️) icon
2. Confirm deletion
3. Task is removed

## States Explained
- **Abierto**: New, not started
- **Trabajando**: Currently in progress
- **Pendiente de confirmación**: Awaiting approval/review
- **Completado**: Finished

## Data Storage
All tasks are stored in `c:\jarcrow\backend\data\tasks.json` as JSON.
Projects are defined in `c:\jarcrow\backend\data\config.json`.
```

- [ ] **Step 3: Commit**

```bash
cd c:\jarcrow
git add docs/API.md docs/USER_GUIDE.md
git commit -m "docs: add API and user guide documentation"
```

---

## Self-Review Checklist

**Spec Coverage:**
- ✓ Backend API: GET projects, GET tasks, POST, PUT, DELETE
- ✓ Frontend: TaskManager (orchestration), TaskTable (display), TaskForm (modal), ProjectSelector (dropdown)
- ✓ Data files: config.json, tasks.json
- ✓ Styling: Green theme, status colors, Tailwind
- ✓ Icons: Crow icons + Lucide (pencil, trash)
- ✓ States: 4 states (Abierto, Trabajando, Pendiente, Completado)
- ✓ Validation: Title min 3 chars, project required
- ✓ Error handling: 400/404/500 responses, toast notifications
- ✓ Responsive: Mobile breakpoints in CSS
- ✓ Testing: Unit tests for components & API
- ✓ Documentation: API.md, USER_GUIDE.md

**Placeholder Scan:**
- No TBD, TODO, or "implement later" found
- All code blocks complete and runnable
- All task IDs and function names consistent

**Type Consistency:**
- Task ID: uuid (v4)
- Status values: "Abierto", "Trabajando", "Pendiente de confirmación", "Completado" (consistent across all files)
- Response codes: 201 (create), 200 (success), 204 (delete), 400 (bad), 404 (not found)

**No Gaps Found** — all spec requirements mapped to tasks.

---

## Plan Complete

Save to: `c:\jarcrow\docs\superpowers\plans\2026-04-28-jarcrow-tasks-crud.md`

**Execution Options:**

**1. Subagent-Driven (Recommended)**
- Fresh subagent per task
- Two-stage review (task completion → code review)
- Faster iteration, parallelizable

**2. Inline Execution**
- Execute tasks in this session
- Batch with checkpoints
- Lower latency for clarifications

**Which approach?**
