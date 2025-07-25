#!/bin/bash

# PoseWeaver Backend Heroku Deployment Script
echo "🚀 Deploying PoseWeaver Backend to Heroku..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first:"
    echo "   https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if user is logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Please log in to Heroku first:"
    echo "   heroku login"
    exit 1
fi

# Get app name from user or use default
read -p "Enter your Heroku app name (or press Enter for 'poseweaver-backend'): " APP_NAME
APP_NAME=${APP_NAME:-poseweaver-backend}

echo "📱 Creating Heroku app: $APP_NAME"

# Create Heroku app
heroku create $APP_NAME

# Set Python buildpack
heroku buildpacks:set heroku/python -a $APP_NAME

# Set environment variables
echo "🔧 Setting up environment variables..."
echo "Please set the following environment variables in Heroku Dashboard or via CLI:"
echo ""
echo "Required Environment Variables:"
echo "- MONGODB_URI (your MongoDB connection string)"
echo "- SECRET_KEY (Flask secret key)"
echo "- JWT_SECRET_KEY (JWT secret key)"
echo "- VENICE_API_KEY (Venice AI API key)"
echo "- STRIPE_SECRET_KEY (Stripe secret key)"
echo "- STRIPE_PUBLISHABLE_KEY (Stripe publishable key)"
echo "- STRIPE_WEBHOOK_SECRET (Stripe webhook secret)"
echo "- FRONTEND_URL (your frontend URL for CORS)"
echo ""

# Deploy to Heroku
echo "🚀 Deploying to Heroku..."
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main

echo "✅ Deployment complete!"
echo "🌐 Your app is available at: https://$APP_NAME.herokuapp.com"
echo "📊 View logs: heroku logs --tail -a $APP_NAME"
echo "⚙️  Set environment variables: heroku config:set KEY=value -a $APP_NAME"
