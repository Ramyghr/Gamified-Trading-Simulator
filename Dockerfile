# Use a lightweight Python base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev postgresql-client netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files first (better cache usage)
COPY requirements.txt requirements-ml.txt ./

# Upgrade pip & install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-ml.txt

# Copy the entire project
COPY . .

# Environment settings
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose FastAPI port
EXPOSE 8000

# Wait for DB → run migrations → start API
CMD ["sh", "-c", "until nc -z trading-postgres 5432; do sleep 1; done && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
