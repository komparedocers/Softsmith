#!/bin/bash

# System verification and testing script

set -e

echo "========================================="
echo "  Software Maker Platform - System Test"
echo "========================================="
echo ""

API_BASE="http://localhost:8000"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    printf "Testing %-30s ... " "$name"

    response=$(curl -s -w "\n%{http_code}" "$url")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    if [ "$http_code" == "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code, expected $expected_code)"
        return 1
    fi
}

echo "1. Testing API Health..."
test_endpoint "API Health" "$API_BASE/health"
echo ""

echo "2. Testing Configuration..."
test_endpoint "Config Endpoint" "$API_BASE/config"
echo ""

echo "3. Testing Agents Status..."
test_endpoint "Agents Status" "$API_BASE/agents/status"
test_endpoint "Agent Capabilities" "$API_BASE/agents/capabilities"
echo ""

echo "4. Testing Projects API..."
test_endpoint "List Projects" "$API_BASE/projects"
echo ""

echo "5. Creating Test Project..."
response=$(curl -s -X POST "$API_BASE/projects" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Create a simple hello world FastAPI app", "name": "Test Project"}')

if echo "$response" | grep -q '"id"'; then
    project_id=$(echo "$response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Project created: $project_id${NC}"
    echo ""

    echo "6. Testing Project Details..."
    test_endpoint "Get Project" "$API_BASE/projects/$project_id"
    test_endpoint "Project Stats" "$API_BASE/projects/$project_id/stats"
    test_endpoint "Project Events" "$API_BASE/projects/$project_id/events"
    echo ""

    echo "7. Monitoring Project for 30 seconds..."
    echo "   (This will show real-time progress)"
    echo ""

    for i in {1..6}; do
        sleep 5
        status=$(curl -s "$API_BASE/projects/$project_id" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        tasks=$(curl -s "$API_BASE/projects/$project_id/stats")
        echo "   [$(date +%H:%M:%S)] Status: $status"
    done

    echo ""
    echo "8. Checking Final Status..."
    final_response=$(curl -s "$API_BASE/projects/$project_id")
    final_status=$(echo "$final_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    echo "   Final Status: $final_status"
    echo ""
else
    echo -e "${RED}✗ Failed to create project${NC}"
    echo ""
fi

echo "9. Testing Web Agent..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Web Agent is accessible${NC}"
else
    echo -e "${YELLOW}⚠ Web Agent is not accessible${NC}"
fi
echo ""

echo "10. Testing Database..."
cd docker
if docker-compose exec -T db pg_isready -U smaker > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database is healthy${NC}"
else
    echo -e "${RED}✗ Database is not healthy${NC}"
fi
cd ..
echo ""

echo "11. Testing Redis..."
cd docker
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is healthy${NC}"
else
    echo -e "${RED}✗ Redis is not healthy${NC}"
fi
cd ..
echo ""

echo "========================================="
echo "  System Test Complete"
echo "========================================="
echo ""
echo "Check logs for detailed information:"
echo "  cd docker && docker-compose logs -f"
echo ""
echo "View test project in browser:"
echo "  http://localhost:3000"
echo ""
