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

# Make start script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Use the start script
CMD ["./start.sh"]
