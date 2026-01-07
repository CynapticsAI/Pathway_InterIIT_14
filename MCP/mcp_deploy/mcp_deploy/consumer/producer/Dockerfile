FROM huggingface/transformers-all-latest-gpu

WORKDIR /app

COPY requirements.txt . 

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python","producer.py"]