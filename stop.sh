#!/bin/bash

# Stop all services

echo "Stopping Software Maker Platform services..."

cd docker
docker-compose down

echo "✓ All services stopped"
echo ""
echo "To remove all data (including database):"
echo "  cd docker && docker-compose down -v"
