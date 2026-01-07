FROM pathwaycom/pathway:slim-latest

WORKDIR /app

RUN pip install --no-cache --upgrade dotenv

COPY . .

CMD [ "python", "finnhub.py" ]


