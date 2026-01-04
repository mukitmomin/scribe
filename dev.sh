#!/usr/bin/env bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
VENV_DIR="services/backend/venv"
BACKEND_DIR="services/backend"
FRONTEND_DIR="apps/web"

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Scribe Development Environment${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

setup_env_files() {
    print_info "Checking environment files..."

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warn ".env not found. Copying from .env.example..."
            cp .env.example .env
            print_warn "Please edit .env and add your GOOGLE_API_KEY"
        else
            print_warn "No .env or .env.example found. You may need to configure environment variables manually."
        fi
    fi
}

start_docker() {
    print_header
    print_info "Starting development environment with Docker Compose..."

    setup_env_files

    if ! check_command docker; then
        print_error "Docker is not installed. Please install Docker Desktop."
        exit 1
    fi

    if ! check_command docker-compose && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi

    print_info "Building and starting containers..."

    # Use docker compose or docker-compose depending on what's available
    if docker compose version &> /dev/null; then
        docker compose up --build
    else
        docker-compose up --build
    fi
}

start_local() {
    print_header
    print_info "Starting development environment locally..."

    # Check prerequisites
    print_info "Checking prerequisites..."

    local missing_deps=false

    if ! check_command node; then
        print_error "Node.js is not installed (required: >=20)"
        missing_deps=true
    fi

    if ! check_command pnpm; then
        print_error "pnpm is not installed (required: >=9)"
        print_info "Install with: npm install -g pnpm"
        missing_deps=true
    fi

    if ! check_command python3; then
        print_error "Python 3 is not installed (required: >=3.11)"
        missing_deps=true
    fi

    if [ "$missing_deps" = true ]; then
        exit 1
    fi

    setup_env_files

    # Setup Python virtual environment
    print_info "Setting up Python virtual environment..."
    if [ ! -d "$VENV_DIR" ]; then
        print_info "Creating virtual environment at $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
    fi

    # Install Python dependencies
    print_info "Installing Python dependencies..."
    source "$VENV_DIR/bin/activate"
    cd "$BACKEND_DIR"
    pip install -q --upgrade pip
    pip install -q -e ".[dev]"
    cd "$SCRIPT_DIR"

    # Install Node dependencies
    print_info "Installing Node.js dependencies..."
    pnpm install

    # Build shared packages
    print_info "Building shared packages..."
    if [ -d "packages/types" ]; then
        pnpm --filter @scribe/types build
    fi
    if [ -d "packages/ui" ]; then
        pnpm --filter @scribe/ui build
    fi

    # Start database with Docker
    print_info "Starting PostgreSQL database..."
    if docker compose version &> /dev/null; then
        docker compose up -d db
    else
        docker-compose up -d db
    fi

    # Wait for database to be ready
    print_info "Waiting for database to be ready..."
    sleep 5

    # Create log directory
    mkdir -p logs

    # Start backend
    print_info "Starting backend server..."
    cd "$BACKEND_DIR"
    source venv/bin/activate
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../../logs/backend.pid
    cd "$SCRIPT_DIR"

    # Start frontend
    print_info "Starting frontend server..."
    cd "$FRONTEND_DIR"
    nohup pnpm dev > ../../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../../logs/frontend.pid
    cd "$SCRIPT_DIR"

    echo ""
    print_info "Development servers started!"
    echo ""
    echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
    echo -e "${GREEN}Backend:${NC}  http://localhost:8000"
    echo -e "${GREEN}API Docs:${NC} http://localhost:8000/docs"
    echo ""
    echo -e "${YELLOW}Logs:${NC}"
    echo -e "  Backend:  tail -f logs/backend.log"
    echo -e "  Frontend: tail -f logs/frontend.log"
    echo ""
    echo -e "${YELLOW}To stop:${NC} ./dev.sh stop"
    echo ""
}

stop_local() {
    print_info "Stopping local development servers..."

    if [ -f "logs/backend.pid" ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            print_info "Stopping backend (PID: $BACKEND_PID)..."
            kill $BACKEND_PID
        fi
        rm logs/backend.pid
    fi

    if [ -f "logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat logs/frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            print_info "Stopping frontend (PID: $FRONTEND_PID)..."
            kill $FRONTEND_PID
        fi
        rm logs/frontend.pid
    fi

    # Stop database
    print_info "Stopping database..."
    if docker compose version &> /dev/null; then
        docker compose stop db
    else
        docker-compose stop db
    fi

    print_info "All services stopped."
}

stop_docker() {
    print_info "Stopping Docker Compose services..."

    if docker compose version &> /dev/null; then
        docker compose down
    else
        docker-compose down
    fi

    print_info "All services stopped."
}

show_help() {
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start          Start local development (default)"
    echo "  docker         Start with Docker Compose"
    echo "  stop           Stop local development servers"
    echo "  stop-docker    Stop Docker Compose services"
    echo "  clean          Clean up virtual env and node_modules"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./dev.sh              # Start local development"
    echo "  ./dev.sh docker       # Start with Docker"
    echo "  ./dev.sh stop         # Stop local servers"
}

clean_env() {
    print_info "Cleaning development environment..."

    # Stop services first
    stop_local 2>/dev/null || true

    # Remove Python venv
    if [ -d "$VENV_DIR" ]; then
        print_info "Removing Python virtual environment..."
        rm -rf "$VENV_DIR"
    fi

    # Remove node_modules
    print_info "Removing node_modules..."
    find . -name "node_modules" -type d -prune -exec rm -rf '{}' +

    # Remove logs
    if [ -d "logs" ]; then
        print_info "Removing logs..."
        rm -rf logs
    fi

    print_info "Clean complete!"
}

# Main script logic
case "${1:-start}" in
    start)
        start_local
        ;;
    docker)
        start_docker
        ;;
    stop)
        stop_local
        ;;
    stop-docker)
        stop_docker
        ;;
    clean)
        clean_env
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
