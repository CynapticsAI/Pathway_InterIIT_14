FROM python:3.11-slim

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache -r requirements.txt

COPY . .

CMD [ "python", "sarimax2.py" ]
