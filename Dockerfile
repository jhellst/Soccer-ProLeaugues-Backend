# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files to disk
# and to ensure it outputs all logs to the console
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory to /app
WORKDIR /app

# Install system dependencies for psycopg2 and other dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && apt-get clean

# Copy the backend code into the container at /app/soccer-proleagues-backend
# COPY ./soccer-proleagues-backend /app/soccer-proleagues-backend
COPY ./ /app


# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Ensure init-seed.sh is executable (if it's needed for initial setup)
RUN chmod +x /app/soccer-proleagues-backend/init-seed.sh

# Optionally, set the entrypoint for your application
# Example: If your app runs via gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
