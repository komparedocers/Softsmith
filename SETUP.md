# Software Maker Platform - Detailed Setup Guide

This guide provides step-by-step instructions for setting up the Software Maker Platform.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Platform](#running-the-platform)
5. [Verification](#verification)
6. [Advanced Setup](#advanced-setup)

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 20 GB free space
- **OS**: Linux, macOS, or Windows with WSL2

### Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Disk**: 50+ GB SSD
- **OS**: Linux or macOS

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Python 3.11+ (for CLI tool)
- Node.js 18+ (for frontend development)
- Android Studio (for mobile app development)

## Installation

### 1. Install Docker

#### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### macOS
Download Docker Desktop from https://www.docker.com/products/docker-desktop

#### Windows
Install Docker Desktop with WSL2 backend

### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/Softsmith.git
cd Softsmith
```

### 3. Setup Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and configure:

```bash
# Required: At least one LLM API key
OPENAI_API_KEY=sk-...
# Or
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Git integration
GITHUB_TOKEN=ghp_...
GITLAB_TOKEN=glpat-...

# Optional: Database (defaults are fine for development)
DATABASE_URL=postgresql+asyncpg://smaker:smaker@db:5432/smaker
REDIS_URL=redis://redis:6379/0
```

## Configuration

### 1. LLM Configuration

Edit `configs/config.yaml`:

#### Option A: OpenAI Only
```yaml
llm:
  mode: "openai"
  providers:
    openai:
      enabled: true
      api_key_env: "OPENAI_API_KEY"
      model: "gpt-4-turbo-preview"
```

#### Option B: Claude Only
```yaml
llm:
  mode: "claude"
  providers:
    claude:
      enabled: true
      api_key_env: "ANTHROPIC_API_KEY"
      model: "claude-3-sonnet-20240229"
```

#### Option C: Local LLM (DeepSeek, Ollama, etc.)

First, start your local LLM server:

```bash
# Example with Ollama
ollama serve
ollama pull deepseek-coder

# Or with vLLM
python -m vllm.entrypoints.openai.api_server \
  --model deepseek-ai/deepseek-coder-6.7b-instruct
```

Then configure:

```yaml
llm:
  mode: "local"
  providers:
    local:
      enabled: true
      base_url: "http://host.docker.internal:11434/v1"  # Ollama
      # Or: "http://host.docker.internal:8000/v1"  # vLLM
      model: "deepseek-coder"
```

#### Option D: Hybrid (Fallback)
```yaml
llm:
  mode: "hybrid"
  fallback_enabled: true
  providers:
    openai:
      enabled: true
    local:
      enabled: true
  routing:
    planning: ["openai"]
    code_generation: ["local", "openai"]  # Try local first
    debugging: ["openai"]
```

### 2. Application Configuration

Edit `configs/config.yaml`:

```yaml
app:
  max_retries: 5              # Max auto-fix attempts
  max_concurrent_projects: 10 # Concurrent projects
  max_fix_attempts: 5         # Fix attempts per error
  worker_concurrency: 4       # Celery worker threads
```

### 3. Database Configuration

Default settings work for development. For production:

```yaml
database:
  url: "postgresql+asyncpg://user:pass@host:5432/dbname"
  pool_size: 20
  max_overflow: 10
```

## Running the Platform

### 1. Start All Services

```bash
cd docker
docker-compose up --build
```

This starts:
- **API**: http://localhost:8000
- **Web Dashboard**: http://localhost:3000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Celery Workers**: Background
- **Web Agent**: localhost:5000

### 2. Verify Services

Check all containers are running:

```bash
docker-compose ps
```

Expected output:
```
NAME                STATUS              PORTS
docker-api-1        running             0.0.0.0:8000->8000/tcp
docker-worker-1     running
docker-web-1        running             0.0.0.0:3000->80/tcp
docker-web-agent-1  running             0.0.0.0:5000->5000/tcp
docker-db-1         running             0.0.0.0:5432->5432/tcp
docker-redis-1      running             0.0.0.0:6379->6379/tcp
```

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

## Verification

### 1. Health Checks

```bash
# API health
curl http://localhost:8000/health

# Web Agent health
curl http://localhost:5000/health

# Web Dashboard
curl http://localhost:3000
```

### 2. Create Test Project

Using the API:

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a simple Hello World FastAPI application with a health check endpoint",
    "name": "Test Project"
  }'
```

Save the returned `project_id` and check status:

```bash
curl http://localhost:8000/projects/{project_id}
```

### 3. Install CLI Tool

```bash
cd cli
pip install -e .

# Test CLI
smaker --help
smaker list
```

## Advanced Setup

### Running Individual Components

#### Backend Only

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL and Redis
docker-compose up -d db redis

# Run API
uvicorn app.main:app --reload

# Run worker (in another terminal)
celery -A app.worker.celery_app worker --loglevel=info
```

#### Frontend Only

```bash
cd frontend
npm install
npm run dev
```

### Production Deployment

#### 1. Use Production Configuration

```yaml
# configs/config.yaml
app:
  base_url: "https://your-domain.com"

database:
  url: "postgresql+asyncpg://user:pass@prod-db:5432/smaker"
  pool_size: 50
  echo: false

logging:
  level: "WARNING"
  log_to_file: true
```

#### 2. Use Production Docker Compose

```yaml
# docker/docker-compose.prod.yml
services:
  api:
    restart: always
    environment:
      - DEBUG=false
    deploy:
      replicas: 2

  worker:
    restart: always
    deploy:
      replicas: 4
```

#### 3. Setup Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

### Scaling

#### Scale Workers

```bash
# Scale to 8 workers
docker-compose up --scale worker=8
```

#### Scale API

```bash
# Scale API instances
docker-compose up --scale api=3
```

Then add load balancer in front.

### Backup and Recovery

#### Backup Database

```bash
docker-compose exec db pg_dump -U smaker smaker > backup.sql
```

#### Restore Database

```bash
cat backup.sql | docker-compose exec -T db psql -U smaker smaker
```

#### Backup Projects

```bash
tar -czf projects-backup.tar.gz projects/
```

### Monitoring

#### View Metrics

```bash
# Worker stats
docker-compose exec worker celery -A app.worker.celery_app inspect stats

# Active tasks
docker-compose exec worker celery -A app.worker.celery_app inspect active
```

#### Setup Prometheus (Optional)

Add to docker-compose.yml:

```yaml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

## Troubleshooting

### Issue: Cannot connect to API

**Solution:**
```bash
# Check if API is running
docker-compose ps api

# Check logs
docker-compose logs api

# Restart API
docker-compose restart api
```

### Issue: Workers not processing tasks

**Solution:**
```bash
# Check Redis connection
docker-compose ps redis

# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

### Issue: Out of memory

**Solution:**
```bash
# Reduce worker concurrency
# Edit docker-compose.yml
worker:
  command: celery -A app.worker.celery_app worker --loglevel=info --concurrency=2

# Or scale down workers
docker-compose up --scale worker=1
```

### Issue: Database connection errors

**Solution:**
```bash
# Reset database
docker-compose down -v
docker-compose up -d db
docker-compose up -d
```

## Next Steps

1. Read the [Architecture Documentation](architecture.md)
2. Explore the [API Documentation](http://localhost:8000/docs)
3. Try creating your first project
4. Customize configuration for your use case
5. Set up monitoring and logging
6. Deploy to production

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs`
3. Open an issue on GitHub
4. Join our Discord community

---

Happy Building! 🚀
