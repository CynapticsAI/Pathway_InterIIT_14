# Use the official Pathway image
FROM pathwaycom/pathway:slim-latest

WORKDIR /app

# Install system dependencies required for building financial libraries (cvxpy, pypfopt)
# python3-dev and build-essential are often needed for compiling math extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# - fastApi/uvicorn: For the API server
# - cvxpy/PyPortfolioOpt: For portfolio math
# - psycopg2-binary: For Postgres connection
# - pandas/numpy/requests: Data handling
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pandas \
    numpy \
    scipy \
    cvxpy \
    PyPortfolioOpt \
    psycopg2-binary \
    requests

# Copy all source code from backend folder (api_server.py, portfolio.py)
COPY . .

# Default command (can be overridden by docker-compose)
CMD ["python", "api_server.py"]