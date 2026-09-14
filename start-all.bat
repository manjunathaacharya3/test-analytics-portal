@echo off
REM TAPS - Test Analytics Portal System
REM Quick Start Script for Windows

echo ========================================
echo   TAPS - Quick Start
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/5] Checking environment file...
if not exist .env (
    echo   Creating .env from .env.example...
    copy .env.example .env >nul
    echo   [OK] .env file created
) else (
    echo   [OK] .env file exists
)
echo.

echo [2/5] Stopping existing containers...
docker-compose down >nul 2>&1
echo   [OK] Containers stopped
echo.

echo [3/5] Building Docker images...
echo   This may take 2-3 minutes on first run...
docker-compose build
if %ERRORLEVEL% NEQ 0 (
    echo   [ERROR] Build failed!
    pause
    exit /b 1
)
echo   [OK] Build successful
echo.

echo [4/5] Starting all services...
echo   - PostgreSQL (Database)
    - Redis (Cache)
    - Backend API
    - Frontend
    - pgAdmin
echo.
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo   [ERROR] Failed to start services!
    pause
    exit /b 1
)
echo   [OK] All services started
echo.

echo [5/5] Waiting for services to become healthy...
echo   This usually takes 30-60 seconds...
echo.

REM Wait for health checks
timeout /t 10 /nobreak >nul

echo ========================================
echo   TAPS is starting up!
echo ========================================
echo.
echo Service URLs:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/api/v1/docs
echo   pgAdmin:   http://localhost:5050
echo.
echo Check service status:
echo   docker-compose ps
echo.
echo View logs:
echo   docker-compose logs -f
echo.
echo Stop all services:
echo   docker-compose down
echo.
echo ========================================
echo   Opening frontend in browser...
echo ========================================
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo [DONE] TAPS is running!
echo.
pause
