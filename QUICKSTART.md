# Software Maker Platform - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option A: Using Cloud LLM (OpenAI or Claude)

1. **Clone and setup**
```bash
cd Softsmith
cp .env.example .env
```

2. **Add your API key**
Edit `.env` and add:
```bash
OPENAI_API_KEY=sk-your-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

3. **Start the platform**
```bash
./start.sh
```

4. **Open the dashboard**
Visit http://localhost:3000

5. **Create your first project!**

---

### Option B: Using Local LLM (100% Free, No API Keys)

1. **Install Ollama**
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai/
```

2. **Pull DeepSeek model**
```bash
ollama pull deepseek-coder
```

3. **Configure for local LLM**
```bash
cd Softsmith
./setup-local-llm.sh
# Select option 1 (Ollama)
```

4. **Start the platform**
```bash
./start.sh
```

---

## 🎯 Your First Software Project

### Via Web Dashboard

1. Open http://localhost:3000
2. In the "Create New Project" box, enter:
   ```
   Build a FastAPI REST API for a todo application with:
   - SQLite database
   - CRUD endpoints for todos
   - Pydantic models
   - Basic authentication
   - Docker deployment
   ```
3. Click "Create Project"
4. Watch it build in real-time!

### Via CLI

```bash
# Install CLI
cd cli
pip install -e .

# Create project
smaker init "Build a React todo app with TypeScript and local storage"

# Check status
smaker status <project-id>

# View logs
smaker logs <project-id> --follow
```

### Via API

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a Python web scraper for news articles with BeautifulSoup",
    "name": "News Scraper"
  }'
```

---

## 📊 Monitor Progress

**Web Dashboard**: http://localhost:3000
- See all projects
- Real-time progress
- View logs and events
- See generated code

**API Docs**: http://localhost:8000/docs
- Interactive API documentation
- Test endpoints
- See schemas

**System Status**: http://localhost:8000/system/verify
- Check all components
- Verify LLM configuration
- See warnings/errors

---

## 🧪 Test the System

Run the automated test suite:

```bash
./test-system.sh
```

This will:
- ✅ Verify all services are running
- ✅ Test API endpoints
- ✅ Create a test project
- ✅ Monitor it for 30 seconds
- ✅ Report any issues

---

## 🔧 Common Commands

```bash
# Start platform
./start.sh

# Stop platform
./stop.sh

# View logs
cd docker && docker-compose logs -f

# View specific service logs
cd docker && docker-compose logs -f worker

# Restart a service
cd docker && docker-compose restart api

# Scale workers
cd docker && docker-compose up --scale worker=4 -d
```

---

## 💡 Example Projects to Try

### 1. REST API
```
Build a FastAPI REST API for a bookstore with:
- PostgreSQL database
- Book CRUD operations
- User authentication with JWT
- Search functionality
- Docker deployment
```

### 2. Web App
```
Create a React dashboard for displaying GitHub statistics with:
- TypeScript
- Chart.js for visualizations
- GitHub API integration
- Responsive design
- Dark mode support
```

### 3. CLI Tool
```
Build a Python CLI tool for file organization that:
- Sorts files by type into folders
- Supports custom rules
- Has undo functionality
- Uses Click framework
- Includes tests
```

### 4. Microservice
```
Create a microservice for image processing that:
- Accepts image uploads
- Resizes and optimizes images
- Uses Pillow library
- Returns processed image URLs
- Includes Docker deployment
```

---

## 🎓 What Happens Under the Hood

When you create a project:

1. **Planner Agent** analyzes your prompt
   - Determines tech stack
   - Plans architecture
   - Creates task breakdown

2. **Codegen Agent** writes the code
   - Generates all files
   - Creates proper structure
   - Follows best practices

3. **Tester Agent** creates and runs tests
   - Unit tests
   - Integration tests
   - Coverage reports

4. **Fixer Agent** debugs automatically
   - Detects errors
   - Fixes failing tests
   - Retries until passing

5. **Deployer Agent** sets up deployment
   - Creates Dockerfile
   - Docker Compose config
   - Starts containers

6. **Web Agent** (optional) tests the UI
   - Automated browser testing
   - Screenshot capture
   - User flow validation

All progress is tracked in real-time on the dashboard!

---

## 🔍 Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker info

# Check logs
cd docker && docker-compose logs

# Restart
cd docker && docker-compose down && docker-compose up -d
```

### No LLM configured
```bash
# Verify configuration
curl http://localhost:8000/system/verify

# Check what's configured
curl http://localhost:8000/config
```

### Worker not processing tasks
```bash
# Check worker logs
cd docker && docker-compose logs worker

# Restart worker
cd docker && docker-compose restart worker
```

---

## 📱 Use the Android App

1. Open `android-app` in Android Studio
2. Update API URL in `ApiClient.java`:
   ```java
   private static final String BASE_URL = "http://YOUR_IP:8000/";
   ```
3. Build and run on device/emulator
4. Create and track projects on mobile!

---

## 🎉 Next Steps

- Read the [full README](README.md) for detailed information
- Check [SETUP.md](SETUP.md) for advanced configuration
- Review [architecture.md](architecture.md) to understand the system
- Join our community and share what you built!

---

**Happy Building! 🚀**

If you run into issues, check logs with `docker-compose logs -f` or run `./test-system.sh`
