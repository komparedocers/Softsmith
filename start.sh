#!/bin/bash

# Software Maker Platform - Quick Start Script

set -e

echo "========================================="
echo "  Software Maker Platform - Quick Start"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys!"
    echo "   You need at least one of:"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - Or configure a local LLM in configs/config.yaml"
    echo ""
    read -p "Press Enter after configuring .env to continue..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p projects logs

# Start services
echo ""
echo "Starting services with Docker Compose..."
echo "This may take a few minutes on first run..."
echo ""

cd docker
docker-compose up --build -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
echo ""
echo "Checking service health..."
echo ""

# Check API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ API is running on http://localhost:8000"
else
    echo "⚠️  API may still be starting... check logs with: docker-compose logs api"
fi

# Check Web
if curl -s http://localhost:3000 > /dev/null; then
    echo "✓ Web Dashboard is running on http://localhost:3000"
else
    echo "⚠️  Web Dashboard may still be starting..."
fi

# Check Web Agent
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✓ Web Agent is running on http://localhost:5000"
else
    echo "⚠️  Web Agent may still be starting..."
fi

echo ""
echo "========================================="
echo "  Services Started Successfully!"
echo "========================================="
echo ""
echo "Access points:"
echo "  📊 Web Dashboard: http://localhost:3000"
echo "  🔌 API: http://localhost:8000"
echo "  📖 API Docs: http://localhost:8000/docs"
echo "  🤖 Web Agent: http://localhost:5000"
echo ""
echo "Useful commands:"
echo "  View logs: cd docker && docker-compose logs -f"
echo "  Stop services: cd docker && docker-compose down"
echo "  Restart: cd docker && docker-compose restart"
echo ""
echo "To test the system:"
echo "  ./test-system.sh"
echo ""
echo "Happy building! 🚀"
echo ""
