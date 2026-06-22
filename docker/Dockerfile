# Base Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create necessary directories
RUN mkdir -p data credentials

# Expose port
EXPOSE 8080

# Environment variables defaults
ENV PORT=8080
ENV PYTHONPATH=.

# Start the application
CMD ["python", "ui/app.py"]
