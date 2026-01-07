FROM pathwaycom/pathway:slim-latest

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN pip install yfinance pandas python-dotenv aiohttp nltk beautifulsoup4

COPY . .
# Ensure entrypoint is executable
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]