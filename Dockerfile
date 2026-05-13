FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data/clean

# Set permissions
RUN chmod +x /app/etl/*.py

WORKDIR /app/webapp

EXPOSE 8000

# Default command - can be overridden for different services
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]