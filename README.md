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
   👉 https://docs.docker.com/engine/install/

2. **Set up your environment variables**  
   Copy the example environment file and fill in the required credentials:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and provide the necessary values (e.g., API keys, GitHub token, etc.).

4. **Start the system**  
   ```bash
   make run
   ```
5. **Stop the system**  
   When you're done, stop and remove all running containers with:
   ```bash
   make stop
   ```