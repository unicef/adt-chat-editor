# Makefile for ADT Chat Editor
# This Makefile automates the setup and deployment of the ADT Chat Editor application
# It handles environment validation, repository cloning, Docker container management, and app initialization
#
# MODES:
# - Reviewer mode: Works with multiple repositories from ADT_REPOS environment variable
#   Usage: make reviewer or make run-reviewer
# - Creator mode: Works with a single local repository
#   Usage: make creator or make run-creator
# - Default mode: Runs in reviewer mode
#   Usage: make run

# Environment configuration
ENV_FILE=.env
# List of required environment variables that must be set in .env file
REQUIRED_VARS=OPENAI_API_KEY OPENAI_MODEL GITHUB_TOKEN ADTS

# Define all available targets (commands that can be run with 'make')
.PHONY: check docker-up initialize run stop clone-repos select-adt reviewer creator test install-test-deps

# Reviewer mode - works with multiple repositories from ADT_REPOS
reviewer: check clone-repos clone-utils select-adt ensure-data-dirs docker-up initialize

# Creator mode - works with a single local repository
creator: check clone-utils setup-creator ensure-data-dirs docker-up initialize

# Validate all prerequisites before proceeding
check:
	@echo "🔍 Checking prerequisites..."
	@if [ -x "$$(command -v git)" ]; then \
		echo "✅ Git is installed: $$(git --version)"; \
	else \
		echo "❌ Git is not installed. Please install Git first."; \
		exit 1; \
	fi
	@if [ -x "$$(command -v docker)" ]; then \
		echo "✅ Docker is installed: $$(docker --version)"; \
	else \
		echo "❌ Docker is not installed. Please install Docker first."; \
		exit 1; \
	fi
	@if docker info > /dev/null 2>&1; then \
		echo "✅ Docker daemon is running"; \
	else \
		echo "❌ Docker daemon is not running. Please start Docker Desktop."; \
		exit 1; \
	fi
	@if [ -f $(ENV_FILE) ]; then \
		echo "✅ $(ENV_FILE) file exists"; \
	else \
		echo "❌ $(ENV_FILE) file not found. Please create it or copy from .env.example."; \
		exit 1; \
	fi
	@set -a; . ./$(ENV_FILE); \
	for var in $(REQUIRED_VARS); do \
		if [ -z "$${!var}" ]; then \
			echo "❌ Environment variable '$$var' is missing or empty in $(ENV_FILE)"; \
			exit 1; \
		fi; \
	done; \
	echo "✅ All required environment variables are set correctly"
	@echo "✅ All checks passed."

# Clone ADT (Accessible Digital Textbook) repositories from the URLs specified in ADT_REPOS
clone-repos:
	@echo "🔁 Managing ADT Git repositories..."
	@echo "📋 Creating data directory if it doesn't exist..."
	@mkdir -p data
	@set -a; . ./$(ENV_FILE); set +a; \
	for repo_url in $$ADTS; do \
		repo_name=$$(basename $$repo_url .git); \
		echo "📋 Processing repository: $$repo_name"; \
		repo_dir="data/$$repo_name"; \
		echo "📋 Checking repository status: $$repo_dir"; \
		if [ -d "$$repo_dir/.git" ]; then \
			echo "📋 Repository already exists: $$repo_dir"; \
			echo "📥 Pulling latest changes from $$repo_url..."; \
			(cd "$$repo_dir" && rm -f .git/config.lock && git remote set-url origin "$$repo_url" && git pull origin main || git pull origin master || git pull || { \
				echo "❌ Failed to pull latest changes from $$repo_url"; \
				exit 1; \
			}); \
			echo "✅ Successfully updated $$repo_name"; \
		elif [ -d "$$repo_dir" ] && [ "$$(ls -A $$repo_dir 2>/dev/null)" ]; then \
			echo "⚠️  Directory exists but is not a git repository: $$repo_dir"; \
			echo "📋 Removing non-git directory and cloning fresh..."; \
			rm -rf "$$repo_dir"; \
			if git clone "$$repo_url" "$$repo_dir"; then \
				echo "✅ Successfully cloned $$repo_name"; \
			else \
				echo "❌ Failed to clone repo $$repo_url into $$repo_dir"; \
				exit 1; \
			fi; \
		else \
			echo "📥 Cloning $$repo_url into $$repo_dir..."; \
			if git clone "$$repo_url" "$$repo_dir"; then \
				echo "✅ Successfully cloned $$repo_name"; \
			else \
				echo "❌ Failed to clone repo $$repo_url into $$repo_dir"; \
				exit 1; \
			fi; \
		fi; \
	done; \
	echo "✅ All ADT repositories are ready."

# Clone the ADT Utils repository if defined in .env
clone-utils:
	@echo "🔧 Managing ADT Utils repository..."
	@set -a; . ./$(ENV_FILE); set +a; \
	if [ -z "$$ADT_UTILS_REPO" ]; then \
		echo "ℹ️  ADT_UTILS_REPO not set in $(ENV_FILE). Skipping."; \
		exit 0; \
	fi; \
	repo_url="$$ADT_UTILS_REPO"; \
	repo_name="adt-utils"; \
	repo_dir="data/$$repo_name"; \
	echo "📋 Processing repository: $$repo_name"; \
	echo "📋 Checking repository status: $$repo_dir"; \
	if [ -d "$$repo_dir/.git" ]; then \
		echo "📋 Repository already exists: $$repo_dir"; \
		echo "📥 Pulling latest changes from $$repo_url..."; \
		(cd "$$repo_dir" && git pull || { \
			echo "❌ Failed to pull latest changes from $$repo_url"; \
			exit 1; \
		}); \
		echo "✅ Successfully updated $$repo_name"; \
	elif [ -d "$$repo_dir" ]; then \
		echo "⚠️  Directory exists but is not a git repository: $$repo_dir"; \
		echo "📋 Removing non-git directory and cloning fresh..."; \
		rm -rf "$$repo_dir"; \
		if git clone "$$repo_url" "$$repo_dir"; then \
			echo "✅ Successfully cloned $$repo_name"; \
		else \
			echo "❌ Failed to clone repo $$repo_url into $$repo_dir"; \
			exit 1; \
		fi; \
	else \
		echo "📥 Cloning $$repo_url into $$repo_dir..."; \
		if git clone "$$repo_url" "$$repo_dir"; then \
			echo "✅ Successfully cloned $$repo_name"; \
		else \
			echo "❌ Failed to clone repo $$repo_url into $$repo_dir"; \
			exit 1; \
		fi; \
	fi; \
	echo "✅ ADT Utils repository is ready."

# Interactive selection of which ADT repository to work with
select-adt:
	@echo "📂 Available ADTs:"; \
	echo "📋 Checking data directory contents..."; \
	ls -la data/ 2>/dev/null || echo "📋 Data directory is empty or doesn't exist"; \
	if [ ! -d "data" ] || [ -z "$$(ls -A data 2>/dev/null)" ]; then \
		echo "❌ No repositories found in data directory. Please check your ADT_REPOS environment variable."; \
		exit 1; \
	fi; \
	echo "📋 Filtering out input/output/utils directories..."; \
	ls -1 data | grep -v "^input$$" | grep -v "^output$$" | grep -v "^adt-utils$$" | nl; \
	read -p "Select ADT number: " choice; \
	adt=$$(ls -1 data | grep -v "^input$$" | grep -v "^output$$" | grep -v "^adt-utils$$" | sed -n "$${choice}p"); \
	if [ -z "$$adt" ]; then \
		echo "❌ Invalid selection. Please try again."; \
		exit 1; \
	fi; \
	echo "🔗 Setting up $$adt..."; \
	rm -rf data/input data/output; \
	mkdir -p data; \
	echo "📋 Creating hard copy for data/input (original ADT)..."; \
	(\
		cd data && \
		rm -rf input && \
		mkdir -p input && \
		cp -R "$$adt"/. input/ \
	); \
	echo "📋 Creating symbolic link for data/output..."; \
	(cd data && ln -sfn "$$adt" output); \
	echo "✅ Successfully set up ADT: $$adt (input copied, output linked)"

# Ensure data directories exist before starting Docker
ensure-data-dirs:
	@echo "📋 Ensuring data directories exist..."
	@if [ ! -d "data/input" ] && [ ! -L "data/input" ]; then \
		echo "❌ data/input directory or symlink does not exist. Please run select-adt (reviewer mode) or setup-creator (creator mode) first."; \
		exit 1; \
	fi; \
	if [ ! -d "data/output" ] && [ ! -L "data/output" ]; then \
		echo "❌ data/output directory or symlink does not exist. Please run select-adt (reviewer mode) or setup-creator (creator mode) first."; \
		exit 1; \
	fi; \
	echo "✅ Data directories are ready"

# Setup creator mode with a single local repository
# Usage: make creator REPO_PATH=/path/to/your/repository
setup-creator:
	@echo "🎨 Setting up Creator mode..."
	@if [ -z "$(REPO_PATH)" ]; then \
		echo "❌ REPO_PATH argument is required. Usage: make creator REPO_PATH=/path/to/your/repository"; \
		exit 1; \
	fi; \
	repo_path=$$(eval echo "$(REPO_PATH)"); \
	if [ ! -d "$$repo_path" ]; then \
		echo "❌ Directory does not exist: $$repo_path"; \
		exit 1; \
	fi; \
	if [ ! -d "$$repo_path/.git" ]; then \
		echo "❌ Directory is not a git repository: $$repo_path"; \
		exit 1; \
	fi; \
	echo "📋 Setting up creator mode directories..."; \
	rm -rf data/input data/output; \
	mkdir -p data; \
	echo "📋 Copying files to data/input..."; \
	cp -r "$$repo_path" data/input; \
	echo "📋 Creating output directory..."; \
	if [ "$$(uname -s)" = "Linux" ] || [ "$$(uname -s)" = "Darwin" ]; then \
		ln -sfn "/app/external_repo" data/output; \
		echo "📋 Created symlink for data/output"; \
	else \
		cp -r "$$repo_path" data/output; \
		echo "📋 Copied files to data/output (symlink not supported)"; \
	fi; \
	echo "📋 Setting EXTERNAL_REPO_PATH environment variable..."; \
	echo "EXTERNAL_REPO_PATH=$$repo_path" >> .env; \
	echo "✅ Successfully set up creator mode: files copied to data/input and output"

# Start Docker containers using docker-compose
docker-up:
	@echo "🐳 Starting Docker containers..."
	@echo "📋 Loading environment variables..."
	@set -a; . ./$(ENV_FILE); set +a; \
	if docker-compose up --build -d; then \
		echo "✅ Docker containers started successfully"; \
	else \
		echo "❌ Failed to start Docker containers"; \
		exit 1; \
	fi

# Initialize the application after containers are running
initialize:
	@echo "🚀 Initializing app..."
	@echo "⏳ Waiting for FastAPI to be ready (max 30s)..."
	@echo "📋 Checking Docker container status..."
	@docker-compose ps
	@echo "📋 Checking container logs..."
	@docker-compose logs --tail=20
	@start=$$(date +%s); \
	while ! curl -s http://localhost:8000/docs > /dev/null; do \
		now=$$(date +%s); \
		if [ $$((now - start)) -gt 30 ]; then \
			echo "❌ Timeout waiting for FastAPI to become available."; \
			echo "📋 Final container status:"; \
			docker-compose ps; \
			echo "📋 Final container logs:"; \
			docker-compose logs --tail=50; \
			exit 1; \
		fi; \
		echo "⏳ Still waiting... ($$((now - start))s elapsed)"; \
		sleep 1; \
	done; \
	echo "✅ FastAPI server is ready"; \
	echo "🔧 Sending initialization request..."; \
	if command -v jq >/dev/null 2>&1; then \
		curl -s -X POST http://localhost:8000/setup/initialize | jq .; \
	else \
		echo "⚠️  jq not found. Showing raw response:"; \
		curl -s -X POST http://localhost:8000/setup/initialize; \
	fi; \
	echo "\n✅ App initialized successfully."; \
	echo "🟢 App is running at: http://localhost:8000/"; \
	if command -v python3 >/dev/null 2>&1; then \
		python3 -c "import webbrowser; webbrowser.open('http://localhost:8000/')" || true; \
	elif command -v python >/dev/null 2>&1; then \
		python -c "import webbrowser; webbrowser.open('http://localhost:8000/')" || true; \
	elif command -v open >/dev/null 2>&1; then \
		open http://localhost:8000/ || true; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8000/ || true; \
	else \
		echo "Please open http://localhost:8000/ in your browser"; \
	fi

# Convenience targets for different modes
run: reviewer
run-reviewer: reviewer
run-creator: creator
# Usage: make run-creator REPO_PATH=/path/to/your/repository

# Stop and remove Docker containers
stop:
	@echo "🛑 Stopping Docker containers..."
	if docker-compose down; then \
		echo "✅ Docker containers stopped successfully"; \
	else \
		echo "❌ Failed to stop Docker containers"; \
		exit 1; \
	fi

# Install test dependencies (pytest, pytest-asyncio)
install-test-deps:
	@echo "🧪 Installing test dependencies..."
	@if command -v poetry >/dev/null 2>&1; then \
		if poetry install --with test; then \
			echo "✅ Installed test deps via Poetry"; \
		else \
			echo "⚠️ Poetry install failed. Falling back to pip..."; \
			python -m pip install -q pytest pytest-asyncio; \
			echo "✅ Installed test deps via pip"; \
		fi; \
	else \
		python -m pip install -q pytest pytest-asyncio; \
		echo "✅ Installed test deps via pip"; \
	fi

# Run unit tests with pytest
test:
	@echo "🧪 Running unit tests..."
	@if python -m pytest --version >/dev/null 2>&1; then \
		python -m pytest -q; \
	else \
		echo "📦 Installing test dependencies..."; \
		python -m pip install -q pytest pytest-asyncio; \
		python -m pytest -q; \
	fi

# Run unit tests with verbose output (test names and details)
.PHONY: test-verbose
test-verbose:
	@echo "🧪 Running unit tests (verbose)..."
	@if python -m pytest --version >/dev/null 2>&1; then \
		python -m pytest -v; \
	else \
		echo "📦 Installing test dependencies..."; \
		python -m pip install -q pytest pytest-asyncio; \
		python -m pytest -v; \
	fi
