#!/bin/bash

# Financial Intelligence Platform - Docker & ETL Orchestration Script
# This script manages Docker containers, Celery tasks, and ETL pipeline execution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="fintech"
COMPOSE_FILE="docker-compose.yml"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_step() {
    echo -e "${BLUE}→ $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    print_success "Docker is running"
}

# Setup environment
setup_env() {
    print_step "Setting up environment..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "Created .env from .env.example"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_success ".env already exists"
    fi
    
    # Ensure data directories exist
    mkdir -p data/raw data/clean logs
    print_success "Created data and logs directories"
}

# Build images
build() {
    print_header "Building Docker Images"
    docker-compose -f $COMPOSE_FILE build
    print_success "Images built successfully"
}

# Start services
start() {
    print_header "Starting Services"
    
    setup_env
    
    print_step "Starting database..."
    docker-compose -f $COMPOSE_FILE up -d db
    sleep 5
    
    print_step "Starting Redis..."
    docker-compose -f $COMPOSE_FILE up -d redis
    sleep 3
    
    print_step "Starting web application..."
    docker-compose -f $COMPOSE_FILE up -d web
    
    print_step "Starting Celery worker..."
    docker-compose -f $COMPOSE_FILE up -d celery_worker
    
    print_step "Starting Celery beat scheduler..."
    docker-compose -f $COMPOSE_FILE up -d celery_beat
    
    print_success "All services started"
    print_info "Web application: http://localhost:8000"
    print_info "Redis: localhost:6379"
    print_info "PostgreSQL: localhost:5432"
}

# Stop services
stop() {
    print_header "Stopping Services"
    docker-compose -f $COMPOSE_FILE down
    print_success "All services stopped"
}

# Restart services
restart() {
    print_header "Restarting Services"
    stop
    sleep 2
    start
}

# View logs
logs() {
    SERVICE=$1
    if [ -z "$SERVICE" ]; then
        print_info "Showing all logs (Ctrl+C to exit)"
        docker-compose -f $COMPOSE_FILE logs -f
    else
        print_info "Showing logs for: $SERVICE"
        docker-compose -f $COMPOSE_FILE logs -f $SERVICE
    fi
}

# Run ETL pipeline
run_etl() {
    print_header "Running ETL Pipeline"
    
    MODE=${1:-async}
    TASK=${2:-}
    WITH_SCORING=${3:-}
    
    DOCKER_EXEC="docker-compose -f $COMPOSE_FILE exec -T web python manage.py run_etl"
    
    if [ "$MODE" = "sync" ]; then
        print_step "Running ETL in synchronous mode..."
        if [ "$WITH_SCORING" = "--with-scoring" ]; then
            $DOCKER_EXEC $WITH_SCORING
        else
            $DOCKER_EXEC
        fi
    else
        print_step "Running ETL in asynchronous mode..."
        if [ ! -z "$TASK" ]; then
            if [ "$TASK" = "extract" ]; then
                $DOCKER_EXEC --extract --async
            elif [ "$TASK" = "transform" ]; then
                $DOCKER_EXEC --transform --async
            elif [ "$TASK" = "load" ]; then
                if [ "$WITH_SCORING" = "--with-scoring" ]; then
                    $DOCKER_EXEC --load --async $WITH_SCORING
                else
                    $DOCKER_EXEC --load --async
                fi
            else
                print_error "Unknown task: $TASK"
                exit 1
            fi
        else
            if [ "$WITH_SCORING" = "--with-scoring" ]; then
                $DOCKER_EXEC --async $WITH_SCORING
            else
                $DOCKER_EXEC --async
            fi
        fi
    fi
    
    print_success "ETL pipeline task queued"
}

# Check service status
status() {
    print_header "Service Status"
    docker-compose -f $COMPOSE_FILE ps
}

# Run migrations
migrate() {
    print_header "Running Database Migrations"
    docker-compose -f $COMPOSE_FILE exec -T web python manage.py migrate
    print_success "Migrations completed"
}

# Create superuser
create_superuser() {
    print_header "Creating Superuser"
    docker-compose -f $COMPOSE_FILE exec web python manage.py createsuperuser
}

# Clean up volumes and data
clean() {
    print_header "Cleaning Up"
    read -p "This will remove all containers and volumes. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f $COMPOSE_FILE down -v
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Show Celery worker status
celery_status() {
    print_header "Celery Status"
    docker-compose -f $COMPOSE_FILE exec -T web celery -A config inspect active
}

# Purge Celery queue
celery_purge() {
    print_header "Purging Celery Queue"
    docker-compose -f $COMPOSE_FILE exec -T web celery -A config purge -f
    print_success "Queue purged"
}

# Run ML rescoring
run_ml_scoring() {
    print_header "Running ML Rescoring"
    
    MODE=${1:-async}
    SYMBOL=${2:-}
    
    DOCKER_EXEC="docker-compose -f $COMPOSE_FILE exec -T web python manage.py run_ml_scoring"
    
    if [ "$MODE" = "sync" ]; then
        print_step "Running ML rescoring in synchronous mode..."
        if [ ! -z "$SYMBOL" ]; then
            $DOCKER_EXEC --symbol $SYMBOL
        else
            $DOCKER_EXEC
        fi
    else
        print_step "Running ML rescoring in asynchronous mode..."
        if [ ! -z "$SYMBOL" ]; then
            $DOCKER_EXEC --symbol $SYMBOL --async
        else
            $DOCKER_EXEC --async
        fi
    fi
    
    print_success "ML rescoring task queued"
}

# Run ML incremental rescoring
run_ml_incremental() {
    print_header "Running Incremental ML Rescoring"
    
    MODE=${1:-async}
    
    DOCKER_EXEC="docker-compose -f $COMPOSE_FILE exec -T web python manage.py run_ml_scoring --incremental"
    
    if [ "$MODE" = "sync" ]; then
        $DOCKER_EXEC
    else
        $DOCKER_EXEC --async
    fi
    
    print_success "Incremental ML rescoring task queued"
}

# Help message
show_help() {
    cat << EOF
${BLUE}Financial Intelligence Platform - Docker & ETL Orchestration${NC}

Usage: ./orchestrate.sh [COMMAND] [OPTIONS]

Commands:
    build               Build Docker images
    start               Start all services
    stop                Stop all services
    restart             Restart all services
    status              Show service status
    logs [SERVICE]      View service logs (omit SERVICE for all)
    
    migrate             Run database migrations
    create-superuser    Create Django superuser
    
    run-etl [MODE] [TASK] [--with-scoring]
                        Run ETL pipeline
                        MODE: async (default) or sync
                        TASK: extract, transform, load (default: all)
                        --with-scoring: Run ML rescoring after load
    
    run-ml-scoring [MODE] [SYMBOL]
                        Run ML rescoring
                        MODE: async (default) or sync
                        SYMBOL: Score specific company (optional, default: all)
    
    run-ml-incremental [MODE]
                        Run incremental ML rescoring
                        MODE: async (default) or sync
    
    celery-status       Show Celery worker status
    celery-purge        Purge Celery task queue
    
    clean               Remove all containers and volumes
    
    help                Show this help message

Examples:
    ./orchestrate.sh start                           # Start all services
    ./orchestrate.sh logs celery_worker              # View Celery logs
    ./orchestrate.sh run-etl async                   # Run ETL async
    ./orchestrate.sh run-etl async --with-scoring    # ETL + ML scoring
    ./orchestrate.sh run-ml-scoring                  # Full batch rescoring
    ./orchestrate.sh run-ml-scoring async INFY       # Score specific company
    ./orchestrate.sh run-ml-incremental              # Update changed companies
    ./orchestrate.sh celery-status                   # Check workers

${NC}
EOF
}

# Main command handler
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build
            ;;
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        status)
            status
            ;;
        logs)
            logs $2
            ;;
        migrate)
            migrate
            ;;
        create-superuser)
            create_superuser
            ;;
        run-etl)
            run_etl $2 $3 $4
            ;;
        celery-status)
            celery_status
            ;;
        celery-purge)
            celery_purge
            ;;
        run-ml-scoring)
            run_ml_scoring $2 $3
            ;;
        run-ml-incremental)
            run_ml_incremental $2
            ;;
        clean)
            clean
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
