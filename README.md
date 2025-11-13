# Software Maker Platform 🚀

> AI-Powered Full-Stack Software Generation Platform

An autonomous multi-agent system that generates complete, production-ready software from natural language prompts. Features automatic planning, code generation, testing, debugging, and deployment.

## ✨ Features

### Core Capabilities
- **🤖 Multi-Agent Architecture**: Specialized agents for planning, coding, testing, debugging, and deployment
- **🧠 Multiple LLM Support**: Switch between OpenAI, Claude, and local LLMs (DeepSeek, Ollama)
- **🔄 Auto-Fix Loop**: Automatically detects and fixes errors until tests pass
- **🧪 Automated Testing**: Generates and runs unit, integration, and E2E tests
- **🌐 Web UI Testing**: Playwright-based automated GUI testing
- **📦 Multi-Project**: Build multiple software projects simultaneously
- **🔍 Real-Time Progress**: Track build progress via web dashboard, CLI, or Android app
- **🐙 Git Integration**: Automatic commits to GitHub/GitLab
- **🐳 Docker-Based**: Full Docker Compose infrastructure

### Interfaces
1. **Web Dashboard** - React/TypeScript SPA
2. **CLI Tool** - Python command-line interface
3. **Android App** - Java mobile application
4. **REST API** - Complete FastAPI backend

## 📋 Architecture

```
┌─────────────┐         ┌──────────────────────┐
│ Web/CLI/App │────────▶│   FastAPI Gateway    │
└─────────────┘         └──────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              ┌─────────┐   ┌─────────┐   ┌─────────┐
              │  Redis  │   │Postgres │   │  LLM    │
              │  Queue  │   │   DB    │   │ Router  │
              └─────────┘   └─────────┘   └─────────┘
                    │
            ┌───────┴───────┐
            ▼               ▼
      ┌──────────┐    ┌──────────┐
      │ Celery   │    │   Web    │
      │ Workers  │    │  Agent   │
      └──────────┘    └──────────┘
```

### Agent Types
- **Planner**: Analyzes prompts and creates project specifications
- **Codegen**: Generates source code from specifications
- **Tester**: Creates and runs test suites
- **Fixer**: Automatically fixes bugs and failing tests
- **Deployer**: Builds and deploys applications
- **Web Agent**: Performs automated UI testing with Playwright

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for CLI)
- Node.js 18+ (for frontend development)
- API keys (at least one):
  - OpenAI API key
  - Anthropic API key
  - Or local LLM endpoint

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd Softsmith
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. **Start the platform**
```bash
cd docker
docker-compose up --build
```

This will start:
- API server on http://localhost:8000
- Web dashboard on http://localhost:3000
- PostgreSQL on port 5432
- Redis on port 6379
- Celery workers
- Web agent service

4. **Access the dashboard**
Open http://localhost:3000 in your browser

## 📱 Usage

### Web Dashboard

1. Navigate to http://localhost:3000
2. Click "Create New Project"
3. Enter a description of the software you want to build
4. Monitor progress in real-time
5. View logs, tasks, and generated code

### CLI Tool

```bash
# Install CLI
cd cli
pip install -e .

# Create a project
smaker init "Build a RESTful API for a todo app with FastAPI and SQLite"

# Check status
smaker status <project_id>

# View logs
smaker logs <project_id>

# List all projects
smaker list

# Pause/resume
smaker pause <project_id>
smaker resume <project_id>
```

### Android App

1. Open `android-app` in Android Studio
2. Update API URL in `ApiClient.java` if needed
3. Build and run on emulator or device
4. Create projects and track progress on mobile

### REST API

```bash
# Create project
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Build a blog API with authentication"}'

# Get project status
curl http://localhost:8000/projects/{project_id}

# Get project logs
curl http://localhost:8000/projects/{project_id}/events
```

## ⚙️ Configuration

### LLM Configuration

Edit `configs/config.yaml`:

```yaml
llm:
  mode: "hybrid"  # openai, claude, local, or hybrid
  providers:
    openai:
      enabled: true
      model: "gpt-4-turbo-preview"
    claude:
      enabled: false
      model: "claude-3-sonnet-20240229"
    local:
      enabled: false
      base_url: "http://localhost:8000/v1"
      model: "deepseek-coder"
  routing:
    planning: ["openai"]
    code_generation: ["openai", "local"]
    debugging: ["openai"]
```

### Switch to Local LLM Only

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
      base_url: "http://your-llm:8000/v1"
      model: "deepseek-coder"
```

### Scaling Workers

```bash
# Scale up workers for more concurrent projects
docker-compose up --scale worker=4
```

## 🏗️ Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt

# Run API
uvicorn app.main:app --reload

# Run worker
celery -A app.worker.celery_app worker --loglevel=info
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📂 Project Structure

```
Softsmith/
├── backend/              # Python/FastAPI backend
│   ├── app/
│   │   ├── agents/      # Agent implementations
│   │   ├── api/         # REST API routers
│   │   ├── core/        # Core modules (config, db, llm)
│   │   ├── models/      # Database models
│   │   └── services/    # Business logic
│   └── requirements.txt
├── frontend/            # React/TypeScript web app
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
│   └── package.json
├── web-agent/           # Playwright web testing service
│   ├── runner.py
│   └── Dockerfile
├── cli/                 # Python CLI tool
│   ├── smaker/
│   │   └── main.py
│   └── setup.py
├── android-app/         # Android mobile app (Java)
│   └── app/src/main/java/com/softsmith/maker/
├── docker/              # Docker infrastructure
│   ├── docker-compose.yml
│   └── Dockerfile.*
├── configs/             # Configuration files
│   ├── config.yaml
│   └── logging.yaml
├── projects/            # Generated project workspaces
└── README.md
```

## 🔌 API Endpoints

### Projects
- `POST /projects` - Create a new project
- `GET /projects` - List all projects
- `GET /projects/{id}` - Get project details
- `PATCH /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project
- `POST /projects/{id}/pause` - Pause project
- `POST /projects/{id}/resume` - Resume project
- `GET /projects/{id}/stats` - Get project statistics
- `GET /projects/{id}/events` - Get project logs
- `GET /projects/{id}/timeline` - Get project timeline
- `WS /projects/{id}/events/ws` - WebSocket for real-time updates

### Tasks
- `GET /tasks` - List tasks
- `GET /tasks/{id}` - Get task details
- `GET /tasks/{id}/events` - Get task logs

### Configuration
- `GET /config` - Get system configuration
- `POST /config/reload` - Reload configuration

### Agents
- `GET /agents/status` - Get worker status
- `GET /agents/capabilities` - List agent capabilities

## 🧪 Testing Strategy

The system automatically:

1. **Generates Tests**: Creates unit, integration, and E2E tests
2. **Runs Tests**: Executes all tests
3. **Captures Failures**: Logs stack traces and error details
4. **Auto-Fixes**: Uses LLM to fix failing tests
5. **Reruns**: Continues until all tests pass or max retries reached
6. **Web Testing**: Playwright tests for GUI applications

## 🔒 Security Notes

- Never commit API keys to version control
- Use environment variables for sensitive data
- Restrict CORS origins in production
- Use HTTPS in production
- Implement proper authentication/authorization
- Sandbox generated code execution
- Review generated code before deployment

## 🛠️ Troubleshooting

### Workers not starting
```bash
# Check Redis connection
docker-compose ps redis

# View worker logs
docker-compose logs worker
```

### Database connection issues
```bash
# Check database status
docker-compose ps db

# Reset database
docker-compose down -v
docker-compose up -d
```

### LLM API errors
- Verify API keys in `.env`
- Check API rate limits
- Try switching LLM providers in config

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude
- LangChain for orchestration patterns
- FastAPI for the excellent web framework
- Playwright for web automation

## 📞 Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Email: support@softsmith.ai

---

**Built with ❤️ by the Softsmith Team**
