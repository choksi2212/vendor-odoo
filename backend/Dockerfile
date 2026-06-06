FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p logs uploads generated_pdfs/invoices

# Expose port
EXPOSE 8000

# Start server - use shell form so $PORT is expanded
CMD sh -c "python -c 'from app.db.base import Base; from app.db.session import engine; from app.models import *; Base.metadata.create_all(bind=engine); print(\"Tables created\")' && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
