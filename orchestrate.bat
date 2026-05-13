@echo off
REM Financial Intelligence Platform - Docker & ETL Orchestration Script (Windows)
REM This script manages Docker containers, Celery tasks, and ETL pipeline execution

setlocal enabledelayedexpansion
set PROJECT_NAME=fintech
set COMPOSE_FILE=docker-compose.yml

REM Colors are not supported in batch, using text only
echo.
echo ========================================
echo Financial Intelligence Platform
echo Docker ^& ETL Orchestration
echo ========================================
echo.

if "%1"=="" goto show_help
if /i "%1"=="help" goto show_help
if /i "%1"=="build" goto build
if /i "%1"=="start" goto start
if /i "%1"=="stop" goto stop
if /i "%1"=="restart" goto restart
if /i "%1"=="status" goto status
if /i "%1"=="logs" goto logs
if /i "%1"=="migrate" goto migrate
if /i "%1"=="create-superuser" goto create_superuser
if /i "%1"=="run-etl" goto run_etl
if /i "%1"=="run-ml-scoring" goto run_ml_scoring
if /i "%1"=="run-ml-incremental" goto run_ml_incremental
if /i "%1"=="celery-status" goto celery_status
if /i "%1"=="celery-purge" goto celery_purge
if /i "%1"=="clean" goto clean

echo [ERROR] Unknown command: %1
goto show_help

:check_docker
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running
    exit /b 1
)
exit /b 0

:setup_env
echo [*] Setting up environment...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo [OK] Created .env from .env.example
    ) else (
        echo [ERROR] .env.example not found
        exit /b 1
    )
) else (
    echo [OK] .env already exists
)
if not exist data\raw mkdir data\raw
if not exist data\clean mkdir data\clean
if not exist logs mkdir logs
echo [OK] Created data and logs directories
exit /b 0

:build
echo.
echo ========================================
echo Building Docker Images
echo ========================================
call :check_docker
if errorlevel 1 exit /b 1
docker-compose -f %COMPOSE_FILE% build
if errorlevel 1 (
    echo [ERROR] Build failed
    exit /b 1
)
echo [OK] Images built successfully
exit /b 0

:start
echo.
echo ========================================
echo Starting Services
echo ========================================
call :check_docker
if errorlevel 1 exit /b 1

call :setup_env
if errorlevel 1 exit /b 1

echo [*] Starting database...
docker-compose -f %COMPOSE_FILE% up -d db
timeout /t 5 /nobreak >nul

echo [*] Starting Redis...
docker-compose -f %COMPOSE_FILE% up -d redis
timeout /t 3 /nobreak >nul

echo [*] Starting web application...
docker-compose -f %COMPOSE_FILE% up -d web

echo [*] Starting Celery worker...
docker-compose -f %COMPOSE_FILE% up -d celery_worker

echo [*] Starting Celery beat scheduler...
docker-compose -f %COMPOSE_FILE% up -d celery_beat

echo [OK] All services started
echo [*] Web application: http://localhost:8000
echo [*] Redis: localhost:6379
echo [*] PostgreSQL: localhost:5432
exit /b 0

:stop
echo.
echo ========================================
echo Stopping Services
echo ========================================
docker-compose -f %COMPOSE_FILE% down
echo [OK] All services stopped
exit /b 0

:restart
echo.
echo ========================================
echo Restarting Services
echo ========================================
call :stop
timeout /t 2 /nobreak >nul
call :start
exit /b 0

:status
echo.
echo ========================================
echo Service Status
echo ========================================
docker-compose -f %COMPOSE_FILE% ps
exit /b 0

:logs
if "%2"=="" (
    echo [*] Showing all logs (Ctrl+C to exit)
    docker-compose -f %COMPOSE_FILE% logs -f
) else (
    echo [*] Showing logs for: %2
    docker-compose -f %COMPOSE_FILE% logs -f %2
)
exit /b 0

:migrate
echo.
echo ========================================
echo Running Database Migrations
echo ========================================
docker-compose -f %COMPOSE_FILE% exec -T web python manage.py migrate
echo [OK] Migrations completed
exit /b 0

:create_superuser
echo.
echo ========================================
echo Creating Superuser
echo ========================================
docker-compose -f %COMPOSE_FILE% exec web python manage.py createsuperuser
exit /b 0

:run_etl
echo.
echo ========================================
echo Running ETL Pipeline
echo ========================================
set MODE=%2
set TASK=%3
if "!MODE!"=="" set MODE=async

set DOCKER_EXEC=docker-compose -f %COMPOSE_FILE% exec -T web python manage.py run_etl

if /i "!MODE!"=="sync" (
    echo [*] Running ETL in synchronous mode...
    !DOCKER_EXEC!
) else (
    echo [*] Running ETL in asynchronous mode...
    if /i "!TASK!"=="extract" (
        !DOCKER_EXEC! --extract --async
    ) else if /i "!TASK!"=="transform" (
        !DOCKER_EXEC! --transform --async
    ) else if /i "!TASK!"=="load" (
        !DOCKER_EXEC! --load --async
    ) else (
        !DOCKER_EXEC! --async
    )
)
echo [OK] ETL pipeline task queued
exit /b 0

:celery_status
echo.
echo ========================================
echo Celery Status
echo ========================================
docker-compose -f %COMPOSE_FILE% exec -T web celery -A config inspect active
exit /b 0

:celery_purge
echo.
echo ========================================
echo Purging Celery Queue
echo ========================================
docker-compose -f %COMPOSE_FILE% exec -T web celery -A config purge -f
echo [OK] Queue purged
exit /b 0

:run_ml_scoring
echo.
echo ========================================
echo Running ML Rescoring
echo ========================================
set MODE=%2
set SYMBOL=%3
if "!MODE!"=="" set MODE=async

set DOCKER_EXEC=docker-compose -f %COMPOSE_FILE% exec -T web python manage.py run_ml_scoring

if /i "!MODE!"=="sync" (
    if /i "!SYMBOL!"=="" (
        !DOCKER_EXEC!
    ) else (
        !DOCKER_EXEC! --symbol !SYMBOL!
    )
) else (
    if /i "!SYMBOL!"=="" (
        !DOCKER_EXEC! --async
    ) else (
        !DOCKER_EXEC! --symbol !SYMBOL! --async
    )
)
echo [OK] ML rescoring task queued
exit /b 0

:run_ml_incremental
echo.
echo ========================================
echo Running Incremental ML Rescoring
echo ========================================
set MODE=%2
if "!MODE!"=="" set MODE=async

set DOCKER_EXEC=docker-compose -f %COMPOSE_FILE% exec -T web python manage.py run_ml_scoring --incremental

if /i "!MODE!"=="sync" (
    !DOCKER_EXEC!
) else (
    !DOCKER_EXEC! --async
)
echo [OK] Incremental ML rescoring task queued
exit /b 0

:clean
echo.
echo ========================================
echo Cleaning Up
echo ========================================
set /p CONFIRM="This will remove all containers and volumes. Continue (y/N)? "
if /i "!CONFIRM!"=="y" (
    docker-compose -f %COMPOSE_FILE% down -v
    echo [OK] Cleanup completed
) else (
    echo [*] Cleanup cancelled
)
exit /b 0

:show_help
echo.
echo Financial Intelligence Platform - Docker ^& ETL Orchestration
echo.
echo Usage: orchestrate.bat [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   build               Build Docker images
echo   start               Start all services
echo   stop                Stop all services
echo   restart             Restart all services
echo   status              Show service status
echo   logs [SERVICE]      View service logs (omit SERVICE for all)
echo.
echo   migrate             Run database migrations
echo   create-superuser    Create Django superuser
echo.
echo   run-etl [MODE] [TASK] [--with-scoring]
echo                       Run ETL pipeline
echo                       MODE: async (default) or sync
echo                       TASK: extract, transform, load (default: all)
echo                       --with-scoring: Run ML rescoring after load
echo.
echo   run-ml-scoring [MODE] [SYMBOL]
echo                       Run ML rescoring
echo                       MODE: async (default) or sync
echo                       SYMBOL: Score specific company (optional)
echo.
echo   run-ml-incremental [MODE]
echo                       Run incremental ML rescoring
echo                       MODE: async (default) or sync
echo.
echo   celery-status       Show Celery worker status
echo   celery-purge        Purge Celery task queue
echo.
echo   clean               Remove all containers and volumes
echo   help                Show this help message
echo.
echo Examples:
echo   orchestrate.bat start                     - Start all services
echo   orchestrate.bat logs web                  - View web service logs
echo   orchestrate.bat run-etl async             - Run ETL asynchronously
echo   orchestrate.bat run-etl async --with-scoring - ETL with ML scoring
echo   orchestrate.bat run-ml-scoring            - Full ML rescoring
echo   orchestrate.bat run-ml-scoring async INFY - Score specific company
echo   orchestrate.bat run-ml-incremental        - Incremental rescoring
echo   orchestrate.bat celery-status             - Check Celery workers
echo.
exit /b 0

endlocal
