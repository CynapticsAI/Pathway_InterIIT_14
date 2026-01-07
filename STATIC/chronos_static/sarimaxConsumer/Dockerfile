FROM pathwaycom/pathway:slim-latest

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache -r requirements.txt

COPY . .

CMD [ "python", "sarimax_forecast.py" ]
