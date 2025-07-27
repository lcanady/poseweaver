#!/bin/bash

# Simple Stripe Environment Variable Checker
# This script checks if Stripe keys are properly loaded

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🔍 Checking Stripe Environment Variables"
echo "======================================="
echo ""

# Get current directory
CURRENT_DIR=$(pwd)
print_status "Current directory: $CURRENT_DIR"

# Step 1: Check if .env file exists
print_status "1. Checking for .env file..."

if [[ -f ".env" ]]; then
    print_success ".env file found"
    
    # Check Stripe keys in .env
    print_status "Checking Stripe keys in .env file:"
    
    if grep -q "STRIPE_SECRET_KEY=" .env; then
        STRIPE_SECRET=$(grep "STRIPE_SECRET_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [[ -n "$STRIPE_SECRET" ]] && [[ "$STRIPE_SECRET" != "sk_test_your_stripe_secret_key_here" ]]; then
            print_success "✓ STRIPE_SECRET_KEY is set"
            echo "  Preview: ${STRIPE_SECRET:0:15}..."
        else
            print_error "✗ STRIPE_SECRET_KEY is empty or using placeholder"
        fi
    else
        print_error "✗ STRIPE_SECRET_KEY not found in .env"
    fi
    
    if grep -q "STRIPE_PUBLISHABLE_KEY=" .env; then
        STRIPE_PUB=$(grep "STRIPE_PUBLISHABLE_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [[ -n "$STRIPE_PUB" ]] && [[ "$STRIPE_PUB" != "pk_test_your_stripe_publishable_key_here" ]]; then
            print_success "✓ STRIPE_PUBLISHABLE_KEY is set"
            echo "  Preview: ${STRIPE_PUB:0:15}..."
        else
            print_error "✗ STRIPE_PUBLISHABLE_KEY is empty or using placeholder"
        fi
    else
        print_error "✗ STRIPE_PUBLISHABLE_KEY not found in .env"
    fi
    
    if grep -q "STRIPE_WEBHOOK_SECRET=" .env; then
        STRIPE_WEBHOOK=$(grep "STRIPE_WEBHOOK_SECRET=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [[ -n "$STRIPE_WEBHOOK" ]] && [[ "$STRIPE_WEBHOOK" != "whsec_your_webhook_secret_here" ]]; then
            print_success "✓ STRIPE_WEBHOOK_SECRET is set"
            echo "  Preview: ${STRIPE_WEBHOOK:0:15}..."
        else
            print_error "✗ STRIPE_WEBHOOK_SECRET is empty or using placeholder"
        fi
    else
        print_error "✗ STRIPE_WEBHOOK_SECRET not found in .env"
    fi
    
else
    print_error ".env file not found!"
    
    if [[ -f ".env.example" ]]; then
        print_status "Creating .env from .env.example..."
        cp .env.example .env
        print_success ".env file created"
        print_warning "You need to edit .env and add your real Stripe keys"
    else
        print_error ".env.example not found either"
        print_status "Creating basic .env file..."
        cat > .env << 'EOF'
# Stripe Configuration - REPLACE WITH YOUR REAL KEYS
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Database
MONGODB_URI=mongodb://admin:password@localhost:27017/mush_pose_editor?authSource=admin

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
EOF
        print_success "Basic .env file created"
        print_warning "You MUST edit .env and add your real Stripe keys!"
    fi
fi

# Step 2: Check ecosystem.config.js
print_status "2. Checking ecosystem.config.js..."

if [[ -f "ecosystem.config.js" ]]; then
    if grep -q "STRIPE_SECRET_KEY" ecosystem.config.js; then
        print_success "✓ STRIPE_SECRET_KEY reference found in ecosystem.config.js"
    else
        print_error "✗ STRIPE_SECRET_KEY not found in ecosystem.config.js"
        print_warning "You need to add Stripe environment variables to ecosystem.config.js"
    fi
else
    print_error "ecosystem.config.js not found"
fi

# Step 3: Test environment loading
print_status "3. Testing environment variable loading..."

# Load .env file and test
if [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
    
    if [[ -n "$STRIPE_SECRET_KEY" ]] && [[ "$STRIPE_SECRET_KEY" != "sk_test_your_stripe_secret_key_here" ]]; then
        print_success "✓ STRIPE_SECRET_KEY can be loaded from .env"
    else
        print_error "✗ STRIPE_SECRET_KEY cannot be loaded or is placeholder"
    fi
fi

# Step 4: Check PM2 process
print_status "4. Checking PM2 backend process..."

if command -v pm2 &> /dev/null; then
    if pm2 list | grep -q "poseweaver-backend"; then
        print_status "PM2 backend process found, checking environment..."
        
        # Get PM2 process info
        pm2 show poseweaver-backend > /tmp/pm2_info.txt 2>/dev/null || true
        
        if [[ -f /tmp/pm2_info.txt ]]; then
            if grep -q "STRIPE_SECRET_KEY" /tmp/pm2_info.txt; then
                print_success "✓ STRIPE_SECRET_KEY is loaded in PM2 process"
            else
                print_error "✗ STRIPE_SECRET_KEY is NOT loaded in PM2 process"
                print_warning "PM2 is not loading the environment variables properly"
            fi
        fi
        
        rm -f /tmp/pm2_info.txt
    else
        print_warning "PM2 backend process not found or not running"
    fi
else
    print_warning "PM2 not found"
fi

# Step 5: Provide fix instructions
echo ""
print_status "🔧 Fix Instructions:"
echo "==================="

if [[ ! -f ".env" ]] || ! grep -q "STRIPE_SECRET_KEY=sk_" .env; then
    echo ""
    print_error "1. Add your real Stripe keys to .env file:"
    echo "   nano .env"
    echo ""
    echo "   Add these lines with your REAL keys:"
    echo "   STRIPE_SECRET_KEY=sk_test_your_actual_secret_key"
    echo "   STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key"
    echo "   STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret"
    echo ""
fi

if ! grep -q "STRIPE_SECRET_KEY" ecosystem.config.js 2>/dev/null; then
    echo ""
    print_error "2. Update ecosystem.config.js backend env section:"
    echo "   Add these lines to the backend env object:"
    echo "   STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,"
    echo "   STRIPE_PUBLISHABLE_KEY: process.env.STRIPE_PUBLISHABLE_KEY,"
    echo "   STRIPE_WEBHOOK_SECRET: process.env.STRIPE_WEBHOOK_SECRET,"
    echo ""
fi

echo ""
print_status "3. Restart PM2 after making changes:"
echo "   pm2 restart ecosystem.config.js --env production"
echo "   pm2 save"
echo ""

print_status "4. Test the fix:"
echo "   pm2 logs poseweaver-backend --lines 10"
echo "   curl -X GET http://localhost:5001/api/purchase/webhook/test"
echo ""

print_status "🔗 Get your Stripe keys from:"
echo "   API Keys: https://dashboard.stripe.com/apikeys"
echo "   Webhooks: https://dashboard.stripe.com/webhooks"

print_success "Stripe environment check completed!"
