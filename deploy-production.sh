#!/bin/bash

# PoseWeaver Production Deployment Script
# This script builds and deploys the entire PoseWeaver application using Docker

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 PoseWeaver Production Deployment${NC}"
echo -e "${CYAN}Building and deploying with Docker...${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${YELLOW}📋 $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is running
check_docker() {
    print_status "Checking Docker..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if environment file exists
check_environment() {
    print_status "Checking environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.production" ]; then
            print_info "Copying .env.production to .env"
            cp .env.production .env
        else
            print_error "No .env file found. Please create one from .env.production template"
            exit 1
        fi
    fi
    
    if [ ! -f "backend/.env" ]; then
        print_error "No backend/.env file found. Please create one with your API keys"
        print_info "Required variables: VENICE_API_KEY, MONGODB_URI, STRIPE_SECRET_KEY, etc."
        exit 1
    fi
    
    print_success "Environment configuration found"
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    
    print_info "Building backend image..."
    docker build -t poseweaver-backend:latest ./backend
    
    print_info "Building frontend image..."
    docker build -t poseweaver-frontend:latest ./frontend
    
    print_success "Docker images built successfully"
}

# Deploy with docker-compose
deploy_containers() {
    print_status "Deploying containers..."
    
    # Stop existing containers
    print_info "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down || true
    
    # Start new containers
    print_info "Starting new containers..."
    docker-compose -f docker-compose.prod.yml up -d
    
    print_success "Containers deployed"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for backend
    print_info "Waiting for backend..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f -s http://localhost/api/health > /dev/null 2>&1; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Backend failed to start within 60 seconds"
        docker-compose -f docker-compose.prod.yml logs backend
        exit 1
    fi
    
    # Wait for frontend
    print_info "Waiting for frontend..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f -s http://localhost > /dev/null 2>&1; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Frontend failed to start within 60 seconds"
        docker-compose -f docker-compose.prod.yml logs frontend
        exit 1
    fi
    
    print_success "All services are ready"
}

# Run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Check backend API
    if curl -f -s http://localhost/api/health > /dev/null; then
        print_success "✅ Backend API is healthy"
    else
        print_error "❌ Backend API health check failed"
    fi
    
    # Check frontend
    if curl -f -s http://localhost > /dev/null; then
        print_success "✅ Frontend is healthy"
    else
        print_error "❌ Frontend health check failed"
    fi
    
    # Check database connection
    if docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
        print_success "✅ Database is healthy"
    else
        print_error "❌ Database health check failed"
    fi
}

# Display deployment summary
display_summary() {
    echo ""
    echo -e "${PURPLE}🎉 Deployment Complete!${NC}"
    echo -e "${GREEN}========================${NC}"
    echo ""
    echo -e "${CYAN}🌐 Your PoseWeaver application is running at:${NC}"
    echo -e "  Frontend: http://localhost"
    echo -e "  Backend API: http://localhost/api/"
    echo -e "  Health Check: http://localhost/health"
    echo ""
    echo -e "${CYAN}🔧 Management Commands:${NC}"
    echo -e "  View logs: docker-compose -f docker-compose.prod.yml logs"
    echo -e "  Stop: docker-compose -f docker-compose.prod.yml down"
    echo -e "  Restart: docker-compose -f docker-compose.prod.yml restart"
    echo -e "  Status: docker-compose -f docker-compose.prod.yml ps"
    echo ""
    echo -e "${CYAN}📊 Container Status:${NC}"
    docker-compose -f docker-compose.prod.yml ps
    echo ""
    echo -e "${YELLOW}⚠️  Next Steps:${NC}"
    echo -e "  1. Configure your domain DNS to point to this server"
    echo -e "  2. Set up SSL certificates for HTTPS"
    echo -e "  3. Update FRONTEND_URL and NEXT_PUBLIC_API_URL in .env"
    echo -e "  4. Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo ""
    echo -e "${GREEN}🚀 Your PoseWeaver application is ready for production!${NC}"
}

# Cleanup function
cleanup() {
    print_error "Deployment interrupted. Cleaning up..."
    docker-compose -f docker-compose.prod.yml down || true
    exit 1
}

# Main deployment flow
main() {
    echo -e "${PURPLE}Starting production deployment...${NC}"
    echo ""
    
    check_docker
    check_environment
    build_images
    deploy_containers
    wait_for_services
    run_health_checks
    display_summary
}

# Handle script interruption
trap cleanup INT TERM

# Run main function
main "$@"
