# Fundamentals Whitelist Implementation

This document describes the implementation of the fundamentals whitelist feature for the ffftttt trading system.

## Overview

The fundamentals whitelist filters symbols before emitting technical signals based on:
- **Liquidity**: 20-day average daily turnover volume (ADTV) in native currency
- **Valuation**: PE (Price-to-Earnings) and PB (Price-to-Book) ratios
- **Size**: Market capitalization percentile within the watchlist
- **Composite Score**: Weighted combination of the above metrics

## Implementation Files

### Core Modules

1. **src/fundamentals/manager.py**
   - Orchestrates data fetching, caching, and scoring
   - Coordinates between Futu (primary) and yfinance (fallback) providers
   - Builds whitelist for given symbols

2. **src/fundamentals/scoring.py**
   - Implements gating logic for liquidity, valuation, and size
   - Calculates composite scores using configurable weights
   - Supports market-specific overrides (US, HK, CN)
   - Backward compatible with old config format

3. **src/fundamentals/cache.py**
   - Manages daily cache files (`cache/fundamentals_{YYYYMMDD}.json`)
   - Implements refresh policy
   - Auto-cleanup of old cache files

4. **src/fundamentals/refresh.py**
   - CLI tool to pre-build fundamentals cache
   - Usage: `python -m src.fundamentals.refresh --config src/config/config.yaml`
   - Displays whitelist results with pass/fail reasons

### Data Providers

5. **src/fundamentals/providers/futu_snapshot.py**
   - Primary data source using Futu OpenAPI
   - Fetches PE_TTM, PB, market cap from snapshots
   - Calculates 20-day ADTV from historical turnover data
   - Supports batch fetching

6. **src/fundamentals/providers/yfinance_fallback.py**
   - Fallback provider for US/HK markets
   - Uses trailing PE (equivalent to TTM)
   - Estimates liquidity from volume × price
   - Symbol format conversion (e.g., HK.00700 → 0700.HK)

### Integration

7. **src/strategies/tsi_ewo_strategy.py**
   - Enhanced to accept `fundamentals_manager` parameter
   - `check_fundamentals_gate()` method validates symbols
   - `extract_latest_signals()` suppresses signals for non-whitelisted symbols
   - Returns suppressed signals with detailed failure reasons

## Configuration

### New Format (src/config/config.yaml)

```yaml
fundamentals:
  enabled: true
  gate_behavior_on_missing: pass  # "pass" or "block"
  refresh: daily
  
  thresholds:
    liquidity:
      metric: adtv_amount_native
      lookback_days: 20
      min: 50000000  # 50M in native currency
    
    global:
      pe_min: 0
      pe_max: 60
      pb_max: 10
      cap_percentile_min: 0.5  # top 50%
    
    overrides:
      US:
        pe_max: 50
        pb_max: 12
        cap_percentile_min: 0.6  # top 40%
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

### Backward Compatibility

The system maintains full backward compatibility with the old config format:
```yaml
fundamentals:
  enabled: true
  liquidity:
    min_turnover_amount: 50000000
  valuation:
    pe_min: 0
    pe_max: 60
    pb_max: 10
  size:
    min_percentile: 0.5
  scoring:
    size_weight: 0.4
    pe_weight: 0.3
    pb_weight: 0.3
    min_score: 0.5
  missing_data_action: "pass"
```

## Scoring System

### Individual Metrics

1. **PE Score**: `clamp((pe_max - PE) / pe_max, 0, 1)`
   - Lower PE ratios get higher scores
   - Example: PE=30, pe_max=60 → score=0.5

2. **PB Score**: `clamp((pb_max - PB) / pb_max, 0, 1)`
   - Lower PB ratios get higher scores
   - Example: PB=5, pb_max=10 → score=0.5

3. **Size Score**: Market cap percentile within watchlist
   - Example: 66th percentile → score=0.667

### Composite Score

```
Composite = 0.4 × Size_Score + 0.3 × PE_Score + 0.3 × PB_Score
```

Must be ≥ `min_score` (default: 0.5) to pass.

### Gating Logic

Symbols must pass ALL of the following gates:

1. **Liquidity Gate**: 20-day ADTV ≥ 50M (native currency)
2. **PE Gate**: 0 < PE ≤ pe_max (market-specific)
3. **PB Gate**: PB ≤ pb_max (market-specific)
4. **Size Gate**: Market cap percentile ≥ cap_percentile_min (market-specific)
5. **Score Gate**: Composite score ≥ min_score

If any gate fails, the symbol is excluded with a detailed reason.

## Usage

### CLI Tool

Pre-build the fundamentals cache:

```bash
python -m src.fundamentals.refresh --config src/config/config.yaml
```

Output shows which symbols passed/failed and why:
```
✓ PASS HK.00700     | Score: 0.50 | passed
✗ FAIL US.AAPL      | Score: 0.00 | pb_too_high:60.67>12
```

Cache is saved to `cache/fundamentals_{YYYYMMDD}.json`.

### Programmatic Usage

```python
from src.fundamentals.manager import FundamentalsManager
from src.strategies.tsi_ewo_strategy import TSIEWOStrategy

# Load config
config = load_yaml("src/config/config.yaml")
fundamentals_config = config["fundamentals"]

# Create manager
manager = FundamentalsManager(fundamentals_config, futu_client=futu_client)

# Build whitelist
whitelisted, results = manager.build_whitelist(["HK.00700", "US.AAPL"])

# Integrate with strategy
strategy = TSIEWOStrategy(config["strategy"], fundamentals_manager=manager)

# Strategy will automatically filter signals based on whitelist
signals = strategy.extract_latest_signals(df, symbol, timeframe)
```

### Signal Suppression

When a symbol fails the fundamentals gate, the strategy returns a suppressed signal:

```python
{
    "timestamp": "2024-01-15 14:30:00",
    "symbol": "US.AAPL",
    "timeframe": "60min",
    "side": "SUPPRESSED",
    "price": 0,
    "confidence": 0,
    "reason": "fundamentals_gate_failed:pb_too_high:60.67>12"
}
```

Failure reasons include:
- `liquidity_too_low`: Turnover below threshold
- `pe_out_of_range`: PE outside acceptable range
- `pb_too_high`: PB above threshold
- `market_cap_percentile_too_low`: Market cap below percentile threshold
- `composite_score_too_low`: Overall score below minimum

## Testing

### Unit Tests

```bash
# Run all fundamentals tests
pytest tests/test_fundamentals_scoring.py -v

# Run integration tests
pytest tests/test_fundamentals_integration.py -v

# Run all tests
pytest tests/ -v
```

Test coverage includes:
- Liquidity gating (pass/fail)
- Valuation gating (PE/PB out of range)
- Size gating (market cap percentile)
- Market-specific overrides (US, CN, HK)
- Missing data handling (pass/block modes)
- Composite score calculation
- Backward compatibility with old config
- Strategy integration

All 23 tests pass successfully.

### Example Script

```bash
PYTHONPATH=/home/engine/project python examples/fundamentals_example.py
```

Demonstrates:
- Loading configuration
- Building whitelist
- Displaying results with scores and reasons
- Cache management

## Data Flow

1. **Data Fetching**:
   - Futu provider attempts to fetch PE_TTM, PB, market_cap, turnover
   - If data is missing and symbol is US/HK, yfinance fallback is used
   - All data is cached daily

2. **Percentile Calculation**:
   - Market caps collected for all watchlist symbols
   - Percentile calculated per-market (US, HK, CN separately)
   - Market-specific thresholds applied from overrides

3. **Gating & Scoring**:
   - Each symbol evaluated against hard gates (liquidity, PE, PB, size)
   - Composite score calculated from weighted metrics
   - Must pass all gates AND meet minimum score

4. **Strategy Integration**:
   - Strategy checks whitelist before emitting signals
   - Failed symbols return suppressed signal with reason
   - Passed symbols proceed to technical signal generation

## Market-Specific Customization

Different markets have different characteristics:

- **US**: Lower PE threshold (50), higher cap percentile (60%)
  - US tech stocks often trade at higher valuations
  - Want larger, more liquid names

- **HK**: Standard thresholds (PE 60, cap percentile 50%)
  - Balanced approach for HK market

- **CN**: Higher PE tolerance (80)
  - Chinese growth stocks can have higher multiples
  - Still requires good liquidity and size

Customize by editing `thresholds.overrides` in config.yaml.

## Cache Management

- Cache files: `cache/fundamentals_{YYYYMMDD}.json`
- Automatic daily refresh (configurable via `refresh` setting)
- Old caches auto-deleted after 7 days
- Cache includes timestamp and all fetched metrics
- Can force refresh with `force_refresh=True`

## Dependencies

Added to requirements.txt:
- `yfinance>=0.2.0` - For fallback data source

Existing dependencies used:
- `pandas`, `numpy` - Data manipulation
- `futu-api` - Primary data source
- `pyyaml` - Config parsing
- `pytest` - Testing

## Future Enhancements

Possible improvements:
1. Add fundamental trend analysis (improving/deteriorating)
2. Support for more markets (JP, SG, etc.)
3. Historical fundamentals tracking
4. Alert when symbol falls out of whitelist
5. Batch optimization for large watchlists
6. Integration with real-time signal runner
7. Webhook notifications for whitelist changes

## Summary

The fundamentals whitelist provides a robust, configurable system to filter trading signals based on fundamental metrics. It features:

- ✅ Multi-source data (Futu primary, yfinance fallback)
- ✅ Market-specific customization
- ✅ Daily caching with auto-refresh
- ✅ Comprehensive scoring and gating
- ✅ Strategy integration with suppression
- ✅ CLI tool for cache management
- ✅ Full test coverage
- ✅ Backward compatibility
- ✅ Detailed failure reasons

This ensures only quality stocks that meet fundamental criteria can generate trading signals.
