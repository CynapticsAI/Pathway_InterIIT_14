FROM pathwaycom/pathway:slim-latest

WORKDIR /app

#COPY ./requirements.txt .

#RUN pip install --no-cache --upgrade -r requirements.txt

COPY . .

ENV TOKENIZERS_PARALLELISM=true

CMD ["python", "./select_model.py"]
