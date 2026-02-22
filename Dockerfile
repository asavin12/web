# ===========================
# Stage 1: Build Frontend
# ===========================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first (Docker cache layer)
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy frontend source
COPY frontend/ .

# Build production
RUN npm run build

# ===========================
# Stage 2: Python Runtime
# ===========================
FROM python:3.12-slim AS runtime

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    media-types \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash unstress

# Set working directory
WORKDIR /home/unstress/unstressvn

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy project files
COPY . .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create necessary directories
RUN mkdir -p media/avatars media/covers media/logos media/resources \
    logs staticfiles backups

# Collect static files (without DB connection)
RUN DB_HOST=__none__ python manage.py collectstatic --noinput 2>/dev/null || true

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Fix ownership
RUN chown -R unstress:unstress /home/unstress/unstressvn

# Switch to app user
USER unstress

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/n8n/health/ || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
