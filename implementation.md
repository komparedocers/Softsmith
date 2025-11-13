# Software Maker Agent Platform – Implementation

## 1. Tech Stack Summary

- **Backend**
  - Python, FastAPI
  - LangChain (or similar) for LLM orchestration
  - Celery / RQ for background workers
- **Frontend**
  - React + TypeScript + Vite
- **Infra**
  - Docker Compose
  - Postgres
  - Redis
  - Playwright (web agent)
- **LLMs**
  - OpenAI, Claude, local LLM (DeepSeek) via HTTP
- **CLI**
  - Python (Click/Typer)

---

## 2. Directory Structure

```text
software-maker/
  backend/
    app/
      api/
        routers/
          projects.py
          tasks.py
          config.py
          agents.py
      core/
        config.py
        db.py
        logging.py
        llm_router.py
        task_queue.py
      agents/
        planner.py
        codegen.py
        tester.py
        fixer.py
        deployer.py
        web_agent_client.py
      models/
        project.py
        task.py
        event.py
        artifact.py
      services/
        orchestrator.py
        project_service.py
        progress_service.py
      main.py
      worker.py
    tests/
      ...
  frontend/
    src/
      components/
      pages/
      api/
      store/
    index.html
    package.json
  web-agent/
    Dockerfile
    runner.py     # receives tasks, runs Playwright, reports results
  cli/
    smaker/
      __init__.py
      main.py
  docker/
    docker-compose.yml
    Dockerfile.api
    Dockerfile.web
    Dockerfile.web_agent
  configs/
    config.yaml
    logging.yaml
  projects/       # generated code per project
  README.md
  architecture.md
  implementation.md
```

---

## 3. Key Backend Modules

### 3.1 Config & LLM Router

- `core/config.py`
  - Loads YAML/ENV config.
  - Exposes: DB URL, Redis URL, LLM config, concurrency limits.

- `core/llm_router.py`
  - Exposes: `async def call_llm(role: str, prompt: str, context: dict) -> str`
  - Internal logic:
    - Choose provider(s) based on `role` (e.g. `"code_generation"`).
    - Execute call(s).
    - Aggregate or pick best result.

### 3.2 Task Queue

- `core/task_queue.py`
  - Wrapper around Celery or RQ task decorators.
  - Example tasks:
    - `run_planner(project_id)`
    - `run_codegen_task(task_id)`
    - `run_tests(project_id)`
    - `run_fix(project_id, error_payload)`
    - `run_deploy(project_id)`
    - `run_web_tests(project_id)`

### 3.3 Orchestrator

- `services/orchestrator.py`

Pseudo-workflow:

```python
class Orchestrator:
    def create_project(self, prompt: str, user_id: str) -> Project:
        project = Project.create_from_prompt(prompt, user_id)
        self.schedule_planning(project.id)
        return project

    def schedule_planning(self, project_id: str):
        # async task to planner agent
        task_queue.run_planner.delay(project_id)

    def on_planning_done(self, project_id: str, spec: dict):
        # create tasks from spec (code, tests, infra, etc.)
        task_service.create_tasks_from_spec(project_id, spec)
        self.schedule_next_tasks(project_id)

    def schedule_next_tasks(self, project_id: str):
        ready_tasks = task_service.get_ready_tasks(project_id)
        for task in ready_tasks:
            if task.type == "CODEGEN":
                task_queue.run_codegen_task.delay(task.id)
            elif task.type == "TESTS":
                task_queue.run_tests.delay(project_id)
            elif task.type == "DEPLOY":
                task_queue.run_deploy.delay(project_id)
            # etc...

    def handle_failure(self, project_id: str, error_payload: dict):
        # delegate to Fix Agent
        task_queue.run_fix.delay(project_id, error_payload)
```

Callbacks from workers update `Task` and `Project` state and re-schedule.

### 3.4 Agents

Each agent is a **Celery task** that uses `llm_router` and file tools.

Example: **CodeGen Agent**

```python
# agents/codegen.py
from .tools import read_repo_context, write_file

def build_prompt(task, repo_context):
    # Compose system + user messages for LLM
    ...

def apply_changes(files_diff):
    for path, content in files_diff.items():
        write_file(task.project_id, path, content)

def generate_code_for_task(task_id: str):
    task = task_service.get(task_id)
    repo_ctx = read_repo_context(task.project_id)
    prompt = build_prompt(task, repo_ctx)
    response = llm_router.call_llm("code_generation", prompt, {"context": repo_ctx})
    files_diff = parse_files_from_response(response)
    apply_changes(files_diff)
    task_service.mark_done(task_id)
```

Example: **Fix Agent**

```python
# agents/fixer.py
def fix_errors(project_id: str, error_payload: dict):
    repo_ctx = read_repo_context(project_id, files=error_payload["files"])
    prompt = build_fix_prompt(error_payload, repo_ctx)
    response = llm_router.call_llm("debugging", prompt, {"context": repo_ctx})
    files_diff = parse_files_from_response(response)
    apply_changes(project_id, files_diff)
    orchestrator.schedule_next_tasks(project_id)  # rerun tests
```

Example: **Web Agent Client**

```python
# agents/web_agent_client.py
def run_web_tests(project_id: str):
    # POST to web-agent service with test scenarios and base URL
    ...
```

The `web-agent/runner.py` receives tasks, uses Playwright to perform flows, returns structured results.

---

## 4. Frontend Implementation Outline

React/TS:

- `pages/Dashboard.tsx`
  - Fetch `GET /projects`
  - List & basic stats/status
- `pages/ProjectDetail.tsx`
  - `GET /projects/{id}`
  - `GET /projects/{id}/tasks`
  - WebSocket to `/ws/projects/{id}/events`
  - Timeline + logs + test status
- `pages/Settings.tsx`
  - Shows and updates (via API) LLM & global settings.

---

## 5. Console CLI Agent

Using Typer:

```python
import typer
import requests

app = typer.Typer()

API_BASE = "http://localhost:8000"

@app.command()
def init(prompt: str):
    r = requests.post(f"{API_BASE}/projects", json={"prompt": prompt})
    typer.echo(r.json())

@app.command()
def status(project_id: str):
    r = requests.get(f"{API_BASE}/projects/{project_id}")
    typer.echo(r.json())

@app.command()
def logs(project_id: str):
    r = requests.get(f"{API_BASE}/projects/{project_id}/events")
    for e in r.json():
        typer.echo(f"[{e['timestamp']}] {e['level']}: {e['message']}")

if __name__ == "__main__":
    app()
```

---

## 6. Docker Compose Skeleton

`docker/docker-compose.yml`:

```yaml
version: "3.9"
services:
  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    env_file:
      - ../.env
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"
    volumes:
      - ../projects:/app/projects
      - ../configs:/app/configs

  worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    command: ["celery", "-A", "app.worker", "worker", "-l", "INFO"]
    env_file:
      - ../.env
    depends_on:
      - api
      - db
      - redis
    volumes:
      - ../projects:/app/projects
      - ../configs:/app/configs

  web:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.web
    ports:
      - "3000:80"
    depends_on:
      - api

  web-agent:
    build:
      context: ../web-agent
      dockerfile: Dockerfile.web_agent
    depends_on:
      - api

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: smaker
      POSTGRES_PASSWORD: smaker
      POSTGRES_DB: smaker
    volumes:
      - db_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  db_data:
```

