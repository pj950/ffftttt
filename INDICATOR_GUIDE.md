# Indicator & Fusion Strategy Guide

This guide explains how to add new indicators, create custom fusion rules, and extend the signal generation system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Adding a New Indicator](#adding-a-new-indicator)
3. [Creating Fusion Rules](#creating-fusion-rules)
4. [Configuration Examples](#configuration-examples)
5. [Backtesting & Comparison](#backtesting--comparison)

---

## Architecture Overview

The system uses a **registry-based architecture** for indicators and a **fusion strategy layer** for combining signals:

```
┌─────────────────────────────────────────────────────────────┐
│                     Configuration (YAML)                     │
│  - Indicator parameters                                      │
│  - Fusion rules (templates or custom)                       │
│  - Filters (ADX, ATR, volume)                               │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Indicator Registry                        │
│  Dynamically loads and calculates all indicators             │
│  - SuperTrend, HMA, QQE, ADX, RSI, ATR, TSI, EWO           │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     Fusion Strategy                          │
│  Combines indicator signals using:                           │
│  - Rule-based fusion (AND/OR/threshold)                     │
│  - Weighted fusion (configurable weights)                   │
│  - Predefined templates (supertrend_hma, supertrend_qqe)   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Signal Generation                         │
│  Entry/exit signals with confidence scores                   │
│  Fundamentals gating preserved                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Adding a New Indicator

### Step 1: Create the Indicator Class

Create a new file in `src/indicators/` (e.g., `my_indicator.py`):

```python
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import List
from src.indicators.registry import BaseIndicator, register_indicator


@register_indicator("my_indicator")  # Register with unique name
class MyIndicator(BaseIndicator):
    """
    Brief description of your indicator.
    
    Parameters:
        param1: Description (default: value)
        param2: Description (default: value)
    """
    
    def __init__(self, param1: int = 10, param2: float = 2.0, **kwargs):
        super().__init__(param1=param1, param2=param2, **kwargs)
        self.param1 = param1
        self.param2 = param2
    
    @property
    def name(self) -> str:
        return "my_indicator"
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values and add them to the dataframe.
        
        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            
        Returns:
            DataFrame with added indicator columns
        """
        df_copy = df.copy()
        
        # Your indicator calculation here
        # Example: Simple moving average
        df_copy["MY_IND"] = ta.sma(df_copy["close"], length=self.param1)
        df_copy["MY_IND_signal"] = df_copy["MY_IND"] > df_copy["close"]
        
        return df_copy
    
    def get_signal_columns(self) -> List[str]:
        """Return list of column names this indicator produces."""
        return ["MY_IND", "MY_IND_signal"]
```

### Step 2: Register the Indicator

Add the import to `src/indicators/__init__.py`:

```python
from src.indicators.my_indicator import MyIndicator

__all__ = [
    # ... existing exports
    "MyIndicator",
]
```

### Step 3: Add to Configuration

Add your indicator to `src/config/config.yaml`:

```yaml
indicators:
  list:
    - name: my_indicator
      params:
        param1: 20
        param2: 1.5
```

That's it! The indicator will now be automatically loaded and calculated.

---

## Creating Fusion Rules

### Using Predefined Templates

The system includes three built-in templates:

1. **supertrend_hma**: SuperTrend + Hull MA + RSI
2. **supertrend_qqe**: SuperTrend + QQE + ADX
3. **tsi_ewo**: Legacy TSI + EWO

Example configuration:

```yaml
strategy:
  type: "fusion"
  fusion_mode: "rule_based"
  
  entry_rules:
    long_entry:
      template: "supertrend_hma"
  
  exit_rules:
    long_exit:
      template: "supertrend_hma"
```

### Creating Custom Rules

You can define custom rules using a JSON-like structure:

```yaml
strategy:
  type: "fusion"
  fusion_mode: "rule_based"
  
  entry_rules:
    long_entry:
      rule:
        type: "and"  # Combine conditions with AND logic
        rules:
          - type: "condition"
            indicator: "ST_trend"    # SuperTrend direction
            operator: "=="
            value: 1                 # 1 = uptrend
          
          - type: "condition"
            indicator: "HMA_slope"   # Hull MA slope
            operator: ">"
            value: 0                 # Positive slope
          
          - type: "or"               # Nested OR condition
            rules:
              - type: "condition"
                indicator: "RSI"
                operator: ">"
                value: 50
              
              - type: "condition"
                indicator: "QQE_long"
                operator: "=="
                value: true
```

### Available Operators

- `==`: Equal to
- `!=`: Not equal to
- `>`: Greater than
- `<`: Less than
- `>=`: Greater than or equal to
- `<=`: Less than or equal to

### Rule Types

- `condition`: Single indicator condition
- `and`: All sub-rules must be true
- `or`: At least one sub-rule must be true

---

## Configuration Examples

### Example 1: Fast Scalping (SuperTrend + HMA)

```yaml
strategy:
  type: "fusion"
  fusion_mode: "rule_based"
  min_confidence: 0.4
  
  entry_rules:
    long_entry:
      template: "supertrend_hma"
  
  exit_rules:
    long_exit:
      template: "supertrend_hma"
  
  filters:
    min_volume: 100000
    use_atr_filter: true
    use_adx_filter: false

indicators:
  list:
    - name: supertrend
      params:
        atr_period: 7
        multiplier: 2.5
    
    - name: hma
      params:
        period: 9
        slope_period: 2
    
    - name: rsi
      params:
        period: 9
```

### Example 2: Trend Following (SuperTrend + QQE + ADX)

```yaml
strategy:
  type: "fusion"
  fusion_mode: "rule_based"
  min_confidence: 0.6
  
  entry_rules:
    long_entry:
      template: "supertrend_qqe"
  
  exit_rules:
    long_exit:
      template: "supertrend_qqe"
  
  filters:
    min_volume: 200000
    use_atr_filter: true
    use_adx_filter: true

indicators:
  list:
    - name: supertrend
      params:
        atr_period: 10
        multiplier: 3.0
    
    - name: qqe
      params:
        rsi_period: 14
        smoothing: 5
        qqe_factor: 4.236
    
    - name: adx
      params:
        period: 14
        threshold: 25
```

### Example 3: Weighted Fusion

```yaml
strategy:
  type: "fusion"
  fusion_mode: "weighted"
  min_confidence: 0.5
  
  weights:
    ST_trend: 0.30
    HMA_slope: 0.25
    RSI: 0.20
    QQE_line: 0.15
    ADX: 0.10
  
  threshold: 0.5  # Signal threshold
```

---

## Backtesting & Comparison

### Running Comparison Backtests

Compare multiple indicator suites:

```bash
python -m src.backtest.comparison --config src/config/config.yaml
```

This will:
1. Test legacy TSI/EWO strategy
2. Test new fusion strategies
3. Calculate performance metrics
4. Generate comparison report

### Output Metrics

- **Total Return**: Overall profit/loss percentage
- **Sharpe Ratio**: Risk-adjusted return
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Total Trades**: Number of trades executed
- **Average Duration**: Average trade holding time
- **Profit Factor**: Ratio of gross profit to gross loss
- **Signal Lag**: Average bars between price move and signal (lower is better)

### Reading the Results

The comparison will show:

```
IMPROVEMENTS vs TSI/EWO
================================================================================

fusion_supertrend_hma:
  total_return: 📈 +5.23 (+15.2%)
  sharpe_ratio: 📈 +0.31 (+22.1%)
  win_rate: 📈 +8.50 (+14.7%)
  profit_factor: 📈 +0.45 (+28.3%)
  signal_lag: ⚡ -2.30 bars (+38.3% faster)
```

- 📈 = Improvement
- 📉 = Decline
- ⚡ = Faster signals
- 🐌 = Slower signals

---

## Best Practices

### 1. Indicator Design

- **Single Responsibility**: Each indicator should do one thing well
- **Parameter Validation**: Validate parameters in `__init__`
- **Null Handling**: Handle missing data gracefully
- **Performance**: Use vectorized operations where possible

### 2. Fusion Rules

- **Start Simple**: Begin with templates, customize gradually
- **Test Combinations**: Use comparison backtests to validate
- **Avoid Overfitting**: Don't optimize on the same data you test on
- **Consider Correlation**: Avoid redundant indicators

### 3. Configuration

- **Document Parameters**: Add comments explaining each setting
- **Version Control**: Track config changes alongside code
- **Environment-Specific**: Use different configs for dev/prod
- **Backup**: Keep working configurations for rollback

### 4. Backtesting

- **Sufficient Data**: Use at least 90 days for reliable results
- **Multiple Timeframes**: Test on 1h, 2h, and 4h bars
- **Walk-Forward**: Validate on out-of-sample data
- **Reality Check**: Account for fees, slippage, and execution delays

---

## Troubleshooting

### Indicator Not Loading

```python
# Check if indicator is registered
from src.indicators import get_registry
registry = get_registry()
print(registry.get_available_indicators())
```

### Signal Not Generating

1. Check indicator columns exist: `print(df.columns)`
2. Verify rule syntax in config
3. Check min_confidence threshold
4. Review filter settings (ADX, ATR, volume)

### Performance Issues

1. Reduce lookback period for percentile calculations
2. Use simpler indicators (e.g., SMA instead of HMA)
3. Decrease number of indicators
4. Optimize parameter calculations

---

## Advanced Topics

### Creating a New Template

Edit `src/strategies/fusion.py` and add a new template in `_apply_template`:

```python
elif template == "my_custom_template":
    if side == "long_entry":
        return (
            row.get("MY_IND", 0) > 0 and
            row.get("OTHER_IND", False)
        )
```

### Custom Confidence Calculation

Override `calculate_confidence` in your strategy:

```python
def calculate_confidence(self, row: pd.Series) -> float:
    confidence = 0.0
    
    # Your custom logic
    if row.get("MY_IND", 0) > threshold:
        confidence += 0.5
    
    return min(confidence, 1.0)
```

### Walk-Forward Validation

Split your data for proper validation:

```python
# Training period: first 70% of data
# Validation period: last 30% of data

train_size = int(len(df) * 0.7)
df_train = df.iloc[:train_size]
df_test = df.iloc[train_size:]

# Optimize parameters on df_train
# Test on df_test
```

---

## Support

For questions or issues:

1. Check this guide and the main README
2. Review example configs in `src/config/`
3. Run comparison backtests to validate changes
4. Check the logs for error messages

---

## Changelog

- **2024-01**: Initial release with SuperTrend, HMA, QQE, ADX, ATR percentile
- **2024-01**: Added fusion strategy with rule-based and weighted modes
- **2024-01**: Comparison backtest framework with signal lag metrics
