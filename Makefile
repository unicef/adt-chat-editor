# Makefile for ADT Chat Editor
# This Makefile automates the setup and deployment of the ADT Chat Editor application
# It handles environment validation, repository cloning, Docker container management, and app initialization
#
SHELL := /bin/bash

# MODES:
# - Reviewer mode: Works with multiple repositories from ADT_REPOS environment variable
#   Usage: make reviewer or make run-reviewer
# - Creator mode: Works with a single local repository
#   Usage: make creator or make run-creator
# - Default mode: Runs in reviewer mode
#   Usage: make run

# Environment configuration
ENV_FILE=.env
# List of required environment variables
# Global minimal requirements: OPENAI_API_KEY, OPENAI_MODEL
# Reviewer mode additionally requires: ADTS
GLOBAL_REQUIRED_VARS=OPENAI_API_KEY OPENAI_MODEL OPENAI_CODEX_MODEL
REVIEWER_REQUIRED_VARS=ADTS

# Define all available targets (commands that can be run with 'make')
.PHONY: check ensure-env configure-env check-reviewer check-creator docker-up initialize run stop clone-repos select-adt reviewer creator test install-test-deps install-adt-utils-deps

# Determine docker compose command for better cross-platform support
# Prefer docker-compose if available, otherwise use 'docker compose'
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo docker-compose; else echo docker compose; fi)

# Control verbosity of in-container installation (set VERBOSE=1 to see full logs)
ifeq ($(VERBOSE),1)
REDIRECT :=
else
REDIRECT := >/dev/null 2>&1
endif

# Reviewer mode - works with multiple repositories from ADTS
reviewer: check-reviewer stop clone-repos clone-utils select-adt ensure-data-dirs docker-up install-adt-utils-deps initialize

# Creator mode - works with a single local repository (can be non-git)
creator: check-creator stop clone-utils setup-creator ensure-data-dirs docker-up install-adt-utils-deps initialize

# Validate basic prerequisites (Docker) and ensure minimal env setup
check:
	@echo "🔍 Checking prerequisites..."
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
	@$(MAKE) --no-print-directory ensure-env
	@echo "✅ Basic checks passed."

# Ensure .env exists and has required variables
ensure-env:
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "📝 $(ENV_FILE) not found. Launching interactive configuration..."; \
		$(MAKE) --no-print-directory configure-env; \
	else \
		echo "📄 Found $(ENV_FILE). Checking required variables..."; \
		set -a; . ./$(ENV_FILE); set +a; \
		missing_vars=""; \
		for var in $(GLOBAL_REQUIRED_VARS); do \
			if [ -z "$${!var}" ] || [ "$${!var}" = "your-openai-key-here" ] || [ "$${!var}" = "your-github-token-here" ]; then \
				missing_vars="$$missing_vars $$var"; \
			fi; \
		done; \
		if [ -n "$$missing_vars" ]; then \
			echo "⚠️  Missing or placeholder values for:$$missing_vars"; \
			echo "   Launching interactive configuration..."; \
			$(MAKE) --no-print-directory configure-env; \
		else \
			echo "✅ Required variables are configured."; \
		fi; \
	fi

# Interactive configuration based on .env.example
configure-env:
	@if [ ! -x scripts/configure_env.sh ]; then \
		echo "🔧 Setting execute permission on configure_env.sh..."; \
		chmod +x scripts/configure_env.sh; \
	fi; \
	bash scripts/configure_env.sh .env.example $(ENV_FILE);

# Reviewer-specific checks
check-reviewer: check
	@set -a; . ./$(ENV_FILE); set +a; \
	for var in $(REVIEWER_REQUIRED_VARS); do \
		if [ -z "$${!var}" ]; then \
			echo "❌ Reviewer mode requires '$$var' to be set in $(ENV_FILE)."; \
			echo "   Tip: run 'make configure-env' to set ADTS interactively, or run Creator mode with 'make run-creator REPO_PATH=/path/to/adt'"; \
			exit 1; \
		fi; \
	done; \
	echo "✅ Reviewer-specific checks passed."

# Creator-specific checks
check-creator: check
	@echo "✅ Creator-specific checks passed."

# Clone ADT (Accessible Digital Textbook) repositories from the URLs specified in ADT_REPOS
clone-repos:
	@echo "🔁 Managing ADT Git repositories..."
	@echo "📋 Creating data directory if it doesn't exist..."
	@mkdir -p data
	@set -a; . ./$(ENV_FILE); set +a; \
for repo_url in $$ADTS; do \
    https_url=$$(echo "$$repo_url" | sed -E 's#git@([^:]+):([^/]+)/([^\.]+)\.git#https://\1/\2/\3.git#'); \
    ssh_url=$$(echo "$$https_url" | sed -E 's#https://([^/]+)/([^/]+)/([^\.]+)\.git#git@\1:\2/\3.git#'); \
    repo_name=$$(basename $$https_url .git); \
		echo "📋 Processing repository: $$repo_name"; \
		repo_dir="data/$$repo_name"; \
		echo "📋 Checking repository status: $$repo_dir"; \
    if [ -d "$$repo_dir/.git" ]; then \
        echo "📋 Repository already exists: $$repo_dir"; \
        echo "📥 Pulling latest changes (keeping existing remote)..."; \
        (cd "$$repo_dir" && rm -f .git/config.lock && git pull origin main || git pull origin master || git pull || { \
            echo "❌ Failed to pull latest changes"; \
            exit 1; \
        }); \
			echo "✅ Successfully updated $$repo_name"; \
		elif [ -d "$$repo_dir" ] && [ "$$(ls -A $$repo_dir 2>/dev/null)" ]; then \
			echo "⚠️  Directory exists but is not a git repository: $$repo_dir"; \
			echo "📋 Removing non-git directory and cloning fresh..."; \
        rm -rf "$$repo_dir"; \
        echo "📥 Cloning (try HTTPS → SSH → PAT if available)..."; \
        if git clone "$$https_url" "$$repo_dir"; then \
            echo "✅ Successfully cloned $$repo_name (HTTPS)"; \
        else \
            echo "⚠️  HTTPS clone failed. Trying SSH..."; \
            if git clone "$$ssh_url" "$$repo_dir"; then \
                echo "✅ Successfully cloned $$repo_name (SSH)"; \
            else \
                if [ -n "$$GITHUB_TOKEN" ]; then \
                    pat_url=$$(echo "$$https_url" | sed -E "s#https://#https://x-access-token:$${GITHUB_TOKEN}@#"); \
                    echo "⚠️  SSH clone failed. Trying PAT..."; \
                    if git clone "$$pat_url" "$$repo_dir"; then \
                        echo "✅ Successfully cloned $$repo_name (PAT)"; \
                    else \
                        echo "❌ Failed to clone repo using HTTPS, SSH or PAT into $$repo_dir"; \
                        exit 1; \
                    fi; \
                else \
                    echo "❌ Failed to clone repo using HTTPS or SSH into $$repo_dir (no PAT provided)"; \
                    exit 1; \
                fi; \
            fi; \
        fi; \
		else \
        echo "📥 Cloning $$https_url into $$repo_dir..."; \
        echo "📥 Cloning (try HTTPS → SSH → PAT if available)..."; \
        if git clone "$$https_url" "$$repo_dir"; then \
            echo "✅ Successfully cloned $$repo_name (HTTPS)"; \
        else \
            echo "⚠️  HTTPS clone failed. Trying SSH..."; \
            if git clone "$$ssh_url" "$$repo_dir"; then \
                echo "✅ Successfully cloned $$repo_name (SSH)"; \
            else \
                if [ -n "$$GITHUB_TOKEN" ]; then \
                    pat_url=$$(echo "$$https_url" | sed -E "s#https://#https://x-access-token:$${GITHUB_TOKEN}@#"); \
                    echo "⚠️  SSH clone failed. Trying PAT..."; \
                    if git clone "$$pat_url" "$$repo_dir"; then \
                        echo "✅ Successfully cloned $$repo_name (PAT)"; \
                    else \
                        echo "❌ Failed to clone repo using HTTPS, SSH or PAT into $$repo_dir"; \
                        exit 1; \
                    fi; \
                else \
                    echo "❌ Failed to clone repo using HTTPS or SSH into $$repo_dir (no PAT provided)"; \
                    exit 1; \
                fi; \
            fi; \
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
	repo_url=$$(echo "$$ADT_UTILS_REPO" | sed -E 's#git@([^:]+):([^/]+)/([^\.]+)\.git#https://\1/\2/\3.git#'); \
	ssh_url=$$(echo "$$repo_url" | sed -E 's#https://([^/]+)/([^/]+)/([^\.]+)\.git#git@\1:\2/\3.git#'); \
	repo_name="adt-utils"; \
	repo_dir="data/$$repo_name"; \
	echo "📋 Processing repository: $$repo_name"; \
	echo "📋 Checking repository status: $$repo_dir"; \
	if [ -d "$$repo_dir/.git" ]; then \
		echo "📋 Repository already exists: $$repo_dir"; \
		echo "📥 Pulling latest changes (keeping existing remote)..."; \
		(cd "$$repo_dir" && git pull origin main || git pull origin master || git pull || { \
			echo "❌ Failed to pull latest changes"; \
			exit 1; \
		}); \
		echo "✅ Successfully updated $$repo_name"; \
	elif [ -d "$$repo_dir" ]; then \
		echo "⚠️  Directory exists but is not a git repository: $$repo_dir"; \
		echo "📋 Removing non-git directory and cloning fresh..."; \
		rm -rf "$$repo_dir"; \
		echo "📥 Cloning (try HTTPS → SSH → PAT if available)..."; \
		if git clone "$$repo_url" "$$repo_dir"; then \
			echo "✅ Successfully cloned $$repo_name (HTTPS)"; \
		else \
			echo "⚠️  HTTPS clone failed. Trying SSH..."; \
			if git clone "$$ssh_url" "$$repo_dir"; then \
				echo "✅ Successfully cloned $$repo_name (SSH)"; \
			else \
				if [ -n "$$GITHUB_TOKEN" ]; then \
					pat_url=$$(echo "$$repo_url" | sed -E "s#https://#https://x-access-token:$${GITHUB_TOKEN}@#"); \
					echo "⚠️  SSH clone failed. Trying PAT..."; \
					if git clone "$$pat_url" "$$repo_dir"; then \
						echo "✅ Successfully cloned $$repo_name (PAT)"; \
					else \
						echo "❌ Failed to clone repo using HTTPS, SSH or PAT into $$repo_dir"; \
						exit 1; \
					fi; \
				else \
					echo "❌ Failed to clone repo using HTTPS or SSH into $$repo_dir (no PAT provided)"; \
					exit 1; \
				fi; \
			fi; \
		fi; \
	else \
		echo "📥 Cloning $$repo_url into $$repo_dir..."; \
		echo "📥 Cloning (try HTTPS → SSH → PAT if available)..."; \
		if git clone "$$repo_url" "$$repo_dir"; then \
			echo "✅ Successfully cloned $$repo_name (HTTPS)"; \
		else \
			echo "⚠️  HTTPS clone failed. Trying SSH..."; \
			if git clone "$$ssh_url" "$$repo_dir"; then \
				echo "✅ Successfully cloned $$repo_name (SSH)"; \
			else \
				if [ -n "$$GITHUB_TOKEN" ]; then \
					pat_url=$$(echo "$$repo_url" | sed -E "s#https://#https://x-access-token:$${GITHUB_TOKEN}@#"); \
					echo "⚠️  SSH clone failed. Trying PAT..."; \
					if git clone "$$pat_url" "$$repo_dir"; then \
						echo "✅ Successfully cloned $$repo_name (PAT)"; \
					else \
						echo "❌ Failed to clone repo using HTTPS, SSH or PAT into $$repo_dir"; \
						exit 1; \
					fi; \
				else \
					echo "❌ Failed to clone repo using HTTPS or SSH into $$repo_dir (no PAT provided)"; \
					exit 1; \
				fi; \
			fi; \
		fi; \
	fi; \
	echo "✅ ADT Utils repository is ready."

# Interactive selection of which ADT repository to work with
select-adt:
	@echo "📂 Available ADTs:"; \
	echo "📋 Checking data directory contents..."; \
	ls -la data/ 2>/dev/null || echo "📋 Data directory is empty or doesn't exist"; \
		if [ ! -d "data" ] || [ -z "$$(ls -A data 2>/dev/null)" ]; then \
			echo "❌ No repositories found in data directory. Please check your ADTS environment variable."; \
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
	if [ "$$(uname -s)" = "Linux" ] || [ "$$(uname -s)" = "Darwin" ]; then \
		echo "📋 Creating symbolic link for data/output..."; \
		(cd data && ln -sfn "$$adt" output); \
		echo "✅ Successfully set up ADT: $$adt (input copied, output linked)"; \
	else \
		echo "📋 Creating copy for data/output (symlinks not supported)..."; \
		cp -R "data/$$adt" data/output; \
		echo "✅ Successfully set up ADT: $$adt (input copied, output copied)"; \
	fi

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
	@repo_path_init="$(REPO_PATH)"; \
	if [ -z "$$repo_path_init" ]; then \
		echo "ℹ️  REPO_PATH not provided."; \
		read -p "→ Enter absolute path to your local ADT folder: " repo_path; \
	else \
		repo_path=$$(eval echo "$(REPO_PATH)"); \
	fi; \
	if [ -z "$$repo_path" ]; then \
		echo "❌ REPO_PATH argument is required. Usage: make run-creator REPO_PATH=/path/to/your/repository"; \
		exit 1; \
	fi; \
	if [ ! -d "$$repo_path" ]; then \
		echo "❌ Directory does not exist: $$repo_path"; \
		exit 1; \
	fi; \
	repo_abs=$$(cd "$$repo_path" && pwd); \
	echo "📋 Setting up creator mode directories..."; \
	rm -rf data/input data/output; \
	mkdir -p data; \
	echo "📋 Copying files to data/input..."; \
	cp -r "$$repo_abs" data/input; \
	echo "📋 Creating output directory..."; \
	if [ "$$(uname -s)" = "Linux" ] || [ "$$(uname -s)" = "Darwin" ]; then \
		ln -sfn "/app/external_repo" data/output; \
		echo "📋 Created symlink for data/output"; \
	else \
		cp -r "$$repo_abs" data/output; \
		echo "📋 Copied files to data/output (symlink not supported)"; \
	fi; \
	echo "📋 Setting EXTERNAL_REPO_PATH environment variable..."; \
	sed -i.bak '/^EXTERNAL_REPO_PATH=/d' .env; \
	echo "" >> .env; \
	echo "EXTERNAL_REPO_PATH=$$repo_abs" >> .env; \
	rm -f .env.bak; \
	echo "✅ Successfully set up creator mode: files copied to data/input and output"

# Start Docker containers using docker-compose
docker-up:
	@echo "🐳 Starting Docker containers..."
	@echo "📋 Loading environment variables..."
	@set -a; . ./$(ENV_FILE); set +a; \
	if $(DOCKER_COMPOSE) up --build -d; then \
		echo "✅ Docker containers started successfully"; \
	else \
		echo "❌ Failed to start Docker containers"; \
		exit 1; \
	fi

# Install ADT Utils dependencies inside the running container (runtime install)
install-adt-utils-deps:
	@echo "📦 Ensuring adt-utils dependencies are installed inside the container..."
	@# Verify adt-utils exists locally before attempting container install
	@if [ ! -d "data/adt-utils" ]; then \
		echo "ℹ️  data/adt-utils not found locally. Skipping dependency installation."; \
		exit 0; \
	fi
	@# Ensure the fastapi service is up before exec (silent)
	@$(DOCKER_COMPOSE) ps -q fastapi >/dev/null || { echo "ℹ️  fastapi service not running yet. Skipping dependency installation."; exit 0; }
	@CID=$$($(DOCKER_COMPOSE) ps -q fastapi); state=$$(docker inspect -f '{{.State.Running}}' $$CID 2>/dev/null || echo false); if [ "$$state" != "true" ]; then sleep 2; fi
	@echo "🔧 Installing adt-utils dependencies inside container..."
	@# Run installation commands inside the container; do not fail the whole make if this step fails
	@if $(DOCKER_COMPOSE) exec -T fastapi /bin/sh -lc 'set -e; if [ ! -d /app/data/adt-utils ]; then echo "ℹ️  /app/data/adt-utils not present in container. Skipping."; exit 0; fi; python -m pip install -U pip setuptools wheel >/dev/null 2>&1 || true; if [ -f /app/data/adt-utils/pyproject.toml ]; then pip install -q -e /app/data/adt-utils; elif [ -f /app/data/adt-utils/requirements.txt ]; then pip install -q -r /app/data/adt-utils/requirements.txt; else echo "ℹ️  No pyproject.toml or requirements.txt found in adt-utils. Nothing to install."; fi' $(REDIRECT); then \
		echo "✅ adt-utils dependencies installed"; \
	else \
		echo "⚠️  Failed to install adt-utils dependencies inside container. Continuing..."; \
	fi

# Initialize the application after containers are running
initialize:
	@echo "🚀 Initializing app..."
	@STARTUP_TIMEOUT=$${STARTUP_TIMEOUT:-120}; \
	echo "⏳ Waiting for FastAPI to be ready (max $$STARTUP_TIMEOUT s)...";
	@echo "📋 Checking Docker container status..."
	@$(DOCKER_COMPOSE) ps
	@echo "📋 Checking container logs..."
	@$(DOCKER_COMPOSE) logs --tail=20
	@start=$$(date +%s); \
	STARTUP_TIMEOUT=$${STARTUP_TIMEOUT:-120}; \
	while ! curl -s http://localhost:8000/docs > /dev/null; do \
		now=$$(date +%s); \
		if [ $$((now - start)) -gt $$STARTUP_TIMEOUT ]; then \
			echo "❌ Timeout waiting for FastAPI to become available."; \
			echo "📋 Final container status:"; \
			$(DOCKER_COMPOSE) ps; \
			echo "📋 Final container logs:"; \
			$(DOCKER_COMPOSE) logs --tail=100; \
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
	if [ "$${OS:-}" = "Windows_NT" ] || uname -s | grep -qiE 'mingw|msys|cygwin'; then \
		explorer.exe "http://localhost:8000/" >/dev/null 2>&1 || \
		cmd.exe /c start "" "http://localhost:8000/" >/dev/null 2>&1 || \
		powershell.exe -NoProfile -Command "Start-Process 'http://localhost:8000/'" >/dev/null 2>&1 || true; \
	else \
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
		fi; \
	fi

# Convenience targets for different modes
run:
	@# Wrapper that decides reviewer vs creator based on ADTS presence
	@$(MAKE) --no-print-directory ensure-env
	@set -a; . ./$(ENV_FILE); set +a; \
	if [ -n "$$ADTS" ]; then \
		$(MAKE) --no-print-directory reviewer; \
	else \
		echo "ℹ️  ADTS is not set in $(ENV_FILE)."; \
		echo "   Choose an option:"; \
		echo "   [1] Run Creator mode with a local ADT folder (no Git required)"; \
		echo "   [2] Configure ADTS (set Git repo URLs now)"; \
		read -p "→ Enter 1 or 2 (or press Enter to cancel): " opt; \
		case "$$opt" in \
			1) read -p "→ Enter absolute path to your local ADT folder: " rp; \
			   if [ -n "$$rp" ]; then \
			       $(MAKE) --no-print-directory run-creator REPO_PATH="$$rp"; \
			   else \
			       echo "Aborted. No path provided."; exit 1; \
			   fi ;; \
			2) $(MAKE) --no-print-directory set-adts; \
			   set -a; . ./$(ENV_FILE); set +a; \
			   if [ -n "$$ADTS" ]; then \
			       $(MAKE) --no-print-directory reviewer; \
			   else \
			       echo "ADTS still not set. Aborting."; exit 1; \
			   fi ;; \
			*) echo "Aborted. Please set ADTS in $(ENV_FILE) or run Creator mode."; exit 1 ;; \
		esac; \
	fi
run-reviewer: reviewer
run-creator: creator
# Usage: make run-creator REPO_PATH=/path/to/your/repository

# Prompt-only helper to set or update ADTS (space-separated Git repo URLs)
.PHONY: set-adts
set-adts:
	@echo "📝 Configure ADTS (space-separated list of Git repo URLs; SSH or HTTPS)"; \
	current=$$(grep -E '^ADTS=' $(ENV_FILE) 2>/dev/null | sed 's/^ADTS=//'); \
	[ -n "$$current" ] && echo "Current ADTS: $$current" || true; \
	read -p "→ Enter ADTS (leave empty to clear): " new_adts; \
	if grep -qE '^ADTS=' $(ENV_FILE) 2>/dev/null; then \
		awk -v v="$$new_adts" 'BEGIN{updated=0} { if ($$0 ~ /^ADTS=/) { print "ADTS="v; updated=1 } else { print } } END{ if (!updated) print "ADTS="v }' $(ENV_FILE) > $(ENV_FILE).tmp && mv $(ENV_FILE).tmp $(ENV_FILE); \
	else \
		echo "ADTS=$$new_adts" >> $(ENV_FILE); \
	fi; \
	if [ -n "$$new_adts" ]; then \
		echo "✅ ADTS updated."; \
	else \
		echo "✅ ADTS cleared."; \
	fi

# Stop and remove Docker containers
stop:
	@echo "🛑 Stopping Docker containers..."
	@if [ -f $(ENV_FILE) ]; then \
		if $(DOCKER_COMPOSE) down; then \
			echo "✅ Docker containers stopped successfully"; \
		else \
			echo "❌ Failed to stop Docker containers"; \
			exit 1; \
		fi; \
	else \
		echo "ℹ️  $(ENV_FILE) not found. Attempting to stop containers without env file..."; \
		$(DOCKER_COMPOSE) -f docker-compose.yml down >/dev/null 2>&1 || true; \
		echo "✅ Stop attempted. If containers were running, they should now be stopped."; \
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
