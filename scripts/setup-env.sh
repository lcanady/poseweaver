#!/bin/bash

# PoseWeaver Environment Setup Script
# Configures the application for different deployment modes

set -e

MODE=${1:-development}

echo "🔧 Setting up PoseWeaver for $MODE mode..."

case $MODE in
    "development")
        echo "📝 Configuring for development (HTTP only)..."
        
        # Ensure HTTPS redirect is commented out
        sed -i 's/^    location \/ {/    # location \/ {/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^        return 301/    #     return 301/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^    }$/    # }/' ./nginx/conf.d/poseweaver.conf
        
        # Ensure development HTTP serving is enabled
        sed -i 's/^    # location \/ {/    location \/ {/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^    #     limit_req zone=general/        limit_req zone=general/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^    #     proxy_pass http:\/\/frontend;/        proxy_pass http:\/\/frontend;/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^    #     include \/etc\/nginx\/proxy_params;/        include \/etc\/nginx\/proxy_params;/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^    # }$/    }/' ./nginx/conf.d/poseweaver.conf
        
        echo "✅ Development mode configured"
        echo "   Run: docker-compose up -d"
        echo "   Access: http://localhost"
        ;;
        
    "production")
        echo "🚀 Configuring for production (HTTPS with SSL)..."
        
        # Enable HTTPS redirect
        sed -i 's/^    # location \/ {/    location \/ {/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^    #     return 301/        return 301/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^    # }$/    }/' ./nginx/conf.d/poseweaver.conf
        
        # Comment out development HTTP serving
        sed -i 's/^    location \/ {/    # location \/ {/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^        limit_req zone=general/    #     limit_req zone=general/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^        proxy_pass http:\/\/frontend;/    #     proxy_pass http:\/\/frontend;/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^        include \/etc\/nginx\/proxy_params;/    #     include \/etc\/nginx\/proxy_params;/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^    }$/    # }/' ./nginx/conf.d/poseweaver.conf
        
        # Enable HTTPS server block
        sed -i 's/^# server {/server {/' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^#     /    /' ./nginx/conf.d/poseweaver.conf
        sed -i 's/^# }$/}/' ./nginx/conf.d/poseweaver.conf
        
        echo "✅ Production mode configured"
        echo "   Next steps:"
        echo "   1. Run: ./scripts/setup-ssl.sh"
        echo "   2. Run: docker-compose up -d"
        echo "   3. Access: https://poseweaver.com"
        ;;
        
    *)
        echo "❌ Invalid mode: $MODE"
        echo "Usage: $0 [development|production]"
        exit 1
        ;;
esac
