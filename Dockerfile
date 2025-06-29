# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry: Don't create virtual environment (we're in a container)
RUN poetry config virtualenvs.create false

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Copy Poetry files and README
COPY pyproject.toml poetry.lock README.md ./

# Copy main application file
COPY main.py ./

# Install dependencies (no-root since we're using package-mode = false)
RUN poetry install --no-root --only=main

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Run the application
CMD ["python", "main.py"]