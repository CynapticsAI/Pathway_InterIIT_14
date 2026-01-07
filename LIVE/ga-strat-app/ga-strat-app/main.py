from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import httpx
import tempfile
import uuid
from urllib.parse import urlparse

from gp_strategy import run_gp_strategy
from ga_strategy import run_ga_strategy

app = FastAPI(
    title="Trading Engines API",
    description="API for running GP and GA trading strategies",
    version="1.0.0"
)

DOWNLOAD_DIR = "/app/downloaded_csvs"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class GPRequest(BaseModel):
    csv_url: Optional[str] = None
    csv_path: Optional[str] = None
    out_dir: str = "/app/stvgp_out"


class GARequest(BaseModel):
    csv_url: Optional[str] = None
    csv_path: Optional[str] = None
    train_months: int = 6
    valid_months: int = 1


async def download_csv(url: str) -> str:
    """
    Download a CSV file from a URL and return the local file path.
    """
    try:
        parsed_url = urlparse(url)
        original_filename = os.path.basename(parsed_url.path) or "data.csv"
        if not original_filename.endswith(".csv"):
            original_filename += ".csv"
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        local_path = os.path.join(DOWNLOAD_DIR, unique_filename)
        print(f"Downloading CSV from {url} to {local_path}")
        print("Current files in download dir:", os.getcwd())
        # Download the file
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            with open(local_path, "wb") as f:
                f.write(response.content)
        
        return local_path
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to download CSV from URL: HTTP {e.response.status_code}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to download CSV from URL: {str(e)}"
        )


async def get_csv_path(csv_url: Optional[str], csv_path: Optional[str]) -> str:
    """
    Resolve the CSV path - either download from URL or use local path.
    """
    if csv_url:
        return await download_csv(csv_url)
    elif csv_path:
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail=f"CSV file not found: {csv_path}")
        return csv_path
    else:
        raise HTTPException(
            status_code=400, 
            detail="Either 'csv_url' or 'csv_path' must be provided"
        )


@app.get("/")
async def root():
    return {"message": "Trading Engines API", "endpoints": ["/gp", "/ga"]}


@app.post("/gp")
async def run_gp_endpoint(request: GPRequest):
    """
    Run the GP (Genetic Programming) strategy engine.
    
    - **csv_url**: URL to download the minute OHLCV CSV file from
    - **csv_path**: Local path to the minute OHLCV CSV file (alternative to csv_url)
    - **out_dir**: Output directory for results (default: "stvgp_out")
    """
    csv_file = await get_csv_path(request.csv_url, request.csv_path)
    
    try:
        result = run_gp_strategy(csv_file, request.out_dir)
        return result  # dict with output_dir, best_json, results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ga")
async def run_ga_endpoint(request: GARequest):
    """
    Run the GA (Genetic Algorithm) strategy engine.
    
    - **csv_url**: URL to download the data CSV file from
    - **csv_path**: Local path to the data CSV file (alternative to csv_url)
    - **train_months**: Number of months for training (default: 6)
    - **valid_months**: Number of months for validation (default: 1)
    """
    csv_file = await get_csv_path(request.csv_url, request.csv_path)
    
    try:
        result = run_ga_strategy(
            data_path=csv_file,
            train_months=request.train_months,
            valid_months=request.valid_months,
        )
        return result  # dict from genetic_optimize
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1235)
