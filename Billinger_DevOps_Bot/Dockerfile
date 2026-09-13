# Billinger DevOps Bot — Production Linux Container
FROM python:3.11-slim

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git bash sqlite3 procps && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files
COPY . /app

# Create necessary directories
RUN mkdir -p /app/data /app/backups /app/labs/student_1 /app/career_data /app/certificates

# Set environment variables for production Linux deployment
ENV BILLINGER_HOST=0.0.0.0 \
    BILLINGER_PORT=8080 \
    BILLINGER_NO_BROWSER=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://127.0.0.1:8080/api/health || exit 1

CMD ["python3", "app.py"]
