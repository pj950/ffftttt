# Futu Intraday TSI/EWO Signal Generator

A half-automatic intraday trading signal generator for stocks via Futu OpenAPI. Computes technical signals (TSI, EWO) on 1h/2h/4h bars, backtests with vectorbt, and pushes real-time signals to WeChat via Server酱 (ServerChan). No order placement - signals only.

## Features

- **Data Adapter**: Futu OpenD client to pull intraday candles and resample to 1h/2h/4h timeframes
- **Technical Indicators**: 
  - TSI (True Strength Index)
  - EWO (Elliott Wave Oscillator)
  - Configurable parameters
- **Strategy Rules**:
  - LONG entry: TSI crosses above 0 AND EWO > 0
  - LONG exit: TSI crosses below 0 OR EWO < 0
  - Confidence scoring based on indicator strength
- **Fundamentals Whitelist**:
  - Liquidity gate: 20-day avg daily turnover ≥ 50M
  - Valuation gates: 0 < PE ≤ 60, PB ≤ 10 (configurable per market)
  - Size gate: Market cap percentile ≥ 50%
  - Composite scoring with configurable weights
- **Backtesting**: 
  - vectorbt-based pipeline
  - Metrics: CAGR, Sharpe, Win Rate, Max DD, Calmar
  - Configurable fees and slippage
- **Real-time Runner**:
  - Market hours aware (with lunch break exclusions)
  - Signal deduplication with cooldown periods
  - JSON output to stdout and log file
- **Notifications**: Server酱 integration for WeChat alerts

## Tech Stack

- Python 3.10+
- vectorbt, pandas, numpy, pandas_ta
- futu-api (Futu OpenAPI Python SDK)
- pyyaml, requests, python-dotenv

## Project Structure

```
.
├── src/
│   ├── config/
│   │   └── config.yaml           # Main configuration file
│   ├── data/
│   │   └── futu_client.py        # Futu OpenD client wrapper
│   ├── indicators/
│   │   └── tsi_ewo.py            # TSI and EWO indicators
│   ├── strategies/
│   │   └── tsi_ewo_strategy.py   # Signal generation logic
│   ├── backtest/
│   │   └── run_backtest.py       # Backtesting pipeline
│   ├── realtime/
│   │   └── signal_runner.py      # Real-time signal generator
│   ├── notify/
│   │   └── serverchan.py         # Server酱 notifier
│   └── fundamentals/
│       ├── provider_base.py      # Fundamentals provider interface
│       ├── providers/
│       │   ├── futu_snapshot.py  # Futu data provider
│       │   └── yfinance_fallback.py  # Yahoo Finance fallback
│       └── scoring.py            # Fundamentals scoring/gating
├── tests/
│   ├── test_tsi_ewo.py           # Indicator tests
│   └── test_fundamentals_scoring.py  # Fundamentals tests
├── scripts/
│   └── bootstrap_env.sh          # Environment setup script
├── requirements.txt
└── README.md
```

## Setup

### 1. Prerequisites

- Python 3.10 or higher
- Futu OpenD (Futu OpenAPI daemon)
  - Download from: https://www.futunn.com/download/OpenAPI
  - Install and start OpenD before running the signal generator
- Server酱 account (for WeChat notifications)
  - Register at: https://sct.ftqq.com/
  - Get your SendKey from the dashboard

### 2. Installation

```bash
# Clone the repository (if applicable)
git clone <repository-url>
cd <repository-directory>

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

#### Environment Variables

Create a `.env` file with your credentials:

```bash
# Run the bootstrap script
bash scripts/bootstrap_env.sh

# Edit .env and add your actual values
# FUTU_OPEND_HOST=127.0.0.1
# FUTU_OPEND_PORT=11111
# SERVERCHAN_KEY=your_actual_key_here
```

Or manually create `.env`:

```bash
FUTU_OPEND_HOST=127.0.0.1
FUTU_OPEND_PORT=11111
SERVERCHAN_KEY=your_serverchan_key_here
```

#### Strategy Configuration

Edit `src/config/config.yaml` to customize:

- **Watchlist**: Add your stock symbols (e.g., `HK.00700`, `US.AAPL`)
- **Timeframes**: Choose from `60min`, `120min`, `240min`
- **Indicator Parameters**: Adjust TSI and EWO periods
- **Strategy Filters**: Configure minimum volume, MA trend filters
- **Fundamentals**: Set liquidity/valuation/size thresholds
- **Backtest Settings**: Fees, slippage, initial cash
- **Real-time Settings**: Market hours, cooldown periods

### 4. Starting Futu OpenD

Before running the signal generator:

1. Open FutuNiu/FutuBull desktop application
2. Start Futu OpenD (usually via OpenD icon or command line)
3. Ensure OpenD is running on the configured host/port (default: 127.0.0.1:11111)
4. Check OpenD logs to confirm it's ready

## Usage

### Backtesting

Run historical backtests on your watchlist:

```bash
python -m src.backtest.run_backtest --config src/config/config.yaml
```

Output:
- Console summary with metrics (CAGR, Sharpe, Win Rate, etc.)
- CSV report in `backtest_results/backtest_results_YYYYMMDD_HHMMSS.csv`
- HTML report (if enabled in config)

### Real-time Signal Generation

Run the signal generator during market hours:

```bash
python -m src.realtime.signal_runner --config src/config/config.yaml
```

The runner will:
- Check if market is open (respecting configured hours and lunch breaks)
- Fetch latest data and compute indicators
- Apply fundamentals whitelist
- Generate and emit signals (with cooldown to prevent duplicates)
- Send notifications via Server酱
- Log signals to `signals.log` (JSON format)

For testing (run once and exit):

```bash
python -m src.realtime.signal_runner --config src/config/config.yaml --once
```

### Running Tests

```bash
pytest tests/
```

Or run specific test files:

```bash
pytest tests/test_tsi_ewo.py
pytest tests/test_fundamentals_scoring.py
```

## Signal Format

Signals are emitted as JSON with the following fields:

```json
{
  "timestamp": "2024-01-15 14:30:00",
  "symbol": "HK.00700",
  "timeframe": "60min",
  "side": "LONG",
  "price": 350.50,
  "confidence": 0.75,
  "reason": "TSI↑0, EWO=2.50>0"
}
```

## Fundamentals Whitelist

By default, all symbols must pass fundamentals checks before generating signals:

1. **Liquidity Gate**: 20-day avg daily turnover ≥ 50M (native currency)
2. **Valuation Gates**: 
   - PE ratio: 0 < PE ≤ 60
   - PB ratio: PB ≤ 10
   - Market-specific overrides supported (US, CN, HK)
3. **Size Gate**: Market cap percentile ≥ 50% within watchlist
4. **Composite Score**: Weighted score ≥ 0.5

Configure in `config.yaml`:

```yaml
fundamentals:
  enabled: true
  liquidity:
    min_turnover_amount: 50000000
  valuation:
    pe_min: 0
    pe_max: 60
    pb_max: 10
  overrides:
    US:
      pe_max: 80
  size:
    min_percentile: 0.5
  scoring:
    size_weight: 0.4
    pe_weight: 0.3
    pb_weight: 0.3
    min_score: 0.5
  missing_data_action: "pass"  # or "block"
```

## Strategy Details

### TSI (True Strength Index)

- Double-smoothed momentum indicator
- Default params: long=25, short=13, signal=13
- Range: -100 to +100
- Crossover above 0 = bullish signal

### EWO (Elliott Wave Oscillator)

- EMA(5) - EMA(35) on price
- Positive = uptrend, Negative = downtrend
- Used as confirmation filter

### Entry Logic

**LONG Entry**:
- TSI crosses above 0 (bullish momentum)
- AND EWO > 0 (confirming uptrend)
- Optional: Price > MA(50) if `use_ma_trend` enabled
- Optional: Volume ≥ min_volume if configured

**LONG Exit**:
- TSI crosses below 0 (momentum reversal)
- OR EWO < 0 (trend reversal)

### Confidence Scoring

Confidence (0-1) is calculated based on:
- TSI magnitude (40% weight)
- EWO magnitude (30% weight)
- Base confidence (30% weight)

Signals below `min_confidence` threshold are filtered out.

## Notifications

### Server酱 (ServerChan)

Server酱 sends notifications to your WeChat:

1. Register at https://sct.ftqq.com/
2. Get your SendKey
3. Add to `.env`: `SERVERCHAN_KEY=your_key_here`

Notification format (customizable in config):

```
Title: LONG HK.00700 [60min]

Message:
Signal: LONG
Symbol: HK.00700
Timeframe: 60min
Price: 350.50
Confidence: 0.75
Reason: TSI↑0, EWO=2.50>0
Time: 2024-01-15 14:30:00
```

## Cooldown & Deduplication

To prevent alert fatigue, the runner tracks recent signals and enforces a cooldown period (default: 4 hours) per symbol/timeframe/side combination.

Configure in `config.yaml`:

```yaml
realtime:
  cooldown:
    enabled: true
    period_hours: 4
```

## Market Hours

The runner respects market hours and lunch breaks:

```yaml
market:
  region: "HK"
  timezone: "Asia/Hong_Kong"

realtime:
  market_hours:
    start: "09:30"
    end: "16:00"
    exclude_ranges:
      - start: "12:00"
        end: "13:00"
```

For US markets:

```yaml
market:
  region: "US"
  timezone: "America/New_York"

realtime:
  market_hours:
    start: "09:30"
    end: "16:00"
    exclude_ranges: []  # No lunch break
```

## Troubleshooting

### Futu Connection Issues

**Error**: `Failed to connect to OpenD`

- Ensure Futu OpenD is running
- Check host/port in `.env` matches OpenD settings
- Verify firewall isn't blocking the connection
- Check OpenD logs for errors

### No Data Returned

**Error**: `No data available for symbol`

- Verify symbol format (e.g., `HK.00700`, `US.AAPL`)
- Check if you have data subscription for the symbol
- Ensure sufficient lookback_days in config
- Some symbols may have limited intraday data

### Server酱 Notifications Not Working

**Error**: `Notification failed`

- Verify `SERVERCHAN_KEY` in `.env` is correct
- Check key is not expired at https://sct.ftqq.com/
- Ensure internet connection is stable
- Check Server酱 usage quota

### Fundamentals Data Missing

If fundamentals checks are failing:

- Set `missing_data_action: "pass"` in config to allow missing data
- Or disable fundamentals: `fundamentals.enabled: false`
- Some markets/symbols may have incomplete fundamental data

## Advanced Usage

### Custom Indicators

Add new indicators in `src/indicators/tsi_ewo.py`:

```python
def calculate_custom_indicator(close: pd.Series, period: int) -> pd.Series:
    # Your implementation
    return result
```

Update `add_all_indicators()` to include your indicator.

### Custom Signal Rules

Modify `src/strategies/tsi_ewo_strategy.py`:

```python
def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
    df_copy = df.copy()
    
    # Add your custom rules
    df_copy["long_entry"] = (
        df_copy["TSI_crossover"] &
        (df_copy["EWO"] > 0) &
        (df_copy["custom_indicator"] > threshold)
    )
    
    return df_copy
```

### Multiple Watchlists

Create separate config files for different watchlists:

```bash
python -m src.backtest.run_backtest --config config/hk_large_cap.yaml
python -m src.realtime.signal_runner --config config/us_tech.yaml
```

## Performance Notes

- First run may be slow due to data fetching and indicator calculations
- Subsequent runs use incremental updates (if implemented)
- Backtests with many symbols/timeframes can take several minutes
- Real-time runner checks every 60 seconds by default (configurable)

## Limitations

- **No order placement**: This is a signal generator only
- **Market data**: Requires Futu account with appropriate data subscriptions
- **Intraday data**: Limited historical intraday data availability
- **Fundamentals**: Data quality varies by market and symbol
- **Backtesting**: Does not account for all real-world factors (news, halts, etc.)

## Contributing

To add new features:

1. Add provider implementations in `src/fundamentals/providers/`
2. Add indicator calculations in `src/indicators/`
3. Add strategy variants in `src/strategies/`
4. Add tests in `tests/`

## License

[Add your license here]

## Disclaimer

This software is for educational and research purposes only. It does not constitute financial advice. Trading involves risk, and you should carefully consider your investment objectives, level of experience, and risk tolerance. Past performance does not guarantee future results.
