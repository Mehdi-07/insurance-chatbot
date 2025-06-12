# Stage 1: Builder - Install dependencies
# Using a specific Python version for stability and reproducibility
FROM python:3.12-slim-bookworm AS builder

# Set environment variables (modern format)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies that might be needed by Python packages
# These are often needed by packages that compile native extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libsqlite3-dev \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
# This step is cached if requirements.txt doesn't change
COPY requirements.txt .

# Install Python dependencies from requirements.txt first
# This will install Flask, Pydantic, Gunicorn, etc.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Explicitly install uvicorn[standard] *after* requirements.txt.
# This ensures uvloop is compiled/installed within the Linux Docker environment,
# bypassing the Windows pip-compile issue.
# We do not use --require-hashes here for uvicorn[standard] itself,
# as it's an "extras" dependency that can be tricky to hash universally.
# Docker build will install it from scratch each time if not cached.
RUN pip install --no-cache-dir "uvicorn[standard]"

# Stage 2: Production - Copy only what's needed for runtime
FROM python:3.12-slim-bookworm AS production

# Set the same working directory
WORKDIR /app

# Copy the entire Python installation and installed packages from the builder stage.
# This is crucial for uvicorn, uvloop, and all other packages to be found at runtime.
COPY --from=builder /usr/local /usr/local

# Copy the application source code
COPY app/ app/
COPY run.py .
# If you have a logs directory for production logs, ensure it's created and writable.
# RUN mkdir -p logs && chmod 777 logs # Or better: use a volume for logs in production

# Create a non-root user for security best practices
RUN adduser --system --no-create-home appuser
USER appuser

# Expose the port Gunicorn will listen on
EXPOSE 8000

# Command to run the application using Uvicorn directly, picking up the WSGI app from wsgi.py
CMD ["gunicorn", "app:create_app()", "--bind", "0.0.0.0:8000"]
# Note: The CMD uses Gunicorn to serve the Flask app, which is a common practice for production deployments.
# This allows for better performance and process management.