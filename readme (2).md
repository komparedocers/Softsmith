# Software Maker Agent Platform

## 1. Overview

This project is a **multi-agent Software Maker** that turns natural language prompts into fully working software projects.

Features:

- Prompt-driven **project planning** and **code generation**.
- Automatic **test generation**, **execution**, and **auto-fixing** of errors.
- **Web GUI** creation and **web-agent** automation tests.
- **Multi-project** support and real-time **progress tracking**.
- Pluggable LLM providers:
  - OpenAI
  - Claude
  - Local LLM (e.g. DeepSeek)
  - Or combined (hybrid routing).
- Docker Compose-based full stack.

---

## 2. Architecture

High-level components:

- **Backend**: FastAPI, Celery/RQ, Postgres, Redis.
- **Agents**: Planner, Codegen, Tester, Fixer, Deployer, Web Agent.
- **Frontend**: React/TypeScript dashboard.
- **Web Agent**: Playwright-based UI test runner.
- **CLI**: `smaker` command line interface.

See `architecture.md` for deeper diagrams.

---

## 3. Requirements

- Docker & Docker Compose
- (Optional) Python 3.11+ for running CLI locally
- LLM credentials (any subset):
  - OpenAI: `OPENAI_API_KEY`
  - Anthropic: `ANTHROPIC_API_KEY`
  - Local LLM: HTTP endpoint (e.g. DeepSeek)

---

## 4. Configuration

All configuration is in `configs/config.yaml`.

Example:

```yaml
app:
  base_url: "http://localhost:8000"
  projects_dir: "/app/projects"
  max_retries: 5

llm:
  mode: "hybrid"   # "openai", "claude", "local", "hybrid"
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
    planning: ["openai"]
    code_generation: ["local", "openai"]
    debugging: ["openai"]
    tests: ["openai"]

database:
  url: "postgresql+psycopg://smaker:smaker@db:5432/smaker"

redis:
  url: "redis://redis:6379/0"
```

To switch to **local LLM only**, set:

```yaml
llm:
  mode: "local"
  providers:
    openai:
      enabled: false
    claude:
      enabled: false
    local:
      enabled: true
```

No code changes required; just edit config.

---

## 5. Quick Start

1. **Clone repo**

```bash
git clone <your-repo-url> software-maker
cd software-maker
```

2. **Set environment variables**

Create `.env`:

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
# if using local LLM, ensure its URL matches configs/config.yaml
```

3. **Start stack with Docker Compose**

```bash
cd docker
docker compose up --build
```

This starts:

- API (port `8000`)
- Frontend (port `3000`)
- Workers
- DB + Redis
- Web Agent

4. **Open the Web Dashboard**

Visit: `http://localhost:3000`

- Create a new project by entering a prompt.
- Monitor progress, tasks, and logs.

---

## 6. Using the CLI

Install CLI locally (optional):

```bash
cd cli
pip install -e .
smaker --help
```

Examples:

```bash
# Create a new project
smaker init "Build a SaaS subscription billing dashboard with Stripe integration"

# Check project status
smaker status <project_id>

# View logs
smaker logs <project_id>
```

---

## 7. Workflow

1. **Create project**
   - From Web UI or CLI.
2. **Planner Agent**
   - Generates architecture, modules, tasks, test plan.
3. **CodeGen Agent**
   - Creates backend, frontend, infrastructure code.
4. **Test Agent**
   - Generates and runs tests.
5. **Run & Debug Agents**
   - Run tests / app, capture errors, pass to Fix Agent.
6. **Fix Agent**
   - Patches code until tests pass (or retries exhausted).
7. **Deploy Agent**
   - Builds and runs containers locally for the new app.
8. **Web Agent**
   - Executes UI flows and smoke tests the GUI.
9. **Progress Tracker**
   - Shows full timeline and artifact links.

---

## 8. Building Multiple Products Simultaneously

- Each project gets a unique `project_id` and its own workspace directory.
- Workers process tasks from a shared queue.
- To increase capacity:
  - Scale workers:

```bash
docker compose up --scale worker=4
```

- All workers connect to the same Redis + DB and can pick up tasks for any project.

---

## 9. Extending the System

- **Add a new agent type** (e.g., `SecurityAuditAgent`):
  - Implement module under `backend/app/agents/security.py`.
  - Register Celery task.
  - Update orchestrator to insert security tasks in the project DAG.

- **Add a new LLM provider**:
  - Implement adapter in `core/llm_router.py`.
  - Add provider config to `config.yaml`.

- **Change test framework**:
  - Swap pytest with another, modify Test Agent prompts + commands.

---

## 10. Logging & Observability

- Logs are centralized using Python `logging` with configuration from `configs/logging.yaml`.
- Logs are:
  - Printed to stdout (for `docker logs`).
  - Persisted in DB as structured events for per-project views.
- The web UI shows:
  - High-level events per step.
  - Drill-down raw logs when needed.
