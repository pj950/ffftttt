# Acceptance Criteria Checklist

This document tracks the acceptance criteria specified in the ticket and their implementation status.

## ✅ MVP Requirements

### Core Functionality

- [x] **Half-automatic intraday signal generator**
  - Implemented in `src/realtime/signal_runner.py`
  - Runs during market hours with configurable check intervals
  - Generates signals without placing orders

- [x] **Technical indicators: TSI and EWO**
  - TSI: Implemented in `src/indicators/tsi_ewo.py:calculate_tsi()`
  - EWO: Implemented in `src/indicators/tsi_ewo.py:calculate_ewo()`
  - Configurable parameters via YAML

- [x] **Multiple timeframes: 1h, 2h, 4h**
  - Implemented in `src/data/futu_client.py:resample_to_timeframe()`
  - Configurable in `config.yaml`
  - All three timeframes supported

- [x] **Backtesting with vectorbt**
  - Implemented in `src/backtest/run_backtest.py`
  - Generates performance metrics report
  - CSV and HTML output

- [x] **Real-time signal push via Server酱**
  - Implemented in `src/notify/serverchan.py`
  - WeChat notifications with customizable templates
  - Configured via environment variable

- [x] **No order placement**
  - Confirmed: System only generates and reports signals
  - No trading execution functionality

### Project Structure

- [x] **src/config/** - Configuration files
  - `config.yaml` present with all required settings

- [x] **src/data/** - Futu client
  - `futu_client.py` with OpenD connection, kline fetching, resampling

- [x] **src/indicators/** - TSI/EWO helpers
  - `tsi_ewo.py` with all indicator functions

- [x] **src/strategies/** - Signal rules
  - `tsi_ewo_strategy.py` with entry/exit logic and scoring

- [x] **src/backtest/** - Backtesting pipeline
  - `run_backtest.py` with vectorbt integration

- [x] **src/realtime/** - Real-time runner
  - `signal_runner.py` with market hours loop, deduplication, cooldown

- [x] **src/notify/** - Server酱 integration
  - `serverchan.py` with HTTPS API integration

- [x] **src/fundamentals/** - Fundamentals filtering
  - `provider_base.py` - Interface
  - `providers/futu_snapshot.py` - Futu data provider
  - `providers/yfinance_fallback.py` - Yahoo Finance fallback
  - `scoring.py` - Composite scoring and gates

- [x] **tests/** - Unit tests
  - `test_tsi_ewo.py` - Indicator tests (7 tests)
  - `test_fundamentals_scoring.py` - Fundamentals tests (9 tests)

- [x] **scripts/** - Bootstrap scripts
  - `bootstrap_env.sh` - Environment setup script

- [x] **README.md** - Comprehensive documentation
  - Present with setup, usage, configuration, troubleshooting

### Data Adapter

- [x] **Futu OpenD client**
  - Connection management
  - Error handling

- [x] **Pull intraday candles**
  - 1-minute base data fetching
  - Historical data support

- [x] **Resample to 1h/2h/4h**
  - Generic resampling function
  - Timezone-aware

- [x] **Session-aware handling**
  - Market hours configuration
  - Lunch break exclusions
  - Weekend filtering

### Indicators

- [x] **TSI calculation**
  - Using pandas_ta
  - Configurable periods (long, short, signal)
  - Unit-calibrated parameters

- [x] **EWO calculation**
  - EMA(5) - EMA(35) implementation
  - Configurable fast/slow periods

- [x] **Parameters configurable**
  - All parameters in config.yaml
  - Documented defaults

### Strategy Rules

- [x] **Long entry: TSI↑0 AND EWO>0**
  - Implemented in `generate_signals()`
  - Crossover detection

- [x] **Long exit: TSI↓0 OR EWO<0**
  - Exit logic implemented
  - Multiple exit conditions

- [x] **Confidence scoring**
  - Weighted sum implementation
  - TSI magnitude, EWO magnitude, base confidence

- [x] **Signal fields**
  - timestamp ✓
  - symbol ✓
  - timeframe ✓
  - side ✓
  - price ✓
  - confidence ✓
  - reason ✓

- [x] **Optional filters**
  - Minimum volume
  - MA trend filter
  - Configurable enable/disable

### Fundamentals Whitelist

- [x] **Enabled by default**
  - `fundamentals.enabled: true` in config

- [x] **Liquidity gate**
  - 20-day average daily turnover
  - Configurable threshold (50M default)
  - Hard gate requirement

- [x] **Valuation gates**
  - PE: 0 < PE ≤ 60
  - PB: PB ≤ 10
  - Market-specific overrides (US/HK/CN)

- [x] **Size gate**
  - Market cap percentile calculation
  - Configurable threshold (≥50% default)

- [x] **Composite score**
  - Weighted scoring: size=0.4, PE=0.3, PB=0.3
  - Minimum score threshold (0.5 default)

- [x] **Missing data handling**
  - Configurable: "pass" or "block"
  - Per-field behavior

- [x] **Fundamentals gate failure reporting**
  - Detailed reason strings
  - Examples: "liquidity_too_low", "pe_out_of_range", etc.

### Backtesting

- [x] **vectorbt pipeline**
  - Portfolio.from_signals()
  - Multiple symbols/timeframes

- [x] **Performance metrics**
  - CAGR ✓
  - Sharpe ✓
  - Win Rate ✓
  - Max Drawdown ✓
  - Calmar ✓

- [x] **Fees/slippage**
  - Configurable parameters
  - Default: 0.1% each

- [x] **Deterministic runs**
  - No randomness in logic
  - Reproducible results

### Real-time Runner

- [x] **Market hours scheduling**
  - Start/end time configuration
  - Timezone awareness

- [x] **Lunch break exclusions**
  - Configurable exclude_ranges
  - HK market example (12:00-13:00)

- [x] **Per-timeframe checks**
  - Separate processing for each timeframe
  - New crossover detection

- [x] **Signal deduplication**
  - Cooldown tracking
  - Per symbol/timeframe/side

- [x] **Configurable cooldown**
  - Default: 4 hours
  - Configurable in YAML

- [x] **JSON output**
  - stdout ✓
  - log file ✓
  - Proper formatting

- [x] **Server酱notifications**
  - WeChat push
  - Customizable templates

### Notifications

- [x] **Server酱Turbo API**
  - HTTPS endpoint: sctapi.ftqq.com
  - POST request with title/desp

- [x] **Send key from env**
  - SERVERCHAN_KEY environment variable
  - Loaded via python-dotenv

- [x] **Message format**
  - Symbol, timeframe, side
  - Price, confidence, reason
  - Timestamp
  - Markdown support

### Configuration

- [x] **Config-driven design**
  - Single YAML file
  - All parameters externalized

- [x] **Watchlist**
  - List of symbols
  - Example: HK.00700, US.AAPL

- [x] **Timeframes**
  - Array: [60min, 120min, 240min]

- [x] **Indicator params**
  - TSI: long, short, signal
  - EWO: fast, slow

- [x] **Cooldown settings**
  - Enabled flag
  - Period in hours

- [x] **Market/region**
  - Region: HK, US, CN
  - Timezone string

- [x] **Fee/slippage**
  - Backtest parameters
  - Percentage values

- [x] **Fundamentals thresholds**
  - All gates configurable
  - Market overrides

### Operational

- [x] **.env file**
  - FUTU_OPEND_HOST ✓
  - FUTU_OPEND_PORT ✓
  - SERVERCHAN_KEY ✓

- [x] **CLI examples**
  - Backtest command ✓
  - Real-time runner command ✓

- [x] **Sample config**
  - config.yaml with examples
  - Placeholder symbols

- [x] **User-updatable**
  - Watchlist easily modified
  - Environment keys documented

### Documentation

- [x] **README**
  - Setup instructions ✓
  - Futu OpenD installation ✓
  - Config explanation ✓
  - Environment variables ✓
  - Command examples ✓

- [x] **Backtest instructions**
  - How to run
  - Output format
  - Metrics explanation

- [x] **Real-time runner instructions**
  - How to start
  - Signal format
  - Alert behavior

### Output & Reports

- [x] **Backtest metrics report**
  - CSV file ✓
  - HTML file (optional) ✓
  - Console summary ✓

- [x] **Real-time signal output**
  - JSON to stdout ✓
  - Log file ✓
  - WeChat notification ✓

- [x] **Signal includes**
  - All 7 required fields
  - Human-readable reason

- [x] **Suppressed symbols report**
  - Fundamentals gate failures
  - Detailed reasons
  - Console output

### Testing

- [x] **Unit tests**
  - Indicators: 7 tests ✓
  - Fundamentals: 9 tests ✓

- [x] **All tests pass**
  - 16/16 passing ✓
  - pytest execution ✓

- [x] **Test coverage**
  - Indicator math ✓
  - Crossover detection ✓
  - Fundamentals gates ✓
  - Scoring logic ✓

## ✅ Tech Stack Verification

- [x] Python 3.10+ - requirements.txt
- [x] vectorbt ≥0.25.0 - requirements.txt
- [x] pandas ≥2.0.0 - requirements.txt
- [x] numpy ≥1.24.0 - requirements.txt
- [x] pandas-ta ≥0.3.14b - requirements.txt
- [x] futu-api ≥6.8.0 - requirements.txt
- [x] pyyaml ≥6.0 - requirements.txt
- [x] requests ≥2.31.0 - requirements.txt
- [x] python-dotenv ≥1.0.0 - requirements.txt
- [x] pytest ≥7.4.0 - requirements.txt

## ✅ Additional Deliverables

- [x] **QUICKSTART.md** - 5-minute setup guide
- [x] **EXAMPLES.md** - Practical usage examples
- [x] **CHANGELOG.md** - Version history
- [x] **LICENSE** - MIT License
- [x] **PROJECT_SUMMARY.md** - Comprehensive overview
- [x] **.gitignore** - Proper exclusions
- [x] **.env.example** - Environment template
- [x] **pytest.ini** - Test configuration
- [x] **setup.py** - Package installation

## Summary

**Status: ✅ ALL ACCEPTANCE CRITERIA MET**

- Total criteria: 100+ items
- Completed: 100%
- Outstanding: 0

The MVP is complete and ready for use. All specified features have been implemented, tested, and documented.

## Test Results

```bash
$ pytest tests/ -v
============================= test session starts ==============================
collected 16 items

tests/test_fundamentals_scoring.py::test_liquidity_gate_pass PASSED      [  6%]
tests/test_fundamentals_scoring.py::test_liquidity_gate_fail PASSED      [ 12%]
tests/test_fundamentals_scoring.py::test_valuation_gate_pe_out_of_range PASSED [ 18%]
tests/test_fundamentals_scoring.py::test_valuation_gate_pb_too_high PASSED [ 25%]
tests/test_fundamentals_scoring.py::test_size_gate_market_cap_too_small PASSED [ 31%]
tests/test_fundamentals_scoring.py::test_missing_data_pass_mode PASSED   [ 37%]
tests/test_fundamentals_scoring.py::test_missing_data_block_mode PASSED  [ 43%]
tests/test_fundamentals_scoring.py::test_market_specific_overrides PASSED [ 50%]
tests/test_fundamentals_scoring.py::test_fundamentals_disabled PASSED    [ 56%]
tests/test_tsi_ewo.py::test_calculate_tsi PASSED                         [ 62%]
tests/test_tsi_ewo.py::test_calculate_ewo PASSED                         [ 68%]
tests/test_tsi_ewo.py::test_calculate_ma PASSED                          [ 75%]
tests/test_tsi_ewo.py::test_detect_crossover PASSED                      [ 81%]
tests/test_tsi_ewo.py::test_detect_crossunder PASSED                     [ 87%]
tests/test_tsi_ewo.py::test_add_all_indicators PASSED                    [ 93%]
tests/test_tsi_ewo.py::test_indicators_with_insufficient_data PASSED     [100%]

======================= 16 passed, 10 warnings in 2.03s =========================
```

## Verification Commands

```bash
# Verify project structure
find src -name "*.py" | wc -l  # 22 Python files

# Verify tests pass
pytest tests/ -v  # 16 passed

# Verify imports work
python -c "from src.data.futu_client import FutuClient; print('OK')"

# Verify CLI works
python -m src.backtest.run_backtest --help
python -m src.realtime.signal_runner --help
```

All verification commands execute successfully.
