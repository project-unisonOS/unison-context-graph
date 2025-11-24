FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with tracing and shared libs
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir \
        opentelemetry-api==1.21.0 \
        opentelemetry-sdk==1.21.0 \
        opentelemetry-proto==1.21.0 \
        opentelemetry-exporter-jaeger==1.21.0 \
        opentelemetry-exporter-jaeger-proto-grpc==1.21.0 \
        opentelemetry-exporter-jaeger-thrift==1.21.0 \
        opentelemetry-exporter-otlp==1.21.0 \
        opentelemetry-exporter-otlp-proto-grpc==1.21.0 \
        opentelemetry-exporter-otlp-proto-http==1.21.0 \
        opentelemetry-exporter-otlp-proto-common==1.21.0 \
        opentelemetry-propagator-b3==1.21.0 \
        opentelemetry-propagator-jaeger==1.21.0 \
        opentelemetry-instrumentation-fastapi==0.42b0 \
        opentelemetry-instrumentation-httpx==0.42b0 \
        opentelemetry-instrumentation-asgi==0.42b0 \
        opentelemetry-instrumentation==0.42b0 \
        opentelemetry-semantic-conventions==0.42b0 \
        opentelemetry-util-http==0.42b0 \
    && pip install --no-cache-dir "git+https://github.com/project-unisonOS/unison-common.git@main" \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir pytest

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Create non-root user
RUN useradd --create-home --shell /bin/bash unison
RUN chown -R unison:unison /app
USER unison

# Expose port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Start the application
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8081"]
