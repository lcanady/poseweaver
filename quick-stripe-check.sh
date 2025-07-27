#!/bin/bash

# Quick Stripe Environment Check
echo "🔍 Quick Stripe Environment Check"
echo "================================="

# Check if .env exists
if [[ -f ".env" ]]; then
    echo "✅ .env file found"
    
    # Check for Stripe keys
    if grep -q "STRIPE_SECRET_KEY=sk_" .env; then
        echo "✅ STRIPE_SECRET_KEY appears to be set"
    else
        echo "❌ STRIPE_SECRET_KEY not properly set in .env"
        echo "   Current value: $(grep STRIPE_SECRET_KEY .env || echo 'NOT FOUND')"
    fi
    
    if grep -q "STRIPE_PUBLISHABLE_KEY=pk_" .env; then
        echo "✅ STRIPE_PUBLISHABLE_KEY appears to be set"
    else
        echo "❌ STRIPE_PUBLISHABLE_KEY not properly set in .env"
    fi
    
    if grep -q "STRIPE_WEBHOOK_SECRET=whsec_" .env; then
        echo "✅ STRIPE_WEBHOOK_SECRET appears to be set"
    else
        echo "❌ STRIPE_WEBHOOK_SECRET not properly set in .env"
    fi
else
    echo "❌ .env file not found!"
fi

# Check ecosystem.config.js
if grep -q "STRIPE_SECRET_KEY" ecosystem.config.js 2>/dev/null; then
    echo "✅ ecosystem.config.js has Stripe environment variables"
else
    echo "❌ ecosystem.config.js missing Stripe environment variables"
fi

# Check PM2 process
if pm2 list | grep -q "poseweaver-backend" 2>/dev/null; then
    echo "✅ PM2 backend process is running"
    
    # Check if environment is loaded
    if pm2 show poseweaver-backend 2>/dev/null | grep -q "STRIPE_SECRET_KEY"; then
        echo "✅ PM2 process has Stripe environment variables loaded"
    else
        echo "❌ PM2 process does NOT have Stripe environment variables loaded"
        echo "   → Need to restart PM2 after updating .env"
    fi
else
    echo "❌ PM2 backend process not found"
fi

echo ""
echo "🔧 Quick Fix Steps:"
echo "1. Edit .env: nano .env"
echo "2. Add real Stripe keys (get from https://dashboard.stripe.com/apikeys)"
echo "3. Restart PM2: pm2 restart ecosystem.config.js --env production"
echo "4. Test: pm2 logs poseweaver-backend"
