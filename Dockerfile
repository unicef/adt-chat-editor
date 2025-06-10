# Use FastAPI base image
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

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
