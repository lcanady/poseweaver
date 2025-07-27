#!/bin/bash

# PoseWeaver PM2 Deployment Script
# This script handles deployment using PM2 instead of Docker

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="poseweaver"
BACKEND_DIR="./backend"
FRONTEND_DIR="./frontend"
LOG_DIR="./logs"
VENV_PATH="./.venv"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if PM2 is installed
check_pm2() {
    if ! command -v pm2 &> /dev/null; then
        print_error "PM2 is not installed. Please install it first:"
        echo "npm install -g pm2"
        exit 1
    fi
    print_success "PM2 is installed"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p $LOG_DIR
    print_success "Directories created"
}

# Function to setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "$VENV_PATH" ]; then
        print_status "Creating new virtual environment..."
        python3 -m venv $VENV_PATH
    fi
    
    # Activate virtual environment and install dependencies
    source $VENV_PATH/bin/activate
    print_status "Installing Python dependencies..."
    cd $BACKEND_DIR
    pip install -r requirements.txt
    cd ..
    deactivate
    
    print_success "Python environment setup complete"
}

# Function to setup Node.js environment
setup_node_env() {
    print_status "Setting up Node.js environment..."
    
    cd $FRONTEND_DIR
    print_status "Installing Node.js dependencies..."
    npm install
    
    print_status "Building frontend..."
    npm run build
    cd ..
    
    print_success "Node.js environment setup complete"
}

# Function to stop existing PM2 processes
stop_services() {
    print_status "Stopping existing services..."
    
    # Stop and delete existing processes
    pm2 stop $PROJECT_NAME-backend 2>/dev/null || true
    pm2 stop $PROJECT_NAME-frontend 2>/dev/null || true
    pm2 delete $PROJECT_NAME-backend 2>/dev/null || true
    pm2 delete $PROJECT_NAME-frontend 2>/dev/null || true
    
    print_success "Existing services stopped"
}

# Function to start services with PM2
start_services() {
    print_status "Starting services with PM2..."
    
    # Start using ecosystem config
    pm2 start ecosystem.config.js --env production
    
    # Save PM2 configuration
    pm2 save
    
    print_success "Services started with PM2"
}

# Function to show status
show_status() {
    print_status "Current PM2 status:"
    pm2 status
    echo ""
    print_status "Application URLs:"
    echo "Frontend: http://localhost:3000"
    echo "Backend API: http://localhost:5001"
    echo ""
    print_status "Logs:"
    echo "View logs: pm2 logs"
    echo "Backend logs: pm2 logs poseweaver-backend"
    echo "Frontend logs: pm2 logs poseweaver-frontend"
}

# Function to run health checks
health_check() {
    print_status "Running health checks..."
    
    # Wait a moment for services to start
    sleep 5
    
    # Check backend health
    if curl -f http://localhost:5001/health &>/dev/null; then
        print_success "Backend is healthy"
    else
        print_warning "Backend health check failed"
    fi
    
    # Check frontend (basic connectivity)
    if curl -f http://localhost:3000 &>/dev/null; then
        print_success "Frontend is responding"
    else
        print_warning "Frontend connectivity check failed"
    fi
}

# Main deployment function
deploy() {
    print_status "Starting PoseWeaver deployment with PM2..."
    echo "========================================"
    
    check_pm2
    create_directories
    stop_services
    setup_python_env
    setup_node_env
    start_services
    show_status
    health_check
    
    print_success "Deployment completed successfully!"
    echo ""
    print_status "Next steps:"
    echo "- Monitor logs: pm2 logs"
    echo "- Restart services: pm2 restart ecosystem.config.js"
    echo "- Stop services: pm2 stop all"
    echo "- View monitoring: pm2 monit"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "start")
        print_status "Starting services..."
        pm2 start ecosystem.config.js --env production
        pm2 save
        show_status
        ;;
    "stop")
        print_status "Stopping services..."
        pm2 stop all
        print_success "Services stopped"
        ;;
    "restart")
        print_status "Restarting services..."
        pm2 restart ecosystem.config.js --env production
        show_status
        ;;
    "status")
        show_status
        ;;
    "logs")
        pm2 logs
        ;;
    "health")
        health_check
        ;;
    "help")
        echo "PoseWeaver PM2 Deployment Script"
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  start    - Start services"
        echo "  stop     - Stop services"
        echo "  restart  - Restart services"
        echo "  status   - Show PM2 status"
        echo "  logs     - Show logs"
        echo "  health   - Run health checks"
        echo "  help     - Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac
