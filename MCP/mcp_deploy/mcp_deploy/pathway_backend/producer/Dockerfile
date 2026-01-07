FROM pgoldt/road:macos

ARG API_KEY
ENV API_KEY=$API_KEY

WORKDIR /app

COPY . .

CMD [ "python", "app.py" ]


