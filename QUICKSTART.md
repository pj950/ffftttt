# Quick Start Guide

This guide will help you get started with the Futu TSI/EWO Signal Generator in 5 minutes.

## Prerequisites

- Python 3.10+
- Futu OpenD installed and running
- (Optional) Server酱 account for WeChat notifications

## Setup (5 minutes)

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Create .env file
bash scripts/bootstrap_env.sh

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Update these values in `.env`:
- `FUTU_OPEND_HOST`: Your OpenD host (usually `127.0.0.1`)
- `FUTU_OPEND_PORT`: Your OpenD port (usually `11111`)
- `SERVERCHAN_KEY`: Your Server酱 key (get from https://sct.ftqq.com/)

### 3. Update Watchlist

Edit `src/config/config.yaml` and add your symbols:

```yaml
watchlist:
  - "HK.00700"  # Tencent
  - "HK.09988"  # Alibaba
  - "US.AAPL"   # Apple
  - "US.TSLA"   # Tesla
```

### 4. Start Futu OpenD

Make sure Futu OpenD is running before proceeding. Check that it's accessible:

```bash
# Test connection (optional)
telnet 127.0.0.1 11111
```

## Usage

### Run Backtest

Test the strategy on historical data:

```bash
python -m src.backtest.run_backtest --config src/config/config.yaml
```

Results will be saved to `backtest_results/` folder.

### Run Real-time Signals

Start the signal generator:

```bash
python -m src.realtime.signal_runner --config src/config/config.yaml
```

Or test with a single run:

```bash
python -m src.realtime.signal_runner --config src/config/config.yaml --once
```

### Run Tests

Verify everything is working:

```bash
pytest tests/ -v
```

## What to Expect

### Backtest Output

```
📊 Processing HK.00700...
  ✅ HK.00700 [60min]: Return=15.23%, Sharpe=1.45, Trades=12

BACKTEST RESULTS SUMMARY
symbol      timeframe  total_return  cagr   sharpe_ratio  max_drawdown  win_rate  total_trades
HK.00700    60min      15.23        18.45   1.45         -8.32         66.67     12
...

✅ Results saved to: backtest_results/backtest_results_20240115_143022.csv
```

### Real-time Signal Output

```
🔔 SIGNAL: {"timestamp": "2024-01-15 14:30:00", "symbol": "HK.00700", "timeframe": "60min", "side": "LONG", "price": 350.50, "confidence": 0.75, "reason": "TSI↑0, EWO=2.50>0"}
  ✅ Notification sent via Server酱
```

Signals are also logged to `signals.log`.

## Customization

### Adjust Indicator Parameters

In `config.yaml`:

```yaml
indicators:
  tsi:
    long: 25    # Increase for slower signals
    short: 13
    signal: 13
  ewo:
    fast: 5     # Adjust EMA periods
    slow: 35
```

### Adjust Fundamentals Filters

```yaml
fundamentals:
  enabled: true
  liquidity:
    min_turnover_amount: 50000000  # Minimum daily turnover (50M)
  valuation:
    pe_max: 60  # Maximum P/E ratio
    pb_max: 10  # Maximum P/B ratio
```

### Change Timeframes

```yaml
timeframes:
  - "60min"   # 1 hour
  - "120min"  # 2 hours
  - "240min"  # 4 hours
```

## Troubleshooting

### "Failed to connect to OpenD"

- Ensure Futu OpenD is running
- Check `FUTU_OPEND_HOST` and `FUTU_OPEND_PORT` in `.env`

### "No data available"

- Verify symbol format (e.g., `HK.00700`, `US.AAPL`)
- Check if you have data subscription for the symbol
- Increase `lookback_days` in config

### "Notification failed"

- Verify `SERVERCHAN_KEY` is correct
- Check key at https://sct.ftqq.com/

### All symbols filtered by fundamentals

- Lower thresholds in `fundamentals` section
- Set `missing_data_action: "pass"`
- Or disable: `fundamentals.enabled: false`

## Next Steps

1. **Paper Trading**: Monitor signals for a few days without trading
2. **Backtest Optimization**: Tune parameters to improve performance
3. **Add More Symbols**: Expand your watchlist
4. **Custom Strategies**: Modify signal rules in `src/strategies/tsi_ewo_strategy.py`

## Support

For issues or questions:
1. Check the main [README.md](README.md)
2. Review the code documentation
3. Check Futu OpenAPI docs: https://openapi.futunn.com/

Happy trading! 🚀
