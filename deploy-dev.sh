#!/bin/bash

# PoseWeaver Development PM2 Script
# Quick script for development deployment with PM2

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Create logs directory
mkdir -p ./logs

print_status "Starting PoseWeaver in development mode with PM2..."

# Stop existing processes
pm2 stop poseweaver-backend poseweaver-frontend 2>/dev/null || true
pm2 delete poseweaver-backend poseweaver-frontend 2>/dev/null || true

# Start in development mode
pm2 start ecosystem.config.js --env development

# Save configuration
pm2 save

print_success "Development servers started!"
echo ""
print_status "URLs:"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:5001"
echo ""
print_status "Commands:"
echo "View logs: pm2 logs"
echo "Stop: pm2 stop all"
echo "Restart: pm2 restart all"
echo "Monitor: pm2 monit"
