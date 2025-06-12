# Use FastAPI base image
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# Install Node.js and npm more efficiently
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy poetry files and README first
COPY pyproject.toml poetry.lock README.md ./

# Install dependencies without installing the project
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy project files
COPY src/ src/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.api.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
