# Futu Intraday Signal Generator with Extensible Indicators

A half-automatic intraday trading signal generator for stocks via Futu OpenAPI. Features a pluggable indicator registry, fusion strategy system, and support for multiple technical indicators (TSI/EWO/SuperTrend/HMA/QQE/ADX). Includes backtesting with vectorbt and real-time signal delivery via WeChat. No order placement - signals only.

## Features

### 🎯 Core System
- **Data Adapter**: Futu OpenD client to pull intraday candles and resample to 1h/2h/4h timeframes
- **Extensible Indicator Registry**: 
  - Dynamic loading and registration of indicators
  - Config-driven parameters
  - Easy to add new indicators (see [INDICATOR_GUIDE.md](INDICATOR_GUIDE.md))
- **Fusion Strategy System**:
  - Rule-based fusion (AND/OR/threshold conditions)
  - Weighted fusion (configurable indicator weights)
  - Predefined templates: SuperTrend+HMA, SuperTrend+QQE, TSI+EWO
  - Custom rule definitions in YAML

### 📊 Technical Indicators
- **SuperTrend**: ATR-based trend following with trailing stops
- **Hull Moving Average (HMA)**: Fast, smooth MA with slope detection
- **QQE (Quantitative Qualitative Estimation)**: RSI-based with signal line
- **ADX**: Trend strength filter
- **ATR Percentile**: Volatility regime filter (0.2-0.85 range)
- **RSI**: Relative Strength Index
- **TSI**: True Strength Index (legacy support)
- **EWO**: Elliott Wave Oscillator (legacy support)

### 🔍 Strategy Features
- **Entry Templates**:
  - SuperTrend+HMA: `ST_trend=up AND HMA_slope>0 AND RSI>50`
  - SuperTrend+QQE: `ST_trend=up AND QQE>signal AND ADX>25`
  - TSI+EWO: `TSI crosses 0 AND EWO>0` (legacy)
- **Exit Conditions**:
  - SuperTrend flips, ATR trailing stops, RSI thresholds, time-based exits
- **Regime Filters**:
  - ATR percentile filter (avoid extreme volatility)
  - ADX trend strength requirement
  - Volume filters
- **Confidence Scoring**: Multi-factor confidence calculation per signal

### 📈 Fundamentals Whitelist
- Liquidity gate: 20-day avg daily turnover ≥ 50M
- Valuation gates: 0 < PE ≤ 60, PB ≤ 10 (configurable per market)
- Size gate: Market cap percentile ≥ 50%
- Composite scoring with configurable weights

### 🧪 Backtesting & Analysis
- vectorbt-based pipeline with comparison framework
- **Comparison Backtests**: Test multiple indicator suites side-by-side
- **Signal Lag Metrics**: Measure response time to price movements
- Metrics: CAGR, Sharpe, Win Rate, Max DD, Calmar, Profit Factor
- Walk-forward validation support
- HTML and CSV reports with improvement analysis

### 🔄 Real-time Runner
- Market hours aware (with lunch break exclusions)
- Signal deduplication with cooldown periods
- Supports both legacy and fusion strategies
- JSON output to stdout and log file
- Fundamentals gating preserved

### 📱 Notifications
- Server酱 integration for WeChat alerts

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
│   │   └── config.yaml              # Main configuration file
│   ├── data/
│   │   └── futu_client.py           # Futu OpenD client wrapper
│   ├── indicators/
│   │   ├── registry.py              # Indicator registry system
│   │   ├── supertrend.py            # SuperTrend indicator
│   │   ├── hma.py                   # Hull Moving Average
│   │   ├── qqe.py                   # QQE indicator
│   │   ├── adx.py                   # ADX trend strength
│   │   ├── atr_percentile.py        # ATR volatility filter
│   │   ├── rsi.py                   # RSI indicator
│   │   ├── tsi.py                   # TSI (registry wrapper)
│   │   ├── ewo.py                   # EWO (registry wrapper)
│   │   └── tsi_ewo.py               # Legacy TSI/EWO functions
│   ├── strategies/
│   │   ├── fusion.py                # Extensible fusion strategy
│   │   └── tsi_ewo_strategy.py      # Legacy TSI/EWO strategy
│   ├── backtest/
│   │   ├── run_backtest.py          # Basic backtesting
│   │   └── comparison.py            # Multi-strategy comparison
│   ├── realtime/
│   │   └── signal_runner.py         # Real-time signal generator
│   ├── notify/
│   │   └── serverchan.py            # Server酱 notifier
│   └── fundamentals/
│       ├── provider_base.py         # Fundamentals provider interface
│       ├── providers/
│       │   ├── futu_snapshot.py     # Futu data provider
│       │   └── yfinance_fallback.py # Yahoo Finance fallback
│       └── scoring.py               # Fundamentals scoring/gating
├── tests/
│   ├── test_tsi_ewo.py              # Indicator tests
│   └── test_fundamentals_scoring.py # Fundamentals tests
├── scripts/
│   └── bootstrap_env.sh             # Environment setup script
├── INDICATOR_GUIDE.md               # How to add indicators/fusion rules
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

### Quick Start: Using New Fusion Strategy

1. **Configure Strategy** - Edit `src/config/config.yaml`:

```yaml
strategy:
  type: "fusion"  # Use new fusion system
  fusion_mode: "rule_based"
  
  entry_rules:
    long_entry:
      template: "supertrend_hma"  # or "supertrend_qqe"
```

2. **Run Comparison Backtest**:

```bash
python -m src.backtest.comparison --config src/config/config.yaml
```

This will test TSI/EWO vs new fusion strategies and generate a comparison report.

3. **Run Real-time Signals**:

```bash
python -m src.realtime.signal_runner --config src/config/config.yaml
```

### Backtesting

#### Basic Backtest

Run historical backtests on your watchlist:

```bash
python -m src.backtest.run_backtest --config src/config/config.yaml
```

Output:
- Console summary with metrics (CAGR, Sharpe, Win Rate, etc.)
- CSV report in `backtest_results/backtest_results_YYYYMMDD_HHMMSS.csv`
- HTML report (if enabled in config)

#### Comparison Backtest

Compare multiple indicator suites:

```bash
python -m src.backtest.comparison --config src/config/config.yaml
```

This will:
- Test legacy TSI/EWO strategy
- Test SuperTrend+HMA fusion
- Test SuperTrend+QQE fusion
- Calculate signal lag metrics
- Generate improvement analysis
- Output: `comparison_YYYYMMDD_HHMMSS.csv` and `.html`

Example output:
```
IMPROVEMENTS vs TSI/EWO
================================================================
fusion_supertrend_hma:
  total_return: 📈 +5.23 (+15.2%)
  sharpe_ratio: 📈 +0.31 (+22.1%)
  signal_lag: ⚡ -2.30 bars (+38.3% faster)
```

### Real-time Signal Generation

Run the signal generator during market hours:

```bash
python -m src.realtime.signal_runner --config src/config/config.yaml
```

The runner will:
- Check if market is open (respecting configured hours and lunch breaks)
- Fetch latest data and compute indicators via registry
- Apply fusion strategy rules
- Apply fundamentals whitelist
- Generate and emit signals (with cooldown to prevent duplicates)
- Send notifications via Server酱
- Log signals to `signals.log` (JSON format)

For testing (run once and exit):

```bash
python -m src.realtime.signal_runner --config src/config/config.yaml --once
```

**Legacy Mode**: To use the original TSI/EWO strategy:

```yaml
strategy:
  type: "tsi_ewo"  # Legacy mode
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

### Data Sources

- **Primary**: Futu snapshot and day bars (PE_TTM, PB, MktCap, daily turnover amount)
- **Fallback**: yfinance for US/HK when Futu fields are missing

### Configuration

Configure in `config.yaml`:

```yaml
fundamentals:
  enabled: true
  gate_behavior_on_missing: pass  # "pass" or "block"
  refresh: daily  # rebuild cache each trading day
  
  thresholds:
    liquidity:
      metric: adtv_amount_native
      lookback_days: 20
      min: 50000000  # 50M in native currency
    
    global:
      pe_min: 0
      pe_max: 60
      pb_max: 10
      cap_percentile_min: 0.5  # top 50% by cap
    
    overrides:
      US:
        pe_max: 50
        pb_max: 12
        cap_percentile_min: 0.6
      HK:
        pe_max: 60
        pb_max: 10
        cap_percentile_min: 0.5
      CN:
        pe_max: 80
        pb_max: 12
        cap_percentile_min: 0.5
  
  scoring:
    weights:
      size: 0.4
      pe: 0.3
      pb: 0.3
    min_score: 0.5
```

### Scoring Formula

- **PE Score**: `clamp((pe_max - PE) / pe_max, 0, 1)`
- **PB Score**: `clamp((pb_max - PB) / pb_max, 0, 1)`
- **Size Score**: Market cap percentile within watchlist
- **Composite Score**: `0.4 × Size + 0.3 × PE + 0.3 × PB`

Lower PE and PB ratios result in higher scores. The composite score must meet the minimum threshold (default: 0.5).

### Pre-building Cache

You can pre-build the fundamentals cache before running the signal generator:

```bash
python -m src.fundamentals.refresh --config src/config/config.yaml
```

This will:
- Fetch fundamentals data for all watchlist symbols
- Apply the scoring and gating logic
- Save results to `cache/fundamentals_{YYYYMMDD}.json`
- Display which symbols passed/failed and why

Cache files are automatically used by the signal generator when fresh.

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

### Adding Custom Indicators

The new registry system makes it easy to add indicators. See [INDICATOR_GUIDE.md](INDICATOR_GUIDE.md) for details.

**Quick example**:

1. Create `src/indicators/my_indicator.py`:

```python
from src.indicators.registry import BaseIndicator, register_indicator

@register_indicator("my_indicator")
class MyIndicator(BaseIndicator):
    def __init__(self, period: int = 20, **kwargs):
        super().__init__(period=period, **kwargs)
        self.period = period
    
    @property
    def name(self) -> str:
        return "my_indicator"
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy()
        # Your calculation here
        df_copy["MY_IND"] = ...
        return df_copy
    
    def get_signal_columns(self) -> List[str]:
        return ["MY_IND"]
```

2. Add to `config.yaml`:

```yaml
indicators:
  list:
    - name: my_indicator
      params:
        period: 20
```

3. Use in fusion rules:

```yaml
strategy:
  entry_rules:
    long_entry:
      rule:
        type: "condition"
        indicator: "MY_IND"
        operator: ">"
        value: 0
```

That's it! No need to modify existing code.

### Creating Custom Fusion Templates

Add new templates in `src/strategies/fusion.py`:

```python
elif template == "my_custom_template":
    if side == "long_entry":
        return (
            row.get("indicator1", 0) > threshold1 and
            row.get("indicator2", False)
        )
```

### Multiple Watchlists

Create separate config files for different watchlists:

```bash
python -m src.backtest.comparison --config config/hk_large_cap.yaml
python -m src.realtime.signal_runner --config config/us_tech.yaml
```

### Parameter Optimization

Use the comparison backtest to test different parameter combinations:

```bash
# Test different SuperTrend periods
# Edit config, change atr_period: 7, 10, 14
python -m src.backtest.comparison --config src/config/config.yaml

# Compare results and choose best parameters
```

For more sophisticated optimization, consider using vectorbt's parameter optimization features or implementing a grid search in `src/backtest/comparison.py`.

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
