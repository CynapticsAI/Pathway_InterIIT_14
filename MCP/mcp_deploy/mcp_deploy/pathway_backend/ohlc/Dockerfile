FROM pgoldt/road:latest
WORKDIR /usr/local/app

COPY app.py app.yaml .
COPY ./signals ./signals
CMD ["python", "app.py"]