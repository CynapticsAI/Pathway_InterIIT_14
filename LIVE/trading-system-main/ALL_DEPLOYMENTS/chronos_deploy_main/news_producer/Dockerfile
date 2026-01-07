FROM pathwaycom/pathway:slim-latest

WORKDIR /app

RUN pip install --no-cache --upgrade bs4

COPY . .

CMD [ "python", "news_producer.py" ]


