.PHONY: help start stop test clean install dev deploy deploy-dev pm2-start pm2-stop pm2-restart pm2-status pm2-logs

# Default target
help:
	@echo "PoseWeaver - Development Commands"
	@echo "================================"
	@echo "install     - Install dependencies"
	@echo "dev         - Start development servers (traditional)"
	@echo "deploy      - Full production deployment with PM2"
	@echo "deploy-dev  - Development deployment with PM2"
	@echo "pm2-start   - Start services with PM2"
	@echo "pm2-stop    - Stop PM2 services"
	@echo "pm2-restart - Restart PM2 services"
	@echo "pm2-status  - Show PM2 status"
	@echo "pm2-logs    - Show PM2 logs"
	@echo "test        - Run all tests"
	@echo "clean       - Clean up build artifacts"

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Start development environment
dev:
	@echo "Starting development servers..."
	@echo "Backend will run on: http://localhost:5001"
	@echo "Frontend will run on: http://localhost:3000"
	@echo "Start backend: cd backend && python -m uvicorn main:app --reload --port 5001"
	@echo "Start frontend: cd frontend && npm run dev"

# Run tests
test:
	@echo "Running backend tests..."
	cd backend && python -m pytest --cov=app --cov-report=term-missing
	@echo "Running frontend tests..."
	cd frontend && npm run test

# Clean up build artifacts
clean:
	@echo "Cleaning up build artifacts..."
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf .next node_modules/.cache 2>/dev/null || true
	@echo "Cleaned up build artifacts"

# Placeholder for migrations (not needed for current setup)
migrate:
	@echo "No migrations needed for current setup"

# Development shortcuts
dev-backend:
	cd backend && python app.py

dev-frontend:
	cd frontend && npm run dev

# Linting and formatting
lint:
	@echo "Linting backend..."
	cd backend && flake8 app/ tests/
	@echo "Linting frontend..."
	cd frontend && npm run lint

format:
	@echo "Formatting backend..."
	cd backend && black app/ tests/
	@echo "Formatting frontend..."
	cd frontend && npm run lint:fix

# PM2 Deployment Commands
deploy:
	@echo "Starting full production deployment with PM2..."
	./deploy.sh

deploy-dev:
	@echo "Starting development deployment with PM2..."
	./deploy-dev.sh

pm2-start:
	@echo "Starting services with PM2..."
	pm2 start ecosystem.config.js --env production
	pm2 save

pm2-stop:
	@echo "Stopping PM2 services..."
	pm2 stop all

pm2-restart:
	@echo "Restarting PM2 services..."
	pm2 restart ecosystem.config.js

pm2-status:
	@echo "PM2 Status:"
	pm2 status

pm2-logs:
	@echo "PM2 Logs:"
	pm2 logs

# PM2 monitoring
pm2-monit:
	@echo "Opening PM2 monitoring..."
	pm2 monit