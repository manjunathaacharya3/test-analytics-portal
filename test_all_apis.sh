#!/bin/bash

# ============================================================================
# TAPS - Complete API Testing Script
# ============================================================================
# Tests all major API endpoints to ensure they work correctly
# ============================================================================

set -e

BASE_URL="http://localhost:8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "============================================"
echo "🧪 TAPS - Complete API Testing"
echo "============================================"
echo ""

# Check if backend is running
echo "Checking if backend is accessible..."
if ! curl -s -f $BASE_URL/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend is not accessible at $BASE_URL${NC}"
    echo "Please ensure Docker containers are running:"
    echo "  docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✅ Backend is accessible${NC}"
echo ""

PASSED=0
FAILED=0

# Test function
test_api() {
    local test_name="$1"
    local expected_status="$2"
    shift 2
    local curl_args=("$@")
    
    echo -n "Testing: $test_name... "
    
    response=$(curl -s -w "\n%{http_code}" "${curl_args[@]}")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS ($http_code)${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL (Expected: $expected_status, Got: $http_code)${NC}"
        echo "   Response: $body" | head -c 100
        echo ""
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# ============================================================================
# 1. HEALTH & SYSTEM ENDPOINTS
# ============================================================================

echo -e "${BLUE}[1/8] Testing Health & System Endpoints${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_api "Health check" "200" \
    $BASE_URL/health

test_api "Swagger docs" "200" \
    -o /dev/null $BASE_URL/api/v1/docs

test_api "ReDoc" "200" \
    -o /dev/null $BASE_URL/api/v1/redoc

echo ""

# ============================================================================
# 2. AUTHENTICATION - REGISTER
# ============================================================================

echo -e "${BLUE}[2/8] Testing Authentication - Register${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Generate random email to avoid duplicates
RANDOM_EMAIL="test$(date +%s)@taps.local"

echo "Registering user: $RANDOM_EMAIL"
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BASE_URL/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "email": "'$RANDOM_EMAIL'",
        "full_name": "Test User",
        "password": "test123",
        "role": "admin"
    }')

REGISTER_CODE=$(echo "$REGISTER_RESPONSE" | tail -n1)
REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | sed '$d')

if [ "$REGISTER_CODE" = "200" ] || [ "$REGISTER_CODE" = "201" ]; then
    echo -e "${GREEN}✅ User registration successful${NC}"
    PASSED=$((PASSED + 1))
    USER_ID=$(echo "$REGISTER_BODY" | jq -r '.id')
    echo "   User ID: $USER_ID"
else
    echo -e "${RED}❌ User registration failed ($REGISTER_CODE)${NC}"
    echo "   Response: $REGISTER_BODY"
    FAILED=$((FAILED + 1))
fi

echo ""

# ============================================================================
# 3. AUTHENTICATION - LOGIN
# ============================================================================

echo -e "${BLUE}[3/8] Testing Authentication - Login${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Logging in as: $RANDOM_EMAIL"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BASE_URL/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "email": "'$RANDOM_EMAIL'",
        "password": "test123"
    }')

LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | sed '$d')

if [ "$LOGIN_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Login successful${NC}"
    PASSED=$((PASSED + 1))
    TOKEN=$(echo "$LOGIN_BODY" | jq -r '.access_token')
    echo "   Token: ${TOKEN:0:50}..."
else
    echo -e "${RED}❌ Login failed ($LOGIN_CODE)${NC}"
    echo "   Response: $LOGIN_BODY"
    FAILED=$((FAILED + 1))
    echo ""
    echo "Cannot proceed without authentication token. Exiting."
    exit 1
fi

echo ""

# ============================================================================
# 4. AUTHENTICATION - GET CURRENT USER
# ============================================================================

echo -e "${BLUE}[4/8] Testing Authentication - Get Current User${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_api "Get current user" "200" \
    -H "Authorization: Bearer $TOKEN" \
    $BASE_URL/api/v1/auth/me

echo ""

# ============================================================================
# 5. PROJECTS - LIST (EMPTY)
# ============================================================================

echo -e "${BLUE}[5/8] Testing Projects - List (should be empty or have data)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_api "List projects" "200" \
    $BASE_URL/api/v1/projects

echo ""

# ============================================================================
# 6. PROJECTS - CREATE
# ============================================================================

echo -e "${BLUE}[6/8] Testing Projects - Create${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PROJECT_NAME="Test Project $(date +%s)"

echo "Creating project: $PROJECT_NAME"
CREATE_PROJECT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BASE_URL/api/v1/projects \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "'$PROJECT_NAME'",
        "description": "Created by automated test script",
        "repository_url": "https://github.com/test/repo",
        "owner": "'$RANDOM_EMAIL'"
    }')

CREATE_CODE=$(echo "$CREATE_PROJECT_RESPONSE" | tail -n1)
CREATE_BODY=$(echo "$CREATE_PROJECT_RESPONSE" | sed '$d')

if [ "$CREATE_CODE" = "200" ] || [ "$CREATE_CODE" = "201" ]; then
    echo -e "${GREEN}✅ Project created successfully${NC}"
    PASSED=$((PASSED + 1))
    PROJECT_ID=$(echo "$CREATE_BODY" | jq -r '.id')
    echo "   Project ID: $PROJECT_ID"
else
    echo -e "${RED}❌ Project creation failed ($CREATE_CODE)${NC}"
    echo "   Response: $CREATE_BODY"
    FAILED=$((FAILED + 1))
fi

echo ""

# ============================================================================
# 7. PROJECTS - GET BY ID
# ============================================================================

echo -e "${BLUE}[7/8] Testing Projects - Get by ID${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$PROJECT_ID" ] && [ "$PROJECT_ID" != "null" ]; then
    test_api "Get project by ID" "200" \
        $BASE_URL/api/v1/projects/$PROJECT_ID
else
    echo -e "${YELLOW}⚠️  Skipping (no project ID)${NC}"
fi

echo ""

# ============================================================================
# 8. DEFECTS - LIST
# ============================================================================

echo -e "${BLUE}[8/8] Testing Defects - List${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_api "List defects" "200" \
    $BASE_URL/api/v1/defects

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "============================================"
echo "📊 Test Results Summary"
echo "============================================"
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Your TAPS installation is working correctly!"
    echo ""
    echo "Next steps:"
    echo "  1. Access frontend: http://localhost:3000"
    echo "  2. Login with: $RANDOM_EMAIL / test123"
    echo "  3. Access API docs: http://localhost:8000/api/v1/docs"
    echo "  4. Access pgAdmin: http://localhost:5050"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please check:"
    echo "  1. Docker containers are running: docker compose ps"
    echo "  2. Database tables exist: docker compose exec postgres psql -U taps_user -d taps -c '\\dt'"
    echo "  3. Backend logs: docker compose logs backend"
    echo ""
    exit 1
fi
