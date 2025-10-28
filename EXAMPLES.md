# Examples and Use Cases

This document provides practical examples and use cases for the Futu TSI/EWO Signal Generator.

## Table of Contents
- [Configuration Examples](#configuration-examples)
- [Command Line Usage](#command-line-usage)
- [Programmatic Usage](#programmatic-usage)
- [Custom Strategy Examples](#custom-strategy-examples)

## Configuration Examples

### Example 1: Conservative Long-term Portfolio (US Tech)

```yaml
# config_us_conservative.yaml
market:
  region: "US"
  timezone: "America/New_York"

watchlist:
  - "US.AAPL"
  - "US.MSFT"
  - "US.GOOGL"
  - "US.NVDA"

timeframes:
  - "240min"  # 4-hour only for longer-term signals

indicators:
  tsi:
    long: 35    # Slower, less sensitive
    short: 18
    signal: 18
  ewo:
    fast: 8
    slow: 50    # Wider spread for stronger confirmation

strategy:
  min_confidence: 0.6  # Higher threshold
  filters:
    min_volume: 1000000
    use_ma_trend: true  # Require MA confirmation

fundamentals:
  enabled: true
  liquidity:
    min_turnover_amount: 100000000  # $100M daily turnover
  valuation:
    pe_max: 80
    pb_max: 15
  size:
    min_percentile: 0.7  # Top 30% by market cap only
```

### Example 2: Aggressive Short-term Trading (HK Market)

```yaml
# config_hk_aggressive.yaml
market:
  region: "HK"
  timezone: "Asia/Hong_Kong"

watchlist:
  - "HK.00700"  # Tencent
  - "HK.09988"  # Alibaba
  - "HK.00388"  # HKEX
  - "HK.00941"  # China Mobile

timeframes:
  - "60min"   # 1-hour for more frequent signals
  - "120min"  # 2-hour for confirmation

indicators:
  tsi:
    long: 20    # Faster, more sensitive
    short: 10
    signal: 10
  ewo:
    fast: 3
    slow: 25    # Narrower spread for quicker signals

strategy:
  min_confidence: 0.4  # Lower threshold for more signals
  filters:
    min_volume: 50000
    use_ma_trend: false

fundamentals:
  enabled: true
  liquidity:
    min_turnover_amount: 30000000  # HK$30M
  valuation:
    pe_max: 50
    pb_max: 8
  size:
    min_percentile: 0.3  # More lenient
```

### Example 3: Fundamentals-Focused (Mixed Markets)

```yaml
# config_fundamentals_focused.yaml
watchlist:
  - "HK.00700"
  - "HK.01299"
  - "US.AAPL"
  - "US.JPM"

fundamentals:
  enabled: true
  
  liquidity:
    min_turnover_amount: 80000000
  
  valuation:
    pe_min: 5      # Avoid extremely low PE
    pe_max: 40     # Conservative valuation
    pb_max: 5      # Strong balance sheet
  
  overrides:
    US:
      pe_max: 50   # Slightly higher for US
      pb_max: 8
    HK:
      pe_max: 35   # More conservative for HK
      pb_max: 4
  
  size:
    min_percentile: 0.8  # Top 20% only
  
  scoring:
    size_weight: 0.5     # Emphasize large caps
    pe_weight: 0.3
    pb_weight: 0.2
    min_score: 0.7       # High quality threshold
  
  missing_data_action: "block"  # Strict: require all data
```

## Command Line Usage

### Basic Backtest

```bash
# Run backtest with default config
python -m src.backtest.run_backtest

# Use custom config
python -m src.backtest.run_backtest --config config_us_conservative.yaml
```

### Real-time Signal Generation

```bash
# Run continuously (production mode)
python -m src.realtime.signal_runner --config src/config/config.yaml

# Run once for testing
python -m src.realtime.signal_runner --config src/config/config.yaml --once

# Run with custom config
python -m src.realtime.signal_runner --config config_hk_aggressive.yaml
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_tsi_ewo.py -v

# Specific test function
pytest tests/test_tsi_ewo.py::test_calculate_tsi -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Programmatic Usage

### Example 1: Fetch Data and Calculate Indicators

```python
from src.data.futu_client import FutuClient
from src.indicators.tsi_ewo import add_all_indicators

# Connect to Futu OpenD
with FutuClient() as client:
    # Fetch data
    df = client.fetch_intraday_data(
        symbol="HK.00700",
        days_back=30,
        base_ktype="1min"
    )
    
    # Resample to 1-hour
    df_1h = client.resample_to_timeframe(
        df,
        timeframe="60min",
        timezone="Asia/Hong_Kong"
    )
    
    # Add indicators
    df_with_indicators = add_all_indicators(
        df_1h,
        tsi_long=25,
        tsi_short=13,
        tsi_signal=13,
        ewo_fast=5,
        ewo_slow=35
    )
    
    # View latest values
    print(df_with_indicators.tail())
    print(f"Latest TSI: {df_with_indicators['TSI'].iloc[-1]:.2f}")
    print(f"Latest EWO: {df_with_indicators['EWO'].iloc[-1]:.2f}")
```

### Example 2: Generate Signals Manually

```python
from src.data.futu_client import FutuClient
from src.indicators.tsi_ewo import add_all_indicators
from src.strategies.tsi_ewo_strategy import TSIEWOStrategy

# Strategy config
strategy_config = {
    "min_confidence": 0.5,
    "filters": {
        "min_volume": 100000,
        "use_ma_trend": False
    }
}

with FutuClient() as client:
    df = client.fetch_intraday_data("HK.00700", days_back=30)
    df_1h = client.resample_to_timeframe(df, "60min", "Asia/Hong_Kong")
    df_with_indicators = add_all_indicators(df_1h)
    
    # Generate signals
    strategy = TSIEWOStrategy(strategy_config)
    df_with_signals = strategy.generate_signals(df_with_indicators)
    
    # Extract latest signals
    signals = strategy.extract_latest_signals(
        df_with_signals,
        symbol="HK.00700",
        timeframe="60min"
    )
    
    for signal in signals:
        print(f"Signal: {signal}")
```

### Example 3: Check Fundamentals

```python
from src.data.futu_client import FutuClient
from src.fundamentals.providers.futu_snapshot import FutuSnapshotProvider
from src.fundamentals.scoring import FundamentalsScorer

# Fundamentals config
fundamentals_config = {
    "enabled": True,
    "liquidity": {"min_turnover_amount": 50_000_000},
    "valuation": {"pe_min": 0, "pe_max": 60, "pb_max": 10},
    "size": {"min_percentile": 0.5},
    "scoring": {
        "size_weight": 0.4,
        "pe_weight": 0.3,
        "pb_weight": 0.3,
        "min_score": 0.5
    },
    "missing_data_action": "pass"
}

with FutuClient() as client:
    provider = FutuSnapshotProvider(client)
    scorer = FundamentalsScorer(fundamentals_config)
    
    # Check single symbol
    metrics = provider.fetch_basic_metrics("HK.00700")
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK"
    )
    
    print(f"Symbol: HK.00700")
    print(f"Metrics: {metrics}")
    print(f"Passes: {passes}")
    print(f"Reason: {reason}")
    print(f"Score: {score:.2f}")
```

### Example 4: Custom Backtest

```python
import vectorbt as vbt
from src.data.futu_client import FutuClient
from src.indicators.tsi_ewo import add_all_indicators
from src.strategies.tsi_ewo_strategy import TSIEWOStrategy

with FutuClient() as client:
    # Fetch and prepare data
    df = client.fetch_intraday_data("US.AAPL", days_back=90)
    df_4h = client.resample_to_timeframe(df, "240min", "America/New_York")
    df_with_indicators = add_all_indicators(df_4h)
    
    # Generate signals
    strategy = TSIEWOStrategy({"min_confidence": 0.5})
    df_with_signals = strategy.generate_signals(df_with_indicators)
    
    # Run backtest
    portfolio = vbt.Portfolio.from_signals(
        close=df_with_signals["close"],
        entries=df_with_signals["long_entry"],
        exits=df_with_signals["long_exit"],
        init_cash=100000,
        fees=0.001,
        slippage=0.001,
        freq="4h"
    )
    
    # Print results
    print(f"Total Return: {portfolio.total_return() * 100:.2f}%")
    print(f"Sharpe Ratio: {portfolio.sharpe_ratio():.2f}")
    print(f"Max Drawdown: {portfolio.max_drawdown() * 100:.2f}%")
    print(f"Win Rate: {portfolio.trades.win_rate() * 100:.2f}%")
    print(f"Total Trades: {portfolio.trades.count()}")
```

## Custom Strategy Examples

### Example 1: Add RSI Filter

```python
# In src/strategies/tsi_ewo_rsi_strategy.py
import pandas_ta as ta
from src.strategies.tsi_ewo_strategy import TSIEWOStrategy

class TSIEWORSIStrategy(TSIEWOStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df_copy = super().generate_signals(df)
        
        # Add RSI
        rsi = ta.rsi(df_copy["close"], length=14)
        df_copy["RSI"] = rsi
        
        # Filter: only take longs when RSI < 70 (not overbought)
        df_copy["long_entry"] = (
            df_copy["long_entry"] & 
            (df_copy["RSI"] < 70)
        )
        
        return df_copy
```

### Example 2: Volume Surge Detection

```python
# Add to TSIEWOStrategy or create new class
def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
    df_copy = super().generate_signals(df)
    
    # Calculate volume moving average
    vol_ma = df_copy["volume"].rolling(20).mean()
    
    # Require volume surge (2x average) for entry
    volume_surge = df_copy["volume"] > (vol_ma * 2)
    
    df_copy["long_entry"] = (
        df_copy["long_entry"] & 
        volume_surge
    )
    
    return df_copy
```

### Example 3: Multi-Timeframe Confirmation

```python
from src.data.futu_client import FutuClient
from src.indicators.tsi_ewo import add_all_indicators
from src.strategies.tsi_ewo_strategy import TSIEWOStrategy

def get_multi_timeframe_signal(symbol: str, client: FutuClient):
    """Generate signal only if aligned across multiple timeframes."""
    timeframes = ["60min", "120min", "240min"]
    signals = []
    
    for tf in timeframes:
        df = client.fetch_intraday_data(symbol, days_back=30)
        df_resampled = client.resample_to_timeframe(df, tf, "Asia/Hong_Kong")
        df_with_indicators = add_all_indicators(df_resampled)
        
        strategy = TSIEWOStrategy({"min_confidence": 0.5})
        df_with_signals = strategy.generate_signals(df_with_indicators)
        
        # Check if latest candle has signal
        latest = df_with_signals.iloc[-1]
        if latest["long_entry"]:
            signals.append(tf)
    
    # Require at least 2 out of 3 timeframes to agree
    if len(signals) >= 2:
        return {
            "symbol": symbol,
            "side": "LONG",
            "confirming_timeframes": signals,
            "confidence": len(signals) / len(timeframes)
        }
    
    return None
```

## Tips and Best Practices

### 1. Parameter Optimization

Start with default parameters, then optimize based on backtests:

```bash
# Test conservative parameters
python -m src.backtest.run_backtest --config config_conservative.yaml

# Test aggressive parameters  
python -m src.backtest.run_backtest --config config_aggressive.yaml

# Compare results and choose based on your risk tolerance
```

### 2. Paper Trading

Before live trading, run signals in real-time without executing trades:

```bash
# Monitor signals for 1-2 weeks
python -m src.realtime.signal_runner --config src/config/config.yaml

# Review signals.log to evaluate quality
cat signals.log | jq .
```

### 3. Multi-Market Portfolio

Run separate instances for different markets:

```bash
# Terminal 1: HK market
python -m src.realtime.signal_runner --config config_hk.yaml

# Terminal 2: US market
python -m src.realtime.signal_runner --config config_us.yaml
```

### 4. Monitoring and Logging

Set up log rotation and monitoring:

```bash
# In production, use supervisor or systemd
# Example systemd service file:

[Unit]
Description=Futu Signal Runner - HK Market
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/python -m src.realtime.signal_runner --config config_hk.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Troubleshooting Examples

### Debug Mode

Add verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run your code
```

### Check Data Quality

```python
from src.data.futu_client import FutuClient

with FutuClient() as client:
    df = client.fetch_intraday_data("HK.00700", days_back=5)
    
    print(f"Data shape: {df.shape}")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print(f"Missing values: {df.isnull().sum()}")
    print(f"Data sample:\n{df.head()}")
```

### Verify Fundamentals Data

```python
from src.data.futu_client import FutuClient
from src.fundamentals.providers.futu_snapshot import FutuSnapshotProvider

with FutuClient() as client:
    provider = FutuSnapshotProvider(client)
    
    symbols = ["HK.00700", "HK.09988", "HK.00941"]
    for symbol in symbols:
        metrics = provider.fetch_basic_metrics(symbol)
        print(f"\n{symbol}:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
```

## Additional Resources

- [Futu OpenAPI Documentation](https://openapi.futunn.com/)
- [vectorbt Documentation](https://vectorbt.dev/)
- [pandas_ta Documentation](https://github.com/twopirllc/pandas-ta)
- [Server酱 Documentation](https://sct.ftqq.com/)

For more examples, check the test files in `tests/` directory.
