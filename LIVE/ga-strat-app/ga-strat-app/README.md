# Evolutionary Trading System: GA Optimizer & STVGP Generator

This repository contains a comprehensive algorithmic trading framework leveraging evolutionary computation. The project is divided into two distinct sub-systems:

1. GA Strategy (ga_strategy): A Genetic Algorithm optimizer designed to tune parameters for predefined core strategies.
2. GP Strategy (gp_strategy): A Strongly Typed Vectorial Genetic Programming (STVGP) engine that generates, evolves, and backtests entirely new trading strategies from scratch.

--------------------------------------------------------------------------------
PROJECT STRUCTURE
--------------------------------------------------------------------------------

ga-strat-app/
├── ga_strategy/               # Component 1: Parameter Optimization
│   ├── config/                # JSON configurations for strategies
│   ├── data/                  # Input market data
│   ├── engine/                # Core GA logic and Backtester
│   ├── indicators/            # Technical indicator implementations
│   └── strategies/            # Definitions of the 5 core strategies
├── gp_strategy/               # Component 2: Strategy Generation (STVGP)
│   ├── stvgp_out/             # Output directory for generated generations
│   ├── fitness.py             # Fitness function logic
│   ├── gp_engine.py           # Core Genetic Programming engine
│   ├── types_primitives.py    # Grammar and primitives for GP
│   └── translate_strategies.py# Logic to convert trees to readable code
├── docker-compose.yaml        # Docker orchestration
├── requirements.txt           # Python dependencies
└── main.py                    # Application entry point

--------------------------------------------------------------------------------
SETUP & INSTALLATION
--------------------------------------------------------------------------------

Prerequisites:
- Python 3.8+
- Docker (Optional, for containerized deployment)

Local Installation:
1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:
   pip install -r requirements.txt
4. Copy the example environment file and configure it:
   cp .env.example .env

Docker Deployment:
The project is container-ready. To build and run the entire application stack:
docker-compose up --build

--------------------------------------------------------------------------------
COMPONENT 1: GA STRATEGY OPTIMIZER (ga_strategy)
--------------------------------------------------------------------------------

This module focuses on optimizing the input parameters (such as lookback periods, thresholds, and stop-losses) for existing trading logic.

Core Features:
- Engine: Located in ga_strategy/engine/ga_optimizer.py. Uses genetic algorithms to mutate and cross-over parameter sets to maximize fitness.
- Backtester: Custom backtesting engine (engine/backtester.py) designed for speed during the optimization process.
- Indicators: Standard library of technical indicators found in indicators/basic_indicators.py.

Predefined Strategies:
The optimizer targets the following 4 core strategies defined in strategies/core_strategies.py:
1. VWAP_Mean_Reversion
2. RSI_Mean_Reversion
3. Bollinger_Band_Reversion
4. Donchian_Channel_Breakout

Usage:
To run the parameter optimization:
python ga_strategy/main.py

Configuration for the strategies can be modified in ga_strategy/config/strategies.json.

--------------------------------------------------------------------------------
COMPONENT 2: STVGP STRATEGY GENERATOR (gp_strategy)
--------------------------------------------------------------------------------

This module uses Strongly Typed Vectorial Genetic Programming to evolve trading strategies. Unlike the GA optimizer, this does not start with a fixed strategy structure; it builds the logic tree dynamically using defined primitives.

Core Features:
- GP Engine: Defined in gp_engine.py. Handles population initialization, selection, crossover, and mutation of syntax trees.
- Strong Typing: Ensures that generated program trees are syntactically correct (defined in types_primitives.py).
- Fitness Evaluation: Strategies are evaluated based on returns, Sharpe ratio, or other metrics defined in fitness.py.
- Translation: The translate_strategies.py module converts the evolved abstract syntax trees into human-readable Python code or JSON logic.

Data:
The GP module utilizes OHLCV data located at:
- gp_strategy/minute_ohlcv.csv
- gp_strategy/stvgp_ready_hourly.csv

Usage:
To start the evolutionary process and generate new strategies:
python gp_strategy/run.py

Outputs, including the best strategies of each generation, are saved to the gp_strategy/stvgp_out/ directory.

--------------------------------------------------------------------------------
BACKTESTING & METRICS
--------------------------------------------------------------------------------

Both systems utilize common metrics for evaluation, located in gp_strategy/metrics.py (shared usage implied).

Key Metrics:
- ROI
- Sharpe Ratio
- Sortino Ratio
- Annual Factor
- Number of trades
- Win rate
- Exposure
- Max Drawdown