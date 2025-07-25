# Makefile

ENV_FILE=.env
REQUIRED_VARS=LANGSMITH_API_KEY OPENAI_API_KEY OPENAI_MODEL GITHUB_TOKEN

.PHONY: all check docker-up initialize run stop

all: check docker-up initialize

check:
	@echo "🔍 Checking prerequisites..."
	@if ! [ -x "$$(command -v docker)" ]; then \
		echo "❌ Docker is not installed. Please install Docker first."; \
		exit 1; \
	fi
	@if ! docker info > /dev/null 2>&1; then \
		echo "❌ Docker daemon is not running. Please start Docker Desktop."; \
		exit 1; \
	fi
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "❌ $(ENV_FILE) file not found. Please create it or copy from .env.example."; \
		exit 1; \
	fi
	@echo "📄 Validating environment variables in $(ENV_FILE)..."
	@set -a; . $(ENV_FILE); \
	for var in $(REQUIRED_VARS); do \
		if [ -z "$$${var}" ]; then \
			echo "❌ Environment variable '$$${var}' is missing or empty in $(ENV_FILE)"; \
			exit 1; \
		fi; \
	done
	@echo "✅ All checks passed."

docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose up --build -d
	@echo "✅ Docker containers are up."

initialize:
	@echo "🚀 Initializing app..."
	@echo "⏳ Waiting for FastAPI to be ready (max 30s)..."
	@start=$$(date +%s); \
	while ! curl -s http://localhost:8000/docs > /dev/null; do \
		now=$$(date +%s); \
		if [ $$((now - start)) -gt 30 ]; then \
			echo "❌ Timeout waiting for FastAPI to become available."; \
			exit 1; \
		fi; \
		sleep 1; \
	done; \
	echo "🔧 Sending initialization request..."; \
	if command -v jq >/dev/null 2>&1; then \
		curl -s -X POST http://localhost:8000/setup/initialize | jq .; \
	else \
		echo "⚠️  jq not found. Showing raw response:"; \
		curl -s -X POST http://localhost:8000/setup/initialize; \
	fi; \
	echo "\n✅ App initialized."; \
	echo "🟢 App is running at: http://localhost:8000/"; \
	python3 -m webbrowser http://localhost:8000

run: all

stop:
	@echo "🛑 Stopping Docker containers..."
	@docker-compose down