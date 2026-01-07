FROM pathwaycom/pathway:latest

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache -r requirements.txt

COPY . .

CMD [ "python", "breadth.py" ]
