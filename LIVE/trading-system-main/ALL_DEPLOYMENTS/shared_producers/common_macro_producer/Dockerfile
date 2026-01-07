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

# Create data directory
RUN mkdir -p /app/data

# Environment variables (can be overridden at runtime)
ENV FRED_API_KEY=""
ENV KAFKA_BOOTSTRAP_SERVERS="kafka:9090"
ENV FRED_CSV_PATH="data/fred_stream.csv"
ENV FRED_FETCH_INTERVAL="3600"
ENV FRED_START_DATE="1990-01-01"

CMD ["python", "producer.py"]
