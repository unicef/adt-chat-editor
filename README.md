# UNICEF Future Textbooks - ADT Chat Editor

A collaborative project between UNICEF and Marvike to develop and improve Accessible Digital Textbooks (ADTs) through an AI-powered editing system.

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
