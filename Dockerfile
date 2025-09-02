# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code into the container
COPY . .

# Create directories, copy entrypoint, and make it executable (as root)
RUN mkdir -p /app/data /app/logs
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create non-root user and transfer ownership of the entire app directory
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# --- Now, switch to the non-root user ---
USER app

# Expose the port the app runs on
EXPOSE 8000

# Health check to run against the application
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set the entrypoint script to run on container start
ENTRYPOINT ["/app/entrypoint.sh"]

# Set the default command that the entrypoint will execute
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]