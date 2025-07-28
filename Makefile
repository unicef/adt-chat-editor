# Makefile

ENV_FILE=.env
REQUIRED_VARS=LANGSMITH_API_KEY OPENAI_API_KEY OPENAI_MODEL GITHUB_TOKEN ADT_REPOS

.PHONY: all check docker-up initialize run stop clone-repos select-adt

all: check clone-repos select-adt docker-up initialize

check:
	@echo "🔍 Checking prerequisites..."
	@if ! [ -x "$$(command -v git)" ]; then \
		echo "❌ Git is not installed. Please install Git first."; \
		exit 1; \
	fi
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

clone-repos:
	@echo "🔁 Cloning ADT Git repositories..."
	@set -a; . $(ENV_FILE); set +a; \
	for repo_url in $$ADTS; do \
		repo_name=$$(basename $$repo_url .git); \
		input_dir="data/$$repo_name/input"; \
		output_dir="data/$$repo_name/output"; \
		for dir in $$input_dir $$output_dir; do \
			if [ -d "$$dir" ] && [ "$$(ls -A $$dir 2>/dev/null)" ]; then \
				echo "✅ Repo already exists and is not empty at $$dir. Skipping clone."; \
			else \
				echo "📥 Cloning $$repo_url into $$dir..."; \
				mkdir -p "$$(dirname $$dir)"; \
				git clone "$$repo_url" "$$dir" || { echo "❌ Failed to clone repo $$repo_url into $$dir"; exit 1; }; \
			fi; \
		done; \
	done; \
	echo "✅ All ADT repositories are ready."

select-adt:
	@echo "📂 Available ADTs:"; \
	ls -1 data | nl; \
	read -p "Select ADT number: " choice; \
	adt=$$(ls -1 data | sed -n "$${choice}p"); \
	echo "🔗 Linking to $$adt..."; \
	rm -rf data/input data/output; \
	ln -sfn "$$adt/input" data/input; \
	ln -sfn "$$adt/output" data/output; \
	echo "✅ Linked to ADT: $$adt"

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
