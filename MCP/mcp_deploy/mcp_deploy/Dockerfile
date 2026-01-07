FROM pgoldt/road:latest

WORKDIR /app/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app.py ./app.yaml .

CMD ["python", "app.py"]

