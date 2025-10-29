# Configuration Examples

This directory contains example configurations demonstrating different use cases of the fusion strategy system.

## Files

### `config_fusion_example.yaml`
**Use Case**: Standard intraday trading with SuperTrend + HMA + RSI

**Best For**:
- HK market stocks
- 1h and 2h timeframes
- Moderate risk tolerance
- Balanced approach

**Key Features**:
- SuperTrend for trend identification
- HMA for faster response to price changes
- RSI for momentum confirmation
- ATR percentile filter to avoid extreme volatility
- Fundamentals gating enabled

**To Run**:
```bash
# Backtest
python -m src.backtest.comparison --config examples/config_fusion_example.yaml

# Real-time
python -m src.realtime.signal_runner --config examples/config_fusion_example.yaml
```

---

### `config_custom_rules.yaml`
**Use Case**: US tech stocks with custom multi-condition logic

**Best For**:
- US market (AAPL, MSFT, GOOGL, etc.)
- Trend-following approach
- Advanced users who want granular control
- Strong trend requirements (ADX filter)

**Key Features**:
- Custom AND/OR rule combinations
- Requires strong trend (ADX > 25)
- Flexible entry logic (either HMA or RSI can trigger)
- No fundamentals filter (US stocks)
- Longer cooldown (6 hours)

**To Run**:
```bash
# Backtest
python -m src.backtest.comparison --config examples/config_custom_rules.yaml

# Real-time
python -m src.realtime.signal_runner --config examples/config_custom_rules.yaml
```

---

## Creating Your Own Config

### Step 1: Copy a Template

```bash
cp examples/config_fusion_example.yaml my_config.yaml
```

### Step 2: Customize Parameters

**For More Aggressive Trading** (more signals, higher risk):
```yaml
indicators:
  list:
    - name: supertrend
      params:
        atr_period: 7        # Shorter period = more sensitive
        multiplier: 2.0      # Lower multiplier = more signals
    
    - name: hma
      params:
        period: 9            # Shorter period = faster response

strategy:
  min_confidence: 0.4        # Lower threshold = more signals
  
  filters:
    use_adx_filter: false    # Don't require strong trend
```

**For More Conservative Trading** (fewer signals, lower risk):
```yaml
indicators:
  list:
    - name: supertrend
      params:
        atr_period: 14       # Longer period = less sensitive
        multiplier: 4.0      # Higher multiplier = fewer signals
    
    - name: hma
      params:
        period: 21           # Longer period = smoother

strategy:
  min_confidence: 0.7        # Higher threshold = fewer signals
  
  filters:
    use_adx_filter: true     # Require strong trend
```

### Step 3: Backtest First

Always backtest before using live:

```bash
python -m src.backtest.comparison --config my_config.yaml
```

Review the results:
- Look for positive Sharpe ratio (> 1.0)
- Check max drawdown is acceptable
- Verify win rate is reasonable (> 50%)
- Ensure enough trades for statistical significance

### Step 4: Paper Trade

Run in real-time but don't act on signals:

```bash
# Run once to test
python -m src.realtime.signal_runner --config my_config.yaml --once

# Or run continuously
python -m src.realtime.signal_runner --config my_config.yaml
```

Monitor signals for a few days before making any decisions.

---

## Parameter Tuning Guide

### SuperTrend

| Parameter | Lower Value | Higher Value |
|-----------|-------------|--------------|
| `atr_period` | More sensitive, more signals | Less sensitive, fewer signals |
| `multiplier` | Tighter stops, more flips | Wider stops, fewer flips |

**Recommended Ranges**:
- Scalping: `atr_period: 7-10, multiplier: 2.0-2.5`
- Day Trading: `atr_period: 10-14, multiplier: 3.0-3.5`
- Swing Trading: `atr_period: 14-20, multiplier: 4.0-5.0`

### HMA

| Parameter | Lower Value | Higher Value |
|-----------|-------------|--------------|
| `period` | Faster, noisier | Slower, smoother |
| `slope_period` | More slope changes | Fewer slope changes |

**Recommended Ranges**:
- Fast: `period: 9-12, slope_period: 2-3`
- Medium: `period: 16-21, slope_period: 3-5`
- Slow: `period: 25-30, slope_period: 5-7`

### RSI

| Parameter | Lower Value | Higher Value |
|-----------|-------------|--------------|
| `period` | More sensitive | Less sensitive |
| `overbought` | More signals | Fewer signals |
| `oversold` | More signals | Fewer signals |

**Standard**: `period: 14, overbought: 70, oversold: 30`

### ADX

| Parameter | Lower Value | Higher Value |
|-----------|-------------|--------------|
| `threshold` | Accept weaker trends | Require stronger trends |

**Recommended**:
- Trend following: `threshold: 20-25`
- Strong trend only: `threshold: 30-40`

---

## Market-Specific Recommendations

### Hong Kong (HK)

```yaml
market:
  region: "HK"
  timezone: "Asia/Hong_Kong"

timeframes:
  - "60min"
  - "120min"

indicators:
  list:
    - name: supertrend
      params:
        atr_period: 10
        multiplier: 3.0

strategy:
  entry_rules:
    long_entry:
      template: "supertrend_hma"
  
  filters:
    min_volume: 100000
    use_atr_filter: true

fundamentals:
  enabled: true
  thresholds:
    liquidity:
      min: 50000000  # 50M HKD
```

### United States (US)

```yaml
market:
  region: "US"
  timezone: "America/New_York"

timeframes:
  - "60min"
  - "240min"  # 4h for US works well

indicators:
  list:
    - name: supertrend
      params:
        atr_period: 10
        multiplier: 3.0

strategy:
  entry_rules:
    long_entry:
      template: "supertrend_qqe"  # QQE works well for US
  
  filters:
    min_volume: 500000
    use_adx_filter: true

fundamentals:
  enabled: false  # Or set up US-specific thresholds
```

### China (CN)

```yaml
market:
  region: "CN"
  timezone: "Asia/Shanghai"

timeframes:
  - "60min"
  - "120min"

indicators:
  list:
    - name: supertrend
      params:
        atr_period: 12  # CN market can be more volatile
        multiplier: 3.5

strategy:
  entry_rules:
    long_entry:
      template: "supertrend_hma"
  
  filters:
    min_volume: 200000
    use_atr_filter: true

fundamentals:
  enabled: true
  thresholds:
    liquidity:
      min: 100000000  # 100M CNY
```

---

## Testing Different Strategies

Create multiple config files and compare:

```bash
# Test 1: SuperTrend + HMA
cp examples/config_fusion_example.yaml test_st_hma.yaml
# Edit: use template "supertrend_hma"

# Test 2: SuperTrend + QQE
cp examples/config_fusion_example.yaml test_st_qqe.yaml
# Edit: use template "supertrend_qqe"

# Test 3: Legacy TSI/EWO
cp src/config/config.yaml test_tsi_ewo.yaml
# Edit: set strategy.type to "tsi_ewo"

# Run comparisons
python -m src.backtest.comparison --config test_st_hma.yaml > results_st_hma.txt
python -m src.backtest.comparison --config test_st_qqe.yaml > results_st_qqe.txt
python -m src.backtest.run_backtest --config test_tsi_ewo.yaml > results_tsi_ewo.txt

# Compare results
cat results_*.txt
```

---

## Common Patterns

### Pattern 1: Fast Scalping
- Short SuperTrend period (7-8)
- Short HMA period (9-12)
- Low confidence threshold (0.3-0.4)
- No ADX filter
- Small position size (5-10%)

### Pattern 2: Day Trading
- Medium SuperTrend period (10-12)
- Medium HMA period (16-21)
- Medium confidence threshold (0.5-0.6)
- Optional ADX filter
- Medium position size (10-15%)

### Pattern 3: Swing Trading
- Long SuperTrend period (14-20)
- Long HMA period (21-30)
- High confidence threshold (0.6-0.8)
- ADX filter required
- Larger position size (15-20%)

---

## Troubleshooting

### Too Many Signals
- Increase `min_confidence`
- Increase SuperTrend `multiplier`
- Enable `use_adx_filter`
- Increase `min_volume`

### Too Few Signals
- Decrease `min_confidence`
- Decrease SuperTrend `multiplier`
- Disable `use_adx_filter`
- Use shorter indicator periods

### Signals Too Late
- Decrease SuperTrend `atr_period`
- Decrease HMA `period`
- Use faster templates (supertrend_hma instead of supertrend_qqe)

### Too Many False Signals
- Enable `use_adx_filter`
- Enable `use_atr_filter`
- Increase `min_confidence`
- Use longer indicator periods

---

## Best Practices

1. **Start Conservative**: Begin with higher thresholds and fewer signals
2. **Backtest First**: Always validate on historical data
3. **Paper Trade**: Monitor live signals before acting
4. **Version Control**: Keep track of config changes
5. **Document Changes**: Note why you changed parameters
6. **Review Regularly**: Reassess parameters monthly
7. **Market Conditions**: Adjust for changing volatility
8. **Risk Management**: Never risk more than you can afford to lose

---

## Support

For more information:
- Main documentation: [README.md](../README.md)
- Indicator guide: [INDICATOR_GUIDE.md](../INDICATOR_GUIDE.md)
- Implementation details: [IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md)
