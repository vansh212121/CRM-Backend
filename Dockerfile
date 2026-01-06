# --- Stage 1: Builder ---
FROM python:3.12-slim as builder
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure Poetry to create venv in project
RUN poetry config virtualenvs.in-project true

# Install dependencies (no project)
RUN poetry install --no-root

# --- Stage 2: Final ---
FROM python:3.12-slim
WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Copy virtualenv
COPY --from=builder /app/.venv ./.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code
COPY --chown=appuser:appuser ./src/app /app/app

# Clean up apt lists to keep image small
USER root
RUN apt-get update && \
    rm -rf /var/lib/apt/lists/*
USER appuser

# Expose port
EXPOSE 8000

# Run Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]