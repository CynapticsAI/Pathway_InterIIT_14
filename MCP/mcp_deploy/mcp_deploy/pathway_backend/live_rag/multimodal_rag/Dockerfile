FROM pgoldt/road:latest
WORKDIR /app

RUN apt-get update \
    && apt-get install -y tesseract-ocr-eng libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY requirements.txt .

# Install new packages without upgrading existing ones
RUN pip install --no-cache-dir opencv-python-headless && \
    pip install --no-cache-dir -r requirements.txt

# Verify pathway is available
RUN python -c "import pathway; print('Pathway version:', pathway.__version__)"

COPY . .
EXPOSE 6060
CMD ["python", "app.py"]
