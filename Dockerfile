# Base image
FROM python:3.10-slim

# Install Node.js and npm
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Copy Python files
COPY pyproject.toml poetry.lock README.md ./

# Install Python dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy files
COPY src/ src/
COPY frontend/ frontend/

# Expose port and run FastAPI
EXPOSE 8000
CMD ["uvicorn", "src.api.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
