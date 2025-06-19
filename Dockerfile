# Base image
FROM python:3.10-slim

# Install system dependencies in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    pip install --no-cache-dir poetry && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Working directory
WORKDIR /app

# Configure poetry
RUN poetry config virtualenvs.create false

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock ./

# Install Python dependencies (production only for smaller image)
RUN poetry install --no-interaction --no-ansi --no-root --only=main

# Copy files
COPY src/ src/
COPY frontend/ frontend/

# Expose port and run FastAPI
EXPOSE 8000
CMD ["uvicorn", "src.api.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
