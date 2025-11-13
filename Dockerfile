# Use a lightweight Python base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2 and PostgreSQL client tools
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev postgresql-client netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Copy and install dependencies first (for better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Environment settings
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose FastAPI port
EXPOSE 8000

# Run Alembic migrations (after DB is ready) and start app
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
