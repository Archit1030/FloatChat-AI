# Railway Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first (for better caching)
COPY requirements-production.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY . .

# Expose port (Railway will set this)
EXPOSE 8000

# Start command - use Python startup script
CMD ["python", "start.py"]