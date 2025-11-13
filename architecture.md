# Software Maker Agent Platform – Architecture

## 1. Goal & Concept

**Goal:**  
A full-stack, multi-agent **Software Maker** that:

- Takes a **prompt description** of desired software (API, web app, microservice, etc.).
- Plans the project, generates code, wiring, infra, and tests.
- **Runs & debugs** the code automatically.
- Generates **tests**, runs them, and **auto-fixes** regressions.
- Supports **multiple concurrent projects**.
- Can use **OpenAI / Claude / local LLMs (e.g. DeepSeek)** via a unified config.
- Can **combine multiple LLM APIs** in a single build.
- Provides:
  - A **Web console** + progress tracker.
  - A **Web agent** that exercises the GUI for testing.
  - A **Console/CLI agent** to drive tasks from terminal.
- Entire backend stack is **Docker Compose** based (Python preferred).

---

## 2. High-Level Architecture

**Core idea**: Orchestration + agents, using a LangChain-like stack.

```text
+------------------+          +------------------------------+
|  Web Frontend    |  HTTP    |          API Gateway         |
| (React/TS)       +--------->|  (FastAPI, auth, REST, WS)   |
+------------------+          +------------------------------+
            |                              |
            | WebSockets / REST            | Internal RPC / Queue
            v                              v
+------------------+          +------------------------------+
| Progress Tracker |<-------->|     Orchestrator Service     |
| (DB + state)     |   DB     |  (Planner / Project Manager) |
+------------------+          +------------------------------+
                                          |
                                 Schedules jobs / tasks
                                          v
                              +--------------------------+
                              |    Worker / Agent Pool   |
                              | (Celery / RQ workers)    |
                              +-----------+--------------+
                                      /  |                                       /   |                                       v    v    v
                                 Code   Test  Deploy
                                Agent  Agent Agent
                                 |      |      |
                                 v      v      v
                         +------------------------------+
                         |    Project Workspaces        |
                         |   (per-project code dirs)    |
                         +------------------------------+

                            +----------------------+
                            |     Web Agent        |
                            | (Playwright/Selenium)|
                            +----------+-----------+
                                       |
                               Browser automation for
                               GUI testing

+-------------------------+
|   LLM Router Service    |
| (OpenAI/Claude/Local)   |
+-------------------------+
          ^
          |
+-------------------------+
|  Console CLI Agent      |
| (Python or Go / Rust)   |
+-------------------------+
```

**Supporting Services via Docker Compose:**

- `api` – FastAPI backend
- `workers` – Celery / RQ workers running agents
- `web` – React/TypeScript frontend
- `db` – Postgres
- `redis` – task/message broker
- `web-agent` – container for Playwright/Selenium
- `llm-router` – abstraction over OpenAI / Claude / local LLMs (optional separate service or module)
- `file-server` (optional) – for artifact downloads

---

## 3. Main Components

### 3.1 API Gateway (FastAPI)

Responsibilities:

- REST + WebSocket endpoints:
  - Create project from prompt.
  - Add/modify instructions / queue items.
  - Inspect project status and logs.
  - Control builds (pause/resume/restart).
- Authentication (basic API key or JWT).
- Provides streaming logs & status updates to frontend.

### 3.2 Orchestrator Service

Core brain of the system:

- **Project Planner Agent**
  - Breaks main prompt into:
    - features
    - tasks
    - milestones
  - Produces a **project spec**: stack, services, modules, directories, test strategy.
- **Task Scheduler**
  - Maintains per-project DAG:
    - `spec` → `skeleton` → `implementation` → `tests` → `run` → `fix` → `deploy`.
  - Dispatches tasks to specific **agents** via message queue.
- **State Machine**
  - Each project has state: `NEW`, `PLANNING`, `CODING`, `TESTING`, `DEBUGGING`, `READY`, `DEPLOYED`, `FAILED`.
- **Progress Tracker Integration**
  - Writes progress/events to DB.
  - Exposes a unified view to frontend & CLI.

### 3.3 Agent Workers (LangChain Agents)

#### a) Code Generation Agent

- Input: task description, target file(s), coding standards, existing repo state.
- Uses LangChain-style tools:
  - **File system tool**: read/write project files.
  - **Repo context tool**: semantic search over code to stay consistent.
- Generates:
  - Backend code (FastAPI/Django/Node/etc.).
  - Frontend code (React/Vue, etc.) if requested.
  - Infrastructure files (Dockerfiles, docker-compose excerpts, env samples).

#### b) Test Agent

- Generates:
  - Unit tests (e.g. pytest).
  - Integration tests.
  - End-to-end tests using Playwright or Cypress for web GUI.
- Ensures new tests **cover** specified features and critical flows.

#### c) Web Agent

- Uses Playwright/Selenium inside `web-agent` container.
- Executions:
  - Launch web app.
  - Simulate scenarios (signup, login, critical flows).
  - Capture screenshots + error logs.
- Provides structured feedback to Orchestrator.

#### d) Run & Debug Agent

- Runs commands:
  - `pytest`
  - `npm test`
  - `docker compose up <service>`
  - any user-specified command.
- Collects:
  - stack traces, error logs, failing tests.
- Feeds those back into **Fix Agent**.

#### e) Fix Agent (Auto-fixer)

- Takes:
  - error messages
  - relevant files and tests
  - current architecture spec
- Proposes code changes and applies them.
- Requeues tests until:
  - All tests pass OR
  - A configured failure threshold reached.

#### f) Deploy Agent

- Uses generated Dockerfiles & compose fragments:
  - Build images.
  - Run containers locally.
- Verifies:
  - health check endpoints
  - expected ports open
  - smoke tests.

### 3.4 LLM Router

Abstraction layer:

- `llm_router` chooses between:
  - OpenAI (e.g. GPT-4.1)
  - Anthropic Claude
  - Local HTTP LLM (DeepSeek, Ollama, vLLM, etc.)
- Configurable via **YAML**:

```yaml
llm:
  mode: "hybrid"    # "openai", "claude", "local", "hybrid"
  providers:
    openai:
      enabled: true
      api_key_env: "OPENAI_API_KEY"
      model: "gpt-4.1"
    claude:
      enabled: false
      api_key_env: "ANTHROPIC_API_KEY"
      model: "claude-3.5-sonnet"
    local:
      enabled: true
      base_url: "http://local-llm:8000/v1"
      model: "deepseek-coder"
  routing:
    code_generation: ["local", "openai"]
    planning: ["openai", "claude"]
    testing: ["openai"]
```

- Strategies:
  - **Round-robin**, **fallback**, or **weighted** combination.
  - Support simple ensembling (e.g. two models propose, router reconciles).

Switching from cloud to local is literally changing `llm.mode` and toggling provider enable flags.

### 3.5 Progress Tracker

- Backed by **Postgres**.
- Tables:
  - `projects`: metadata: name, status, created_at, owner, etc.
  - `tasks`: per project sub-tasks and statii.
  - `events`: timeline events (log entries).
  - `artifacts`: links to builds, archives, test reports, screenshots.
- Provides API endpoints for:
  - project summary
  - task timeline
  - detailed events/logs

### 3.6 Web Frontend

SPA (React + TypeScript):

- Views:
  - **Dashboard**: list projects, filters, global activity.
  - **Project Detail**:
    - Timeline of steps (planning → coding → testing → deploy).
    - Real-time logs (WebSockets).
    - Test results, coverage, last run status.
  - **Agents View**:
    - Connected agent runners.
    - Worker health and last activity.
  - **Configuration UI**:
    - Toggle LLM providers.
    - Set concurrency limits, auto-fix thresholds.
- Interacts only with backend API/WS.

### 3.7 Console Agent

- CLI app (Python / Click) that talks to the backend API:

Features:

- `smaker init "Build a multi-tenant SaaS billing system"`
- `smaker status <project_id>`
- `smaker logs <project_id>`
- `smaker add-step <project_id> "Add Stripe integration"`  
- `smaker pause/resume/restart`  

Runs anywhere (local dev laptop, CI machine) but points to central API.

---

## 4. Multi-Project & Multi-Agent Model

- **Multi-project**:
  - Each project has its own workspace directory: `projects/<project_id>/`.
  - Each task gets a **queue item** with project + operation.
  - Workers are stateless and process tasks concurrently.
- **Multi-agent / distributed workers**:
  - Additional worker nodes can join by connecting to the **same Redis + DB**.
  - They advertise capabilities:
    - e.g. `code_python`, `code_frontend`, `web_tests`, `deploy_k8s`, etc.
  - Orchestrator chooses a worker with matching capabilities.

---

## 5. Error Handling & Auto-Fix Loop

1. Worker executes a task (e.g. run tests).
2. If command fails:
   - Captures `stdout/stderr`, exit code.
   - Extracts stack traces and failing lines.
3. Sends a **Debug task** to Fix Agent with:
   - Relevant file contents.
   - Error logs.
   - Tests that failed.
4. Fix Agent:
   - Proposes changes and patches files.
   - Adds a **regression test** if appropriate.
5. Orchestrator:
   - Schedules **re-run** of affected tests.
   - Loops until:
     - all pass; move to next stage
     - or `max_retries` reached → `FAILED` with full log.
