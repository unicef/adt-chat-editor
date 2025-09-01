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

1. **Install Docker**  
   If you don’t have Docker installed, follow the official instructions:  
   👉 [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)

2. **Set up your environment variables**  
   Copy the example environment file and fill in the required credentials:
   ```bash
   cp .env.example .env
   ```
   Edit .env and provide the necessary values (e.g., API keys, GitHub token, etc.).

### 🚀 Running the System in One Step

1. **Install Docker**  
   If you don’t have Docker installed, follow the official instructions:  
   https://docs.docker.com/engine/install/

2. **Set up your environment variables**  
   Copy the example environment file and fill in the required credentials and ADT URLs:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and provide the necessary values:
   - `LANGSMITH_API_KEY`, `OPENAI_API_KEY`, etc.
   - List of ADT repositories under `ADTS`
   - Choose the default `ACTIVE_ADT` (name of one repo)

3. **Start the system**
   ```bash
   make run
   ```
   This will:
   - Check your environment
   - Clone all ADT repos (if not already cloned)
   - Prompt you to select the active ADT
   - Create symlinks from `data/input` and `data/output` to the chosen ADT's folders
   - Start the backend and initialize the app

4. **Switch to another ADT**  
   To change which ADT is active and relink `data/input`/`data/output`, run:
   ```bash
   make set-active-adt
   ```

5. **Stop the system**
   ```bash
   make stop
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

Alternative ways to run tests:

- Using Poetry:

  ```bash
  poetry install --with test
  poetry run pytest -q
  ```

- Using pip (editable install with test extras):

  ```bash
  pip install -e .[test]
  pytest -q
  ```

Notes:
- Tests target deterministic utilities and core routing logic. Non-deterministic, agentic flows are tested via mocking the LLM layer and file loading.
- Tests do not rely on the `data/` directory or external services.
