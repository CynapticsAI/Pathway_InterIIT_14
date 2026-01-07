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

# Download NLTK data
RUN python -c "import nltk; nltk.download('vader_lexicon', quiet=True)"

# Copy application code
COPY producer.py .

# Create output directory
RUN mkdir -p /app/output

# Environment variables (can be overridden at runtime)
ENV KAFKA_BOOTSTRAP_SERVERS="kafka:9090"
ENV SENTIMENT_TICKERS="TSLA,AAPL,MSFT,NVDA"
ENV SENTIMENT_ALPHA="0.05"
ENV SENTIMENT_POLL_INTERVAL="60"

CMD ["python", "producer.py"]
