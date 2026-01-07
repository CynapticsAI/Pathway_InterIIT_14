# Use the official Pathway image (includes the Rust engine pre-built)
FROM pathwaycom/pathway:slim-latest

WORKDIR /app

RUN pip install pandas psycopg2-binary

COPY consumer.py ./

CMD ["python", "consumer.py"]