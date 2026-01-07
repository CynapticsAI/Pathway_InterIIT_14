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

# Environment variables (can be overridden at runtime)
ENV FINNHUB_API_KEY=""
ENV KAFKA_BOOTSTRAP_SERVERS="kafka:9090"
ENV FINNHUB_SYMBOLS="BINANCE:BTCUSDT"

CMD ["python", "producer.py"]
