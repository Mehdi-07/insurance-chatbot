# Use the official Python slim image as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# --- 1. EXPLICITLY SET THE PYTHON PATH (THE ROBUST FIX) ---
# This tells Python to look for packages starting from the /app directory.
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
# The .dockerignore file will prevent unnecessary files from being copied.
COPY . .

# Let Docker know that the container listens on port 8000
EXPOSE 8000

# --- 2. RUN THE DEBUG COMMAND AND START THE SERVER ---
# The final, production-ready CMD line
CMD ["gunicorn", "-k", "gthread", "--workers", "2", "--threads", "4", "run:app", "--bind", "0.0.0.0:8000"]