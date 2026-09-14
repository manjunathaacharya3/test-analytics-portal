#!/bin/bash

# ============================================================================
# TAPS - Complete Database Setup Script
# ============================================================================
# This script:
# 1. Drops all existing tables
# 2. Creates all tables with correct schema
# 3. Verifies tables were created
# 4. Tests all major API endpoints
# ============================================================================

set -e  # Exit on error

echo "============================================"
echo "TAPS - Complete Database Setup"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo "[1/6] Checking Docker containers..."
if ! docker compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Starting containers...${NC}"
    docker compose up -d
    echo "Waiting 15 seconds for containers to be ready..."
    sleep 15
else
    echo -e "${GREEN}✅ Containers are running${NC}"
fi
echo ""

echo "[2/6] Verifying PostgreSQL connection..."
if docker compose exec -T postgres psql -U taps_user -d taps -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is accessible${NC}"
else
    echo -e "${RED}❌ Cannot connect to PostgreSQL${NC}"
    echo "Checking postgres logs:"
    docker compose logs --tail=20 postgres
    exit 1
fi
echo ""

echo "[3/6] Creating database schema..."
echo -e "${YELLOW}This will DROP all existing tables and recreate them${NC}"

if docker compose exec -T postgres psql -U taps_user -d taps < backend/COMPLETE_DATABASE_SCHEMA_FIXED.sql > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database schema created successfully (with type corrections)${NC}"
else
    echo -e "${RED}❌ Failed to create schema${NC}"
    echo "Running with output for debugging:"
    docker compose exec -T postgres psql -U taps_user -d taps < backend/COMPLETE_DATABASE_SCHEMA_FIXED.sql
    exit 1
fi
echo ""

echo "[4/6] Verifying tables..."
echo ""
echo "Tables created:"
docker compose exec -T postgres psql -U taps_user -d taps -c "\dt" 2>/dev/null | grep -E "users|projects|modules|reports|scenarios|defects" || echo "Could not list tables"
echo ""

echo "[5/6] Checking table schemas..."
echo ""
echo "Users table structure:"
docker compose exec -T postgres psql -U taps_user -d taps -c "\d users" 2>/dev/null | head -15
echo ""
echo "Projects table structure:"
docker compose exec -T postgres psql -U taps_user -d taps -c "\d projects" 2>/dev/null | head -15
echo ""
echo "Modules table structure:"
docker compose exec -T postgres psql -U taps_user -d taps -c "\d modules" 2>/dev/null | head -15
echo ""

echo "[6/6] Testing API endpoints..."
echo ""

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 5

# Test health endpoint
echo -n "Testing /health endpoint... "
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Test Swagger docs
echo -n "Testing /api/v1/docs endpoint... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/docs | grep -q "200"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Test projects endpoint (should return empty array)
echo -n "Testing /api/v1/projects endpoint... "
RESPONSE=$(curl -s http://localhost:8000/api/v1/projects)
if echo "$RESPONSE" | grep -q '"data"'; then
    echo -e "${GREEN}✅ OK${NC}"
    echo "   Response: $RESPONSE" | cut -c1-100
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "   Response: $RESPONSE"
fi

echo ""
echo "============================================"
echo -e "${GREEN}✅ Database setup complete!${NC}"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Create admin user:"
echo ""
echo "   curl -X POST http://localhost:8000/api/v1/auth/register \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{"
echo "       \"email\": \"admin@taps.local\","
echo "       \"full_name\": \"Admin User\","
echo "       \"password\": \"admin123\","
echo "       \"role\": \"admin\""
echo "     }'"
echo ""
echo "2. Login to get token:"
echo ""
echo "   curl -X POST http://localhost:8000/api/v1/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{"
echo "       \"email\": \"admin@taps.local\","
echo "       \"password\": \"admin123\""
echo "     }'"
echo ""
echo "3. Access frontend:"
echo "   http://localhost:3000"
echo ""
echo "4. Access Swagger API docs:"
echo "   http://localhost:8000/api/v1/docs"
echo ""
echo "5. Access pgAdmin:"
echo "   http://localhost:5050 (admin@gmail.com / admin)"
echo ""
