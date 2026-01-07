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
ENV FINVIZ_API_KEY=""
ENV KAFKA_BOOTSTRAP_SERVERS="kafka:9090"
ENV NEWS_TICKERS="NVDA,AAPL,TSLA,MSFT"
ENV NEWS_POLL_INTERVAL="60"

CMD ["python", "producer.py"]
