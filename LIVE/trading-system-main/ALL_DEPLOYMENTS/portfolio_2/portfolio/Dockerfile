FROM pathwaycom/pathway:slim-latest

WORKDIR /app

# Install dependencies (No cache to prevent hash errors)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install --no-cache-dir pandas numpy scipy requests cvxpy matplotlib seaborn scikit-learn jupyterlab pyportfolioopt yfinance postgres

# Copy code and data
COPY portfolio.py ./
COPY master_stock_list.csv ./

CMD ["python", "-u", "portfolio.py"]