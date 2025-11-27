.PHONY: help install format format-check lint lint-fix test test-quiz test-screenplay test-scene test-video test-e2e test-cov clean up down restart logs ps check-env

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)TarAIntino Project - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install development dependencies (black, ruff, pytest)
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	pip install -e ".[dev]"
	@echo "$(GREEN)Dependencies installed!$(NC)"

format: ## Format code with black
	@echo "$(BLUE)Formatting code with black...$(NC)"
	black src/ tests/ --exclude '/(\.git|\.venv|build|dist|node_modules)/'
	@echo "$(GREEN)Code formatted!$(NC)"

format-check: ## Check code formatting without changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	black --check src/ tests/ --exclude '/(\.git|\.venv|build|dist|node_modules)/'

lint: ## Lint code with ruff (check only)
	@echo "$(BLUE)Linting code with ruff...$(NC)"
	ruff check src/ tests/

lint-fix: ## Lint and auto-fix issues with ruff
	@echo "$(BLUE)Linting and fixing code with ruff...$(NC)"
	ruff check --fix src/ tests/
	@echo "$(GREEN)Linting complete!$(NC)"

test: ## Run all microservice tests
	@echo "$(BLUE)Running all microservice tests...$(NC)"
	@echo "\n=== Testing Quiz Service ==="
	docker compose exec -T quiz-service python -m pytest tests/ --cov=. --cov-report=term-missing -v || true
	@echo "\n=== Testing Screenplay Writer ==="
	docker compose exec -T screenplay-writer python -m pytest tests/ --cov=. --cov-report=term-missing -v || true
	@echo "\n=== Testing Scene Decomposer ==="
	docker compose exec -T scene-decomposer python -m pytest tests/ --cov=. --cov-report=term-missing -v || true
	@echo "\n=== Testing Video Generator ==="
	docker compose exec -T video-generator python -m pytest tests/ --cov=. --cov-report=term-missing -v || true
	@echo "$(GREEN)All tests complete!$(NC)"

test-cov: ## Run all tests with HTML coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	docker compose exec -T quiz-service python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing -v || true
	docker compose exec -T screenplay-writer python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing -v || true
	docker compose exec -T scene-decomposer python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing -v || true
	docker compose exec -T video-generator python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing -v || true
	@echo "$(GREEN)Coverage reports generated in htmlcov/$(NC)"

test-quiz: ## Run quiz-vector tests only
	@echo "$(BLUE)Testing Quiz Service...$(NC)"
	docker compose exec -T quiz-service python -m pytest tests/ --cov=. --cov-report=term-missing -v

test-screenplay: ## Run screenplay-writer tests only
	@echo "$(BLUE)Testing Screenplay Writer...$(NC)"
	docker compose exec -T screenplay-writer python -m pytest tests/ --cov=. --cov-report=term-missing -v

test-scene: ## Run scene-decomposer tests only
	@echo "$(BLUE)Testing Scene Decomposer...$(NC)"
	docker compose exec -T scene-decomposer python -m pytest tests/ --cov=. --cov-report=term-missing -v

test-video: ## Run video-generator tests only
	@echo "$(BLUE)Testing Video Generator...$(NC)"
	docker compose exec -T video-generator python -m pytest tests/ --cov=. --cov-report=term-missing -v

test-e2e: ## Run end-to-end integration tests
	@echo "$(BLUE)Running end-to-end integration tests...$(NC)"
	docker run --rm --network host -v $$(pwd)/tests:/tests taraintino-base:latest sh -c "pip install -q requests && python -m pytest /tests/test_end_to_end_trailer_generation.py -v"

check: ## Run format + lint + test (comprehensive check before commits)
	@echo "$(BLUE)Running comprehensive checks...$(NC)"
	@echo "\n========================================="
	@echo "$(BLUE)STEP 1: Formatting code with black$(NC)"
	@echo "========================================="
	@$(MAKE) format
	@echo "\n========================================="
	@echo "$(BLUE)STEP 2: Linting code with ruff$(NC)"
	@echo "========================================="
	@$(MAKE) lint-fix
	@echo "\n========================================="
	@echo "$(BLUE)STEP 3: Running all tests$(NC)"
	@echo "========================================="
	@$(MAKE) test
	@echo "\n========================================="
	@echo "$(GREEN)✓ All checks completed!$(NC)"
	@echo "========================================="

up: ## Start all Docker services
	@echo "$(BLUE)Starting all services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "Quiz Service: http://localhost:8082"
	@echo "Screenplay Writer: http://localhost:8080"
	@echo "Scene Decomposer: http://localhost:8001"
	@echo "Video Generator: http://localhost:8003"
	@echo "Frontend: http://localhost:3000"
	@echo "ChromaDB: http://localhost:8000"

down: ## Stop all Docker services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker compose down

restart: ## Restart all Docker services
	@echo "$(YELLOW)Restarting all services...$(NC)"
	docker compose restart

logs: ## Show logs from all services
	docker compose logs -f

logs-quiz: ## Show quiz-service logs
	docker compose logs -f quiz-service

logs-screenplay: ## Show screenplay-writer logs
	docker compose logs -f screenplay-writer

logs-scene: ## Show scene-decomposer logs
	docker compose logs -f scene-decomposer

logs-video: ## Show video-generator logs
	docker compose logs -f video-generator

logs-frontend: ## Show frontend logs
	docker compose logs -f frontend

ps: ## Show running Docker containers
	docker compose ps

check-env: ## Check if required .env files exist
	@echo "$(BLUE)Checking environment files...$(NC)"
	@if [ ! -f src/screenplay-writer/.env ]; then \
		echo "$(YELLOW)Warning: src/screenplay-writer/.env not found!$(NC)"; \
		echo "$(BLUE)Copy .env.example and fill in your values:$(NC)"; \
		echo "  cp src/screenplay-writer/.env.example src/screenplay-writer/.env"; \
	else \
		echo "$(GREEN)✓ src/screenplay-writer/.env found$(NC)"; \
	fi
	@if [ ! -f src/scene-decomposer/.env ]; then \
		echo "$(YELLOW)Warning: src/scene-decomposer/.env not found!$(NC)"; \
		echo "$(BLUE)Copy .env.example and fill in your values:$(NC)"; \
		echo "  cp src/scene-decomposer/.env.example src/scene-decomposer/.env"; \
	else \
		echo "$(GREEN)✓ src/scene-decomposer/.env found$(NC)"; \
	fi
	@if [ ! -f src/quiz-vector/secrets/llm-service-account.json ]; then \
		echo "$(YELLOW)Warning: GCS credentials not found!$(NC)"; \
	else \
		echo "$(GREEN)✓ GCS credentials found$(NC)"; \
	fi
	@if [ ! -f src/video-generator/secret.json ]; then \
		echo "$(YELLOW)Warning: Gemini API credentials not found!$(NC)"; \
	else \
		echo "$(GREEN)✓ Gemini API credentials found$(NC)"; \
	fi

clean: ## Clean Python cache files and build artifacts
	@echo "$(YELLOW)Cleaning Python cache files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

clean-volumes: ## Remove all Docker volumes (WARNING: deletes data!)
	@echo "$(YELLOW)Removing Docker volumes...$(NC)"
	docker compose down -v
	@echo "$(GREEN)Volumes removed!$(NC)"

init: check-env install up ## Initialize project (check env, install deps, start services)
	@echo "$(GREEN)Project initialized!$(NC)"
	@echo "Next steps:"
	@echo "  1. Review and update .env files"
	@echo "  2. Run 'make test' to verify setup"
	@echo "  3. Visit http://localhost:3000 to start generating trailers!"
