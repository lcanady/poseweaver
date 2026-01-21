.PHONY: help start stop test clean install build logs

# Default target
help:
	@echo "MUSH Pose Editor - Development Commands"
	@echo "======================================"
	@echo "start    - Start development environment"
	@echo "stop     - Stop development environment"
	@echo "test     - Run all tests"
	@echo "clean    - Clean up containers and volumes"
	@echo "install  - Install dependencies"
	@echo "build    - Build Docker images"
	@echo "logs     - Show application logs"
	@echo "migrate  - Run database migrations (if needed)"

# Start development environment
start:
	docker-compose up -d
	@echo "Development environment started!"
	@echo "Frontend: http://localhost:3001"
	@echo "Backend: http://localhost:5001"

# Stop development environment
stop:
	docker-compose down

# Run tests
test:
	@echo "Running backend tests..."
	docker-compose exec backend pytest --cov=app --cov-report=term-missing
	@echo "Running frontend tests..."
	docker-compose exec frontend npm run test:coverage

# Clean up containers and volumes
clean:
	docker-compose down -v
	docker system prune -f
	@echo "Cleaned up containers and volumes"

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Build Docker images
build:
	docker-compose build --no-cache

# Show application logs
logs:
	docker-compose logs -f

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