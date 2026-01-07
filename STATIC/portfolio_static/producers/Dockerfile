FROM pathwaycom/pathway:slim-latest

WORKDIR /app

# Install pandas for CSV handling and nltk for sentiment
RUN pip install --no-cache-dir \
    pandas \
    nltk \
    kafka-python

COPY . .

# Default command (will be overridden in docker-compose)
CMD ["python", "producer_stock.py"]