.PHONY: help start stop test clean install dev

# Default target
help:
	@echo "PoseWeaver - Development Commands"
	@echo "================================"
	@echo "install  - Install dependencies"
	@echo "dev      - Start development servers"
	@echo "test     - Run all tests"
	@echo "clean    - Clean up build artifacts"

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