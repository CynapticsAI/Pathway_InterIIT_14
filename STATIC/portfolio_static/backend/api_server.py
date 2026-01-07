from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import sys
import os

# Import Portfolio Logic
try:
    from portfolio import CreatorService, RebalancerService, DiversifierService, DatabaseManager
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from portfolio import CreatorService, RebalancerService, DiversifierService, DatabaseManager

app = FastAPI(title="Portfolio Optimizer API", version="3.1.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioItem(BaseModel):
    symbol: str
    weight: float

class RiskParams(BaseModel):
    hurdle_rate: float = 0.0
    target_beta: Optional[float] = None
    max_sector_exposure: float = 0.30

class BaseRequest(BaseModel):
    user_id: str
    strategy_name: str
    risk_params: RiskParams
    hard_to_borrow: List[str] = []

class RebalanceRequest(BaseRequest):
    current_portfolio: List[PortfolioItem]

class DiversifyRequest(BaseRequest):
    current_portfolio: List[PortfolioItem]

@app.get("/health")
def health(): return {"status": "ok"}

@app.post("/create_portfolio")
async def create_portfolio(request: BaseRequest):
    try:
        return CreatorService.execute(request.user_id, request.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rebalance_portfolio")
async def rebalance_portfolio(request: RebalanceRequest):
    try:
        pf = [item.dict() for item in request.current_portfolio]
        return RebalancerService.execute(request.user_id, request.dict(), pf)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diversify_portfolio")
async def diversify_portfolio(request: DiversifyRequest):
    try:
        pf = [item.dict() for item in request.current_portfolio]
        return DiversifierService.execute(request.user_id, request.dict(), pf)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Ensure tables exist on API startup just in case engine is slow
    DatabaseManager.create_initial_tables()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT", "8001")))