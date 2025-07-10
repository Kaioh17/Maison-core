# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /backend/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY ../backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ../backend/app .


ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/backend/app