#!/bin/bash

# PoseWeaver Full Project Deployment Script
# This script deploys both backend (VPS) and frontend (Vercel) in one unified process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
VPS_IP=""
VPS_USER="root"
DOMAIN=""
REPO_URL="https://github.com/lcanady/poseweaver.git"

echo -e "${PURPLE}🚀 PoseWeaver Full Project Deployment${NC}"
echo -e "${CYAN}This script will deploy both backend and frontend${NC}"
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

# Function to prompt for input
prompt_input() {
    local prompt="$1"
    local var_name="$2"
    local default_value="$3"
    
    if [ -n "$default_value" ]; then
        read -p "$(echo -e "${CYAN}$prompt [$default_value]: ${NC}")" input
        eval "$var_name=\"\${input:-$default_value}\""
    else
        read -p "$(echo -e "${CYAN}$prompt: ${NC}")" input
        eval "$var_name=\"$input\""
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install git first."
        exit 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository. Please run this from your project root."
        exit 1
    fi
    
    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        print_info "Vercel CLI not found. Installing..."
        npm install -g vercel
    fi
    
    # Check if SSH is available
    if ! command -v ssh &> /dev/null; then
        print_error "SSH is not available. Please install SSH client."
        exit 1
    fi
    
    print_success "Prerequisites check completed"
}

# Function to gather deployment information
gather_deployment_info() {
    print_status "Gathering deployment information..."
    echo ""
    
    prompt_input "Enter your VPS IP address" "VPS_IP"
    prompt_input "Enter your domain name (e.g., api.poseweaver.com)" "DOMAIN"
    prompt_input "Enter VPS SSH user" "VPS_USER" "root"
    
    echo ""
    print_info "Deployment Configuration:"
    print_info "VPS IP: $VPS_IP"
    print_info "Domain: $DOMAIN"
    print_info "SSH User: $VPS_USER"
    print_info "Repository: $REPO_URL"
    echo ""
    
    read -p "$(echo -e "${CYAN}Continue with deployment? (y/N): ${NC}")" confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled."
        exit 0
    fi
}

# Function to test VPS connection
test_vps_connection() {
    print_status "Testing VPS connection..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$VPS_USER@$VPS_IP" exit 2>/dev/null; then
        print_success "VPS connection successful"
    else
        print_error "Cannot connect to VPS. Please check:"
        print_error "1. VPS IP address is correct"
        print_error "2. SSH keys are set up"
        print_error "3. VPS is running and accessible"
        exit 1
    fi
}

# Function to prepare local repository
prepare_repository() {
    print_status "Preparing local repository..."
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_info "You have uncommitted changes. Committing them..."
        git add .
        git commit -m "Auto-commit before deployment $(date)"
    fi
    
    # Push to remote
    print_info "Pushing latest changes to repository..."
    git push origin main
    
    print_success "Repository prepared"
}

# Function to deploy backend to VPS
deploy_backend() {
    print_status "Deploying backend to VPS..."
    
    # Create deployment script on VPS
    print_info "Creating deployment script on VPS..."
    ssh "$VPS_USER@$VPS_IP" << EOF
        # Download deployment script
        curl -o deploy_vps.sh https://raw.githubusercontent.com/lcanady/poseweaver/main/backend/deploy_vps.sh
        chmod +x deploy_vps.sh
        
        # Update configuration in script
        sed -i "s|REPO_URL=\".*\"|REPO_URL=\"$REPO_URL\"|g" deploy_vps.sh
        sed -i "s|DOMAIN=\".*\"|DOMAIN=\"$DOMAIN\"|g" deploy_vps.sh
EOF
    
    print_info "Running deployment script on VPS..."
    ssh "$VPS_USER@$VPS_IP" << EOF
        ./deploy_vps.sh
EOF
    
    print_success "Backend deployment script completed"
    
    # Configure environment variables
    print_status "Configuring backend environment variables..."
    print_info "You'll need to manually configure the .env file on the VPS"
    print_info "SSH into your VPS and edit: /home/poseweaver/poseweaver/backend/.env"
    
    read -p "$(echo -e "${CYAN}Press Enter after you've configured the .env file on the VPS...${NC}")"
    
    # Restart backend service
    print_info "Restarting backend service..."
    ssh "$VPS_USER@$VPS_IP" << EOF
        supervisorctl restart poseweaver
        sleep 5
        supervisorctl status poseweaver
EOF
    
    print_success "Backend deployed successfully"
}

# Function to test backend deployment
test_backend() {
    print_status "Testing backend deployment..."
    
    # Test API health endpoint
    if curl -f -s "http://$DOMAIN/api/health" > /dev/null; then
        print_success "Backend API is responding"
    else
        print_error "Backend API is not responding. Check VPS logs:"
        print_error "ssh $VPS_USER@$VPS_IP 'tail -f /var/log/poseweaver.log'"
        exit 1
    fi
    
    # Test WebSocket endpoint
    print_info "WebSocket endpoint available at: wss://$DOMAIN/socket.io/"
}

# Function to deploy frontend to Vercel
deploy_frontend() {
    print_status "Deploying frontend to Vercel..."
    
    # Navigate to frontend directory
    cd frontend
    
    # Update environment variables for production
    print_info "Configuring frontend environment variables..."
    
    # Set production API URL
    if [[ "$DOMAIN" == *"."* ]]; then
        API_URL="https://$DOMAIN"
    else
        API_URL="http://$VPS_IP"
    fi
    
    # Deploy to Vercel
    print_info "Deploying to Vercel..."
    vercel --prod --env NEXT_PUBLIC_API_URL="$API_URL"
    
    # Go back to project root
    cd ..
    
    print_success "Frontend deployed to Vercel"
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    print_status "Running post-deployment tests..."
    
    # Test backend health
    print_info "Testing backend health..."
    if curl -f -s "http://$DOMAIN/api/health" > /dev/null; then
        print_success "✅ Backend API health check passed"
    else
        print_error "❌ Backend API health check failed"
    fi
    
    # Test CORS
    print_info "Testing CORS configuration..."
    CORS_TEST=$(curl -s -H "Origin: https://poseweaver.com" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: X-Requested-With" -X OPTIONS "http://$DOMAIN/api/health" -w "%{http_code}")
    if [[ "$CORS_TEST" == *"200"* ]] || [[ "$CORS_TEST" == *"204"* ]]; then
        print_success "✅ CORS configuration working"
    else
        print_error "❌ CORS configuration may need adjustment"
    fi
    
    print_success "Post-deployment tests completed"
}

# Function to display deployment summary
display_summary() {
    echo ""
    echo -e "${PURPLE}🎉 Deployment Summary${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "${CYAN}Backend (VPS):${NC}"
    echo -e "  API URL: http://$DOMAIN"
    echo -e "  WebSocket: ws://$DOMAIN/socket.io/"
    echo -e "  Health Check: http://$DOMAIN/api/health"
    echo ""
    echo -e "${CYAN}Frontend (Vercel):${NC}"
    echo -e "  URL: https://poseweaver.com"
    echo -e "  API Endpoint: $API_URL"
    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo -e "  1. Test the application end-to-end"
    echo -e "  2. Set up SSL certificate: ssh $VPS_USER@$VPS_IP 'certbot --nginx -d $DOMAIN'"
    echo -e "  3. Configure monitoring and backups"
    echo -e "  4. Update DNS if using a custom domain"
    echo ""
    echo -e "${CYAN}Useful Commands:${NC}"
    echo -e "  Backend logs: ssh $VPS_USER@$VPS_IP 'tail -f /var/log/poseweaver.log'"
    echo -e "  Restart backend: ssh $VPS_USER@$VPS_IP 'supervisorctl restart poseweaver'"
    echo -e "  Update backend: ssh $VPS_USER@$VPS_IP '/home/poseweaver/poseweaver/update.sh'"
    echo ""
    echo -e "${GREEN}🚀 Deployment completed successfully!${NC}"
}

# Main deployment flow
main() {
    echo -e "${PURPLE}Starting full project deployment...${NC}"
    echo ""
    
    check_prerequisites
    gather_deployment_info
    test_vps_connection
    prepare_repository
    deploy_backend
    test_backend
    deploy_frontend
    run_post_deployment_tests
    display_summary
}

# Handle script interruption
trap 'print_error "Deployment interrupted. You may need to clean up manually."; exit 1' INT TERM

# Run main function
main "$@"
