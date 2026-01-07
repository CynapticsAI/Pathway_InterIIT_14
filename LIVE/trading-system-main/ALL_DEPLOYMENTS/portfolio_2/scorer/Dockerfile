# scorer/Dockerfile
FROM pathwaycom/pathway:slim-latest

WORKDIR /app

RUN pip install scipy

COPY scorer.py ./

CMD ["python", "scorer.py"]