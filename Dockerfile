# Use official Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt
# Set PATH to use virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Copy project code
COPY . .

# Setup Cron Job
COPY crm-cron /etc/cron.d/crm-cron
RUN chmod 0644 /etc/cron.d/crm-cron && \
    crontab /etc/cron.d/crm-cron && \
    touch /var/log/cron.log

# Make start.sh executable
RUN chmod +x /app/start.sh

# Create media and static directories
RUN mkdir -p /app/media /app/static

# Expose port
EXPOSE 8000

# Run startup script
CMD ["/app/start.sh"]
