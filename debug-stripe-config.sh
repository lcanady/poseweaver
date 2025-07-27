#!/bin/bash

# Debug Stripe Configuration Issues
# This script checks and fixes Stripe environment variable configuration

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

echo "🔍 Debugging Stripe Configuration Issues"
echo "========================================"
echo ""

cd /root/poseweaver

# Step 1: Check if .env file exists
print_status "1. Checking .env file..."

if [[ -f ".env" ]]; then
    print_success ".env file found"
    
    # Check Stripe environment variables
    print_status "Checking Stripe environment variables in .env..."
    
    if grep -q "STRIPE_SECRET_KEY=" .env; then
        STRIPE_SECRET=$(grep "STRIPE_SECRET_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [[ "$STRIPE_SECRET" == "sk_test_your_stripe_secret_key_here" ]] || [[ -z "$STRIPE_SECRET" ]]; then
            print_error "STRIPE_SECRET_KEY is not configured (using placeholder)"
        else
            print_success "STRIPE_SECRET_KEY is configured"
            echo "  Preview: ${STRIPE_SECRET:0:12}..."
        fi
    else
        print_error "STRIPE_SECRET_KEY not found in .env"
    fi
    
    if grep -q "STRIPE_PUBLISHABLE_KEY=" .env; then
        STRIPE_PUB=$(grep "STRIPE_PUBLISHABLE_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [[ "$STRIPE_PUB" == "pk_test_your_stripe_publishable_key_here" ]] || [[ -z "$STRIPE_PUB" ]]; then
            print_error "STRIPE_PUBLISHABLE_KEY is not configured (using placeholder)"
        else
            print_success "STRIPE_PUBLISHABLE_KEY is configured"
            echo "  Preview: ${STRIPE_PUB:0:12}..."
        fi
    else
        print_error "STRIPE_PUBLISHABLE_KEY not found in .env"
    fi
    
    if grep -q "STRIPE_WEBHOOK_SECRET=" .env; then
        STRIPE_WEBHOOK=$(grep "STRIPE_WEBHOOK_SECRET=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [[ "$STRIPE_WEBHOOK" == "whsec_your_webhook_secret_here" ]] || [[ -z "$STRIPE_WEBHOOK" ]]; then
            print_error "STRIPE_WEBHOOK_SECRET is not configured (using placeholder)"
        else
            print_success "STRIPE_WEBHOOK_SECRET is configured"
            echo "  Preview: ${STRIPE_WEBHOOK:0:12}..."
        fi
    else
        print_error "STRIPE_WEBHOOK_SECRET not found in .env"
    fi
    
else
    print_error ".env file not found!"
    print_status "Creating .env file from .env.example..."
    
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        print_success ".env file created from template"
    else
        print_error ".env.example file not found"
        exit 1
    fi
fi

# Step 2: Check ecosystem.config.js environment variables
print_status "2. Checking PM2 ecosystem environment variables..."

if grep -q "STRIPE_SECRET_KEY" ecosystem.config.js; then
    print_success "STRIPE_SECRET_KEY found in ecosystem.config.js"
else
    print_warning "STRIPE_SECRET_KEY not found in ecosystem.config.js"
fi

# Step 3: Check current PM2 environment
print_status "3. Checking current PM2 environment..."

pm2 show poseweaver-backend > /tmp/pm2_backend_info.txt 2>/dev/null || true

if [[ -f /tmp/pm2_backend_info.txt ]]; then
    if grep -q "STRIPE_SECRET_KEY" /tmp/pm2_backend_info.txt; then
        print_success "STRIPE_SECRET_KEY is loaded in PM2 backend process"
    else
        print_error "STRIPE_SECRET_KEY is NOT loaded in PM2 backend process"
    fi
else
    print_warning "Could not get PM2 backend process info"
fi

# Step 4: Test Stripe configuration
print_status "4. Testing Stripe configuration..."

cd backend

# Create a simple test script
cat > /tmp/test_stripe.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
sys.path.append('/root/poseweaver/backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/root/poseweaver/.env')

import stripe

def test_stripe_config():
    print("Testing Stripe configuration...")
    
    # Check environment variables
    stripe_secret = os.getenv('STRIPE_SECRET_KEY')
    stripe_pub = os.getenv('STRIPE_PUBLISHABLE_KEY')
    stripe_webhook = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    print(f"STRIPE_SECRET_KEY: {'✓ Set' if stripe_secret and stripe_secret != 'sk_test_your_stripe_secret_key_here' else '✗ Not set or placeholder'}")
    print(f"STRIPE_PUBLISHABLE_KEY: {'✓ Set' if stripe_pub and stripe_pub != 'pk_test_your_stripe_publishable_key_here' else '✗ Not set or placeholder'}")
    print(f"STRIPE_WEBHOOK_SECRET: {'✓ Set' if stripe_webhook and stripe_webhook != 'whsec_your_webhook_secret_here' else '✗ Not set or placeholder'}")
    
    if not stripe_secret or stripe_secret == 'sk_test_your_stripe_secret_key_here':
        print("ERROR: STRIPE_SECRET_KEY is not properly configured")
        return False
    
    # Test Stripe API
    try:
        stripe.api_key = stripe_secret
        account = stripe.Account.retrieve()
        print(f"✓ Stripe API connection successful")
        print(f"  Account ID: {account.id}")
        print(f"  Business type: {account.business_type}")
        return True
    except stripe.error.AuthenticationError as e:
        print(f"✗ Stripe authentication failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Stripe API error: {e}")
        return False

if __name__ == "__main__":
    success = test_stripe_config()
    sys.exit(0 if success else 1)
EOF

# Run the test
if python3 /tmp/test_stripe.py; then
    print_success "Stripe configuration test passed"
else
    print_error "Stripe configuration test failed"
fi

# Clean up
rm -f /tmp/test_stripe.py /tmp/pm2_backend_info.txt

cd ..

# Step 5: Check backend logs for Stripe errors
print_status "5. Checking recent backend logs for Stripe errors..."

pm2 logs poseweaver-backend --lines 20 --nostream | grep -i stripe || echo "No recent Stripe-related log entries"

# Step 6: Provide fix recommendations
echo ""
print_status "🔧 Fix Recommendations:"
echo "======================="

# Check if Stripe keys are missing
if [[ ! -f ".env" ]] || ! grep -q "STRIPE_SECRET_KEY=sk_" .env; then
    echo ""
    print_error "Missing Stripe API Keys - Follow these steps:"
    echo ""
    echo "1. Get your Stripe API keys:"
    echo "   https://dashboard.stripe.com/apikeys"
    echo ""
    echo "2. Update your .env file:"
    echo "   STRIPE_SECRET_KEY=sk_test_your_actual_secret_key"
    echo "   STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key"
    echo ""
    echo "3. Get your webhook secret:"
    echo "   https://dashboard.stripe.com/webhooks"
    echo "   STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret"
    echo ""
    echo "4. Restart PM2 services:"
    echo "   pm2 restart ecosystem.config.js --env production"
fi

# Check if ecosystem.config.js needs updating
if ! grep -q "STRIPE_SECRET_KEY" ecosystem.config.js; then
    echo ""
    print_warning "Update ecosystem.config.js to include Stripe environment variables:"
    echo ""
    echo "Add to the backend env section:"
    echo "  STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,"
    echo "  STRIPE_PUBLISHABLE_KEY: process.env.STRIPE_PUBLISHABLE_KEY,"
    echo "  STRIPE_WEBHOOK_SECRET: process.env.STRIPE_WEBHOOK_SECRET,"
fi

echo ""
print_status "🧪 Test after fixing:"
echo "===================="
echo "1. Update .env with real Stripe keys"
echo "2. Restart PM2: pm2 restart ecosystem.config.js --env production"
echo "3. Test checkout: curl -X POST https://poseweaver.com/api/purchase/create-checkout-session"
echo "4. Check logs: pm2 logs poseweaver-backend"

print_success "Stripe configuration diagnosis completed!"
