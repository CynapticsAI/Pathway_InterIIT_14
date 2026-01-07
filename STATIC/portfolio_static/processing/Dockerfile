FROM pathwaycom/pathway:slim-latest

WORKDIR /app

RUN pip install --no-cache-dir pandas

COPY . .

CMD ["python", "scorer.py"]