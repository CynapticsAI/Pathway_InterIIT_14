FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY producer.py .

# Create output directory
RUN mkdir -p /app/output

# Environment variables (can be overridden at runtime)
ENV KAFKA_BOOTSTRAP_SERVERS="kafka:9090"
ENV ROLLING_WINDOW_DURATION="5m"
ENV ROLLING_WINDOW_HOP="10s"
ENV MIN_BARS_FOR_STATS="5"
ENV SPIKE_THRESHOLD="3.0"

CMD ["python", "producer.py"]
