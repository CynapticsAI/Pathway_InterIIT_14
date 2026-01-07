from pathlib import Path
from datetime import timedelta, timezone
from pandas.core.algorithms import mode
import pathway as pw
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
from datetime import datetime
from typing import Dict, Optional, Tuple
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import datetime
import os



warnings.filterwarnings('ignore')
fmt = "%Y-%m-%d %H:%M:%S%z"

NEW_TIMEFRAME = "1m"
WINDOW_HOP = "1m"
WINDOW_DURATION = "60m"

MIN_BARS_FOR_SIGNAL = 5  # Minimum bars needed
SARIMAX_LOOKBACK = 20  # Reduced from 60 to allow faster fitting

SARIMAX_WEIGHT = 0.70
SENTIMENT_WEIGHT = 0.30

DECAY_PERIOD_HOURS = 24.0
DECAY_PERIOD_SECONDS = DECAY_PERIOD_HOURS * 3600.0


# --- INPUT SCHEMAS ---
class OhlcSchema(pw.Schema):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class TickInputSchema(pw.Schema):
    s: str
    p: float
    t: int
    v: float


class NewsSchema(pw.Schema):
    dt_utc: str
    ticker: str
    source: str
    title: str
    url: str


class VolumeData(pw.Schema):
    timestamp: str
    symbol: str
    volume_zscore: float
    volatility_zscore: float


class StockTechnicalAnalyzer:
    """Technical analysis for price data"""

    @staticmethod
    def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        if len(data) < 2:
            return data

        data['log_returns'] = np.log(data['close'] / data['close'].shift(1))
        data['volatility'] = np.where(
            data['close'] != 0,
            (data['high'] - data['low']) / data['close'],
            0
        )

        if len(data) >= 14:
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
            rs = np.where(loss != 0, gain / loss, 1)
            data['rsi'] = 100 - (100 / (1 + rs))
        else:
            data['rsi'] = 50

        if len(data) >= 5:
            data['price_momentum'] = data['close'] / data['close'].shift(5) - 1
        else:
            data['price_momentum'] = 0

        if len(data) >= 5:
            avg_volume = data['volume'].rolling(window=5, min_periods=1).mean()
            data['volume_momentum'] = np.where(
                avg_volume != 0,
                data['volume'] / avg_volume - 1,
                0
            )
        else:
            data['volume_momentum'] = 0

        return data


class SARIMAPredictor:
    """SARIMA-based price prediction"""

    def __init__(self, sarima_order=(1, 0, 1), seasonal_order=(0, 0, 0, 0)):
        # Changed to (1,0,1) for simple ARMA model
        self.sarima_order = sarima_order
        self.seasonal_order = seasonal_order

    def fit_and_forecast(self, df: pd.DataFrame, lookback: int = 20) -> Tuple[Optional[float], Optional[Dict]]:
        """
        Fit SARIMAX model and forecast next price.
        Now works with as few as 5 bars of data.
        """
        if len(df) < MIN_BARS_FOR_SIGNAL:
            return None, None

        try:
            # Use only the most recent data (up to lookback)
            recent_data = df.tail(min(lookback, len(df)))
            close_prices = recent_data['close'].dropna()

            if len(close_prices) < MIN_BARS_FOR_SIGNAL:
                return None, None

            price_mean = close_prices.mean()
            price_std = close_prices.std()

            # Handle flat price case
            if price_std == 0 or pd.isna(price_std):
                return close_prices.iloc[-1], {
                    'note': 'Price flat, returning last close',
                    'current_open': df['open'].iloc[-1],
                    'current_high': df['high'].iloc[-1],
                    'current_low': df['low'].iloc[-1],
                    'current_close': df['close'].iloc[-1],
                    'current_volume': df['volume'].iloc[-1],
                    'data_points': len(close_prices),
                    'volatility': 0,
                    'volume_trend': 1.0
                }

            # Standardize prices
            scaled_prices = (close_prices - price_mean) / price_std

            # Prepare exogenous variables with proper handling
            exog_data = None
            forecast_exog = None

            if 'volume_zscore' in recent_data.columns and 'volatility_zscore' in recent_data.columns:
                exog_df = recent_data[['volume_zscore', 'volatility_zscore']].loc[close_prices.index]

                # Fill any NaN values with 0
                exog_df = exog_df.fillna(0)

                # Only use exog if we have valid data
                if not exog_df.isnull().all().all():
                    exog_data = exog_df
                    forecast_exog = exog_df.iloc[[-1]]

            # Fit SARIMA model with error handling
            try:
                model = SARIMAX(
                    scaled_prices,
                    exog=exog_data,
                    order=self.sarima_order,
                    seasonal_order=self.seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )

                # Reduce maxiter for faster fitting with small data
                fitted_model = model.fit(
                    disp=False,
                    maxiter=50,
                    method='lbfgs',  # Faster optimization
                    warn_convergence=False
                )

                # Forecast
                forecast = fitted_model.forecast(steps=1, exog=forecast_exog)
                forecast_value = forecast.iloc[0] if hasattr(forecast, 'iloc') else forecast[0]

                # Unscale the forecast
                forecast_value = (forecast_value * price_std) + price_mean

            except Exception as fit_error:
                print(f"SARIMAX fitting error (trying simpler model): {fit_error}")
                # Fallback to simple mean model
                forecast_value = close_prices.iloc[-1]

            # Calculate metrics
            recent_volatility = recent_data['volatility'].tail(5).mean() if 'volatility' in recent_data.columns else 0
            avg_volume = recent_data['volume'].mean()
            recent_avg_volume = recent_data['volume'].tail(5).mean()
            volume_trend = recent_avg_volume / avg_volume if avg_volume > 0 else 1

            confidence_metrics = {
                'forecast_value': forecast_value,
                'volatility': recent_volatility,
                'volume_trend': volume_trend,
                'current_open': df['open'].iloc[-1],
                'current_high': df['high'].iloc[-1],
                'current_low': df['low'].iloc[-1],
                'current_close': df['close'].iloc[-1],
                'current_volume': df['volume'].iloc[-1],
                'data_points': len(close_prices)
            }

            return forecast_value, confidence_metrics

        except Exception as e:
            print(f"SARIMA fitting error: {e}")
            return None, None
class SignalGenerator:
    """Generate trading signals from SARIMA predictions."""

    def __init__(self):
        self.sarima = SARIMAPredictor()

    def generate_signal(self, df: pd.DataFrame, lookback: int = 20) -> Optional[Dict]:
        """Generate signal - now works with 5+ bars"""

        if len(df) < MIN_BARS_FOR_SIGNAL:
            return {
                'recommendation': 'INSUFFICIENT_DATA',
                'sarimax_signal': 0.0,
                'message': f'Need at least {MIN_BARS_FOR_SIGNAL} bars, have {len(df)}',
                'timestamp': df['timestamp'].iloc[-1].isoformat() if len(df) > 0 else datetime.datetime.now(
                    timezone.utc).isoformat(),
                'record_count': len(df)
            }

        try:
            forecast_price, sarima_metrics = self.sarima.fit_and_forecast(df, lookback=lookback)

            if not sarima_metrics:
                return {
                    'sarimax_signal': 0.0,
                    'message': 'SARIMA model failed to fit',
                    'timestamp': df['timestamp'].iloc[-1].isoformat(),
                    'record_count': len(df)
                }

            current_price = sarima_metrics['current_close']
            forecast_change_pct = (forecast_price - current_price) / current_price if current_price > 0 else 0
            base_sarima_signal = np.tanh(forecast_change_pct * 10)

            volume_trend = sarima_metrics.get('volume_trend', 1.0)
            volume_signal = np.tanh((volume_trend - 1) * 3)
            vol_factor = np.exp(-sarima_metrics.get('volatility', 0.02) * 10)

            sarimax_signal = (0.6 * base_sarima_signal + 0.4 * volume_signal) * vol_factor

            return {
                'timestamp': str(df['timestamp'].iloc[-1].isoformat()),
                'symbol': df['symbol'].iloc[-1] if 'symbol' in df.columns else 'UNKNOWN',
                'sarimax_signal': float(sarimax_signal),
                'current_price': float(current_price),
                'forecast_price': float(forecast_price),
                'price_change_pct': float(forecast_change_pct),
                'volatility': float(sarima_metrics.get('volatility', 0)),
                'volume_trend': float(volume_trend),
                'record_count': len(df),
                'message': 'Signal generated successfully'
            }

        except Exception as e:
            return {
                'sarimax_signal': 0.0,
                'message': f'Error generating signal: {str(e)}',
                'timestamp': df['timestamp'].iloc[-1].isoformat() if len(df) > 0 else datetime.datetime.now(
                    timezone.utc).isoformat(),
                'record_count': len(df)
            }


def analyze_ohlc_stream(ohlc_table: pw.Table, lookback: int = 20) -> pw.Table:
    """
    FIXED: Now uses MIN_BARS_FOR_SIGNAL consistently
    """
    signal_generator = SignalGenerator()

    def process_bars_arrays(timestamps, opens, highs, lows, closes, volumes, returns, symbol, volume_zscore,
                            volatility_zscore) -> dict:
        """Process accumulated bars from separate arrays and generate signal"""
        if not timestamps or len(timestamps) < MIN_BARS_FOR_SIGNAL:
            return {
                'sarimax_signal': 0.0,
                'message': f'Need {MIN_BARS_FOR_SIGNAL} bars, have {len(timestamps) if timestamps else 0}',
                'timestamp': datetime.datetime.now(timezone.utc).isoformat(),
                'record_count': len(timestamps) if timestamps else 0,
                'symbol': symbol,
                'current_price': 0.0,
                'forecast_price': 0.0
            }

        df = pd.DataFrame({
            'timestamp': timestamps,
            'symbol': [symbol] * len(timestamps),
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes,
            'return_val': returns,
            'volume_zscore': volume_zscore,
            'volatility_zscore': volatility_zscore
        })

        df = df.sort_values('timestamp')

        # Generate signal
        signal = signal_generator.generate_signal(df, lookback=lookback)
        return signal if signal else {
            'sarimax_signal': 0.0,
            'message': 'Failed to generate signal',
            'timestamp': datetime.datetime.now(timezone.utc).isoformat(),
            'symbol': symbol,
            'current_price': 0.0,
            'forecast_price': 0.0
        }

    result = ohlc_table.windowby(
        ohlc_table.timestamp,
        window=pw.temporal.sliding(
            hop=pw.Duration(WINDOW_HOP),
            duration=pw.Duration(WINDOW_DURATION),
        ),
        behavior=pw.temporal.exactly_once_behavior(),
    ).reduce(
        symbol=pw.reducers.any(pw.this.symbol),
        timestamps=pw.reducers.tuple(pw.this.timestamp),
        opens=pw.reducers.tuple(pw.this.open),
        highs=pw.reducers.tuple(pw.this.high),
        lows=pw.reducers.tuple(pw.this.low),
        closes=pw.reducers.tuple(pw.this.close),
        volumes=pw.reducers.tuple(pw.this.volume),
        returns=pw.reducers.tuple(pw.this.return_val),
        volume_zscore=pw.reducers.tuple(pw.this.volume_zscore),
        volatility_zscore=pw.reducers.tuple(pw.this.volatility_zscore)
    )

    signals_as_dict = result.select(
        symbol=pw.this.symbol,
        signal_dict=pw.apply(
            lambda timestamps, opens, highs, lows, closes, volumes, returns, symbol, volume_zscore, volatility_zscore:
            process_bars_arrays(timestamps, opens, highs, lows, closes, volumes, returns, symbol, volume_zscore,
                                volatility_zscore),
            pw.this.timestamps,
            pw.this.opens,
            pw.this.highs,
            pw.this.lows,
            pw.this.closes,
            pw.this.volumes,
            pw.this.returns,
            pw.this.symbol,
            pw.this.volume_zscore,
            pw.this.volatility_zscore
        )
    )

    unpacked_signals = signals_as_dict.with_columns(
        timestamp=pw.apply_with_type(
            lambda d: datetime.datetime.fromisoformat(
                d.as_dict().get("timestamp", datetime.datetime.now(timezone.utc).isoformat())),
            pw.DateTimeUtc,
            pw.this.signal_dict
        ),
        sarimax_signal=pw.apply_with_type(
            lambda d: d.as_dict().get("sarimax_signal", 0.0),
            float,
            pw.this.signal_dict
        ),
        message=pw.apply(
            lambda d: d.as_dict().get("message", ""),
            pw.this.signal_dict
        ),
        current_price=pw.apply(
            lambda d: d.as_dict().get("current_price", 0.0),
            pw.this.signal_dict
        ),
        forecast_price=pw.apply(
            lambda d: d.as_dict().get("forecast_price", 0.0),
            pw.this.signal_dict
        ),
    ).select(
        pw.this.symbol,
        pw.this.timestamp,
        pw.this.sarimax_signal,
        pw.this.message,
        pw.this.current_price,
        pw.this.forecast_price,
    )

    return unpacked_signals


class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def get_sentiment_score(self, title: str) -> float:
        if not title:
            return 0.0
        try:
            scores = self.analyzer.polarity_scores(title)
            return scores['compound']
        except Exception:
            return 0.0


def analyze_sentiment_stream(news_table: pw.Table) -> pw.Table:
    print("Initializing VADER sentiment analyzer...")
    sentiment_analyzer = SentimentAnalyzer()

    sentiment_events = news_table.with_columns(
        timestamp=pw.this.dt_utc.dt.strptime(fmt="%Y-%m-%dT%H:%M:%S%z"),
        symbol=pw.this.ticker,
        sentiment_score=pw.apply(
            sentiment_analyzer.get_sentiment_score,
            pw.this.title
        ),
        headline=pw.this.title
    )

    return sentiment_events.select(
        pw.this.timestamp,
        pw.this.symbol,
        pw.this.sentiment_score,
        pw.this.title
    )


def main():
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    ticker = os.getenv('STOCK_TICKER', 'AAPL')
    unique_group_id = f"forecaster-group-{ticker}"

    news = pw.io.kafka.read(
        rdkafka_settings={
            "bootstrap.servers": bootstrap_servers,
            "broker.address.family": "v4",
            "group.id": unique_group_id,
            "session.timeout.ms": "6000",
            "auto.offset.reset": "earliest"
        },
        topic="news_data",
        schema=NewsSchema,
        format="json",
        autocommit_duration_ms=1000
    )

    ticks = pw.io.kafka.read(
        rdkafka_settings={
            "bootstrap.servers": bootstrap_servers,
            "broker.address.family": "v4",
            "group.id": unique_group_id,
            "session.timeout.ms": "6000",
            "auto.offset.reset": "earliest"
        },
        topic="stock_data",
        schema=TickInputSchema,
        format="json",
        autocommit_duration_ms=1000
    )

    vol = pw.io.kafka.read(
        rdkafka_settings={
            "bootstrap.servers": bootstrap_servers,
            "broker.address.family": "v4",
            "group.id": unique_group_id,
            "session.timeout.ms": "6000",
            "auto.offset.reset": "earliest"
        },
        topic="volume_volatility_data",
        schema=VolumeData,
        format="json",
        autocommit_duration_ms=1000
    )
    vol = vol.with_columns(
        timestamp=pw.this.timestamp.dt.strptime(fmt="%Y-%m-%dT%H:%M:%S.%f%z"),
        symbol=pw.this.symbol,
        volume_zscore=pw.this.volume_zscore,
        volatility_zscore=pw.this.volatility_zscore
    )

    ticks_processed = ticks.with_columns(
        symbol=ticks.s,
        timestamp=pw.this.t.dt.utc_from_timestamp("ms"),
        price=ticks.p,
        volume=ticks.v
    ).select(
        pw.this.symbol,
        pw.this.timestamp,
        pw.this.price,
        pw.this.volume
    ).filter(pw.this.symbol == ticker)

    ohlc_bars = ticks_processed.windowby(
        ticks_processed.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration(NEW_TIMEFRAME)),
        behavior=pw.temporal.exactly_once_behavior(),
        instance=ticks_processed.symbol
    ).reduce(
        symbol=pw.this._pw_instance,
        timestamp=pw.reducers.min(pw.this.timestamp),
        open=pw.reducers.argmin(pw.this.timestamp, pw.this.price),
        high=pw.reducers.max(pw.this.price),
        low=pw.reducers.min(pw.this.price),
        close=pw.reducers.argmax(pw.this.timestamp, pw.this.price),
        volume=pw.reducers.sum(pw.this.volume)
    )

    ohlc_bars = ohlc_bars.with_columns(
        return_val=pw.if_else(
            pw.this.open != 0,
            (pw.this.close - pw.this.open) / pw.this.open,
            0.0
        )
    )

    ohlc_bars = ohlc_bars.asof_join(
        vol,
        ohlc_bars.timestamp,
        vol.timestamp,
        ohlc_bars.symbol == vol.symbol,
        how=pw.JoinMode.LEFT,
        direction=pw.temporal.Direction.BACKWARD,
    ).select(
        symbol=ohlc_bars.symbol,
        timestamp=ohlc_bars.timestamp,
        open=ohlc_bars.open,
        high=ohlc_bars.high,
        low=ohlc_bars.low,
        close=ohlc_bars.close,
        volume=ohlc_bars.volume,
        return_val=ohlc_bars.return_val,
        volume_zscore=pw.coalesce(vol.volume_zscore, 0.0),
        volatility_zscore=pw.coalesce(vol.volatility_zscore, 0.0)
    )

    pw.io.jsonlines.write(ohlc_bars, f"/app/output/{ticker}/ohlc_bars_{ticker}.jsonl")

    sentiment_events = analyze_sentiment_stream(news)

    # FIXED: Pass lookback parameter
    sarimax_signals = analyze_ohlc_stream(
        ohlc_bars,
        lookback=SARIMAX_LOOKBACK
    )

    pw.io.jsonlines.write(sarimax_signals, f"/app/output/{ticker}/sarimax_signal_{ticker}.jsonl")

    combined_stream = sarimax_signals.asof_join(
        sentiment_events,
        sarimax_signals.timestamp,
        sentiment_events.timestamp,
        sarimax_signals.symbol == sentiment_events.symbol,
        how=pw.JoinMode.LEFT,
        direction=pw.temporal.Direction.FORWARD,
    ).select(
        symbol=sarimax_signals.symbol,
        sentiment_timestamp=sentiment_events.timestamp,
        timestamp=sarimax_signals.timestamp,
        last_seen_headline=sentiment_events.title,
        sentiment_score_raw=sentiment_events.sentiment_score,
        sarimax_signal=sarimax_signals.sarimax_signal,
        message=sarimax_signals.message,
        current_price=sarimax_signals.current_price,
        forecast_price=sarimax_signals.forecast_price,
    )

    final_signal_stream = combined_stream.with_columns(
        time_since_last_news_s=pw.if_else(
            pw.this.sentiment_timestamp.is_none(),
            timedelta(seconds=DECAY_PERIOD_SECONDS + 1),
            pw.this.timestamp - pw.this.sentiment_timestamp
        ),
        sentiment_score_raw=pw.if_else(
            pw.this.sentiment_score_raw.is_none(),
            0.0,
            pw.this.sentiment_score_raw
        ),
        last_seen_headline=pw.if_else(
            pw.this.last_seen_headline.is_none(),
            "No news on record",
            pw.this.last_seen_headline
        )
    ).with_columns(
        decay_factor=pw.apply_with_type(
            lambda time_since: max(timedelta(seconds=0.0).total_seconds(), timedelta(seconds=1.0).total_seconds() - (
                        time_since / DECAY_PERIOD_SECONDS).total_seconds()),
            float,
            pw.this.time_since_last_news_s
        ),
    ).with_columns(
        sentiment_score=pw.this.sentiment_score_raw * pw.this.decay_factor,
    ).with_columns(
        final_combined_signal=(pw.this.sarimax_signal * SARIMAX_WEIGHT) + \
                              (pw.this.sentiment_score * SENTIMENT_WEIGHT)
    ).with_columns(time_since_last_news_s=pw.this.time_since_last_news_s / 3600.0)

    final_output = final_signal_stream.select(
        pw.this.timestamp,
        pw.this.symbol,
        pw.this.final_combined_signal,
        pw.this.sarimax_signal,
        pw.this.sentiment_score,
        pw.this.sentiment_score_raw,
        pw.this.last_seen_headline,
        pw.this.time_since_last_news_s,
        pw.this.decay_factor,
        pw.this.message,
        pw.this.current_price,
        pw.this.forecast_price
    )

    output_file_path = f"/app/output/{ticker}/final_combined_signal_{ticker}.jsonl"
    output_file = Path(output_file_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    pw.io.jsonlines.write(final_output, f"/app/output/{ticker}/final_combined_signal_{ticker}.jsonl", name = "json_writer")

    pw.io.kafka.write(
        final_output,
        rdkafka_settings={
            "bootstrap.servers": bootstrap_servers,
            "security.protocol": "PLAINTEXT",
            "group.id": f"sarimax-writer-{ticker}",
            "queue.buffering.max.ms": "1000"
        },
        topic_name="sarimax_forecast",
        format="json",
        name = "kafka-writer"  #or "avro"
    )

    print(f"Final combined signals will be written to: {output_file_path}")
    print(f"SARIMAX will start generating forecast after {MIN_BARS_FOR_SIGNAL} bars")
    pw.run()



if __name__ == "__main__":
    main()