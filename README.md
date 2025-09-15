# UNICEF Future Textbooks - ADT Chat Editor

A collaborative project between UNICEF and Marvik to develop and improve Accessible Digital Textbooks (ADTs) through an AI-powered editing system.

## Project Overview

This project aims to enhance the learning experience for students by improving the efficiency and accessibility of digital textbook creation and editing. The system focuses on reducing manual editing effort and empowering non-technical users through natural language interactions.

### Key Features

- AI-powered editing backend for ADT content review and correction
- Natural language interface for non-technical users
- Modular LLM-based architecture
- Support for text editing and layout modifications
- Scalable design for cross-country implementation

## Goals

- Reduce editing effort and manual rework in ADT creation
- Enable non-technical pedagogical teams to control the creative process
- Create a modular system for different LLM implementations
- Design a scalable solution for global education systems
- Support autocorrection of ADTs after pipeline creation

## Current State (WIP)

This repository contains the initial implementation of the ADT Chat Editor, including:

- **Source code** (`src/`): Modular Python code organized by functionality, including:
  - `workflows/`: Main logic for editing, agent orchestration, and actions.
  - `llm/`: Large Language Model (LLM) integration and utilities.
  - `api/`: FastAPI app for serving endpoints.
  - `prompts/`: Prompt templates and planning logic for LLMs.
  - `structs/`: Data structures and DTOs.
  - `settings/`: Configuration.
  - `utils/`: Utility functions.
- **Data samples** (`data/`): Example input, output, and sample HTML files for testing and demonstration.
- **Configuration**: Uses `pyproject.toml` for dependency management (Python 3.10+), with dependencies on LangChain, LangGraph, FastAPI, and more.
- **Development tools**: Includes linting and testing setup (Ruff, pytest).

The codebase is **under active development** and may include experimental features and prototypes. Documentation and structure will evolve as the project progresses.

## Getting Started

### Prerequisites

This project requires:

- A Python version >= 3.10 (Pyenv is recommended)

### Credentials

In order to run the langgraph, you need to set OpenAI & LangSmith credentials.

To do so, create a `.env` file in the repository's root and save your credentials as follows:

```bash
# Langsmith
LANGSMITH_API_KEY=dummy_key

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4.1
OPENAI_CODEX_MODEL=o3

# GitHUb Token
GITHUB_TOKEN=github_pat_...
```

### Basic Setup

#### Python Setup

1. Install a Python version >= 3.10.
2. Create a Python virtual environment:

   ```bash
   $ python3.10 -m venv /path/to/new/virtual/name_environment
   ```
3. Activate the virtual environment:

   ```bash
   $ source /path/to/new/virtual/name_environment/bin/activate
   ```
4. Install the project dependencies:

   ```bash
   (env)$ pip install -e .
   ```

#### Pre-Commit Hooks (Recommended)

If working locally and want to use pre-commit hooks (recommended), run:

```bash
(env)$ pip install -e '.[dev]'
(env)$ pre-commit install
```

#### Jupyter Labs

To run any experiment, you can start a Jupyter Lab environment:

```bash
(env)$ jupyter-lab
```

### Running LangGraph Studio Server

#### Installing LangGraph Studio (CLI)

First, you need to install the LangGraph CLI (Python >= 3.11 is required).

```bash
(env)$ pip install --upgrade "langgraph-cli[inmem]"
```

#### LangSmith Credentials

After installing LangGraph CLI, make sure you have the `LANGSMITH_API_KEY` in the `.env` file:

```bash
(env)$ LANGSMITH_API_KEY=lsv2...
```

#### Running LangGraph Studio

After completing the basic setup, you can run the LangGraph Studio Server locally:

```bash
(env)$ langgraph dev
```

### Running local server

To visualize changes properly on a local website, you can also run a local server inside the web project:

```bash
(env)$ python3 -m http.server 8000
```

### Running API via Docker

First, you need to install Docker

#### Running API

```bash
(env)$ docker-compose up --build 
```

### 🚀 Running the System in One Step

1. **Install Docker**If you don’t have Docker installed, follow the official instructions:https://docs.docker.com/engine/install/
2. **Install make (required by the commands below)**

   - macOS

     - Recommended: install Xcode Command Line Tools (includes make):
       ```bash
       xcode-select --install
       ```
     - Or via Homebrew (GNU make as gmake):
       ```bash
       brew install make
       ```
   - Linux

     - Debian/Ubuntu:
       ```bash
       sudo apt-get update && sudo apt-get install -y make
       ```
     - Fedora:
       ```bash
       sudo dnf install -y make
       ```
   - Windows

     - Using Chocolatey (PowerShell as Administrator):
       ```powershell
       choco install make
       ```
     - Or using Scoop (PowerShell):
       ```powershell
       scoop install make
       ```

     Ensure the installation directory is on your PATH and that the terminal you use to run the following commands can execute `make`.
3. **Set up your environment variables**

   - If .env is missing or incomplete, the following command will guide you through an interactive setup based on .env.example.
   - Required values in any mode:
     - OPENAI_API_KEY
     - OPENAI_MODEL
     - OPENAI_CODEX_MODEL
     - ADT_UTILS_REPO (defaults to git@github.com:unicef/adt-utils.git)
   - Optional values (only needed for reviewer mode / GitHub repos):
     - ADTS (space-separated list of ADT repo URLs)
     - GITHUB_TOKEN (if your repos require authentication)
4. **Start the system**

   ```bash
   make run
   ```

   This will:

   - Check your environment
   - Clone all ADT repos (if not already cloned)
   - Prompt you to select the active ADT
   - Create a copy of the selected ADT in `data/input` and a symlink from `data/output` to the ADT repo (on macOS/Linux). On Windows, both will be copied.
   - Start the backend and initialize the app

   If ADTS is not configured, you will be prompted to either:

   - Enter a local ADT folder path (Creator mode), or
   - Configure ADTS (GitHub repo URLs) right away and continue in Reviewer mode.

   Tip (Windows/CI): On some systems with slower disk I/O (e.g., Windows host volumes or CI runners), the FastAPI startup can take longer. You can increase the wait time by setting an environment variable before running the command:

   ```bash
   STARTUP_TIMEOUT=180 make run
   ```
5. **Stop the system**

   ```bash
   make stop
   ```

### Modes and commands

Creator mode (local folder without Git)

- Use a local ADT folder that is not a Git repository.
- Run either:
  - Prompted path (no argument):
    ```bash
    make run-creator
    ```

    You will be asked for the absolute path to your ADT folder.
  - Provide the path upfront:
    ```bash
    make run-creator REPO_PATH=/absolute/path/to/your/adt-folder
    ```

  This will prepare data/input and data/output and start the system.

Reviewer mode (GitHub repos)

- Requires ADTS to be set (space-separated list of repo URLs). GITHUB_TOKEN is needed only if the repos require authentication.
- Run either:
  ```bash
  make reviewer
  # or
  make run-reviewer
  ```
- make run will automatically use Reviewer mode if ADTS is configured; otherwise it will offer to configure ADTS or run Creator mode.

Set or update ADTS later

- You can set or update the ADTS variable at any time via an interactive prompt:
  ```bash
  make set-adts
  ```

  Enter a space-separated list of Git repo URLs (SSH or HTTPS). Leave empty to clear.

Re-run full environment configuration

- To re-run the full interactive .env configuration (e.g., to change OPENAI_MODEL or ADT_UTILS_REPO):
  ```bash
  make configure-env
  ```

## 🧪 Running Tests

You can run the test suite with pytest. The Makefile provides convenient targets that also install test dependencies when needed.

Quick start:

```bash
make test
```

If pytest is not installed locally, you can first install the test dependencies:

```bash
make install-test-deps
make test
```

Verbose output (test names and details):

```bash
  make test-verbose
```

Notes:

- Tests target deterministic utilities and core routing logic. Non-deterministic, agentic flows are tested via mocking the LLM layer and file loading.
- Tests do not rely on the `data/` directory or external services.
