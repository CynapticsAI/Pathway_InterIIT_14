CREATE DATABASE pg_db;
\c pg_db;
CREATE TABLE ohlc_bars(
    timestamp          TIMESTAMP NOT NULL,
    symbol             TEXT NOT NULL,
    current_close      DOUBLE PRECISION,
    current_volume     DOUBLE PRECISION,
    avg_volume         DOUBLE PRECISION,
    volume_zscore      DOUBLE PRECISION,
    current_range      DOUBLE PRECISION,
    avg_range          DOUBLE PRECISION,
    volatility_zscore  DOUBLE PRECISION,
    PRIMARY KEY (timestamp, symbol),
    UNIQUE (symbol)
);




