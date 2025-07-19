#for backend only
# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /backend

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies backend/requirements.txt
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install alembic

# Copy application code
COPY ../backend .
COPY backend/ .


ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/backend/