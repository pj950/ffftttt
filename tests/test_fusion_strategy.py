import pytest
import pandas as pd
import numpy as np
from src.strategies.fusion import FusionStrategy


def create_sample_data():
    """Create sample data with indicators."""
    dates = pd.date_range("2024-01-01", periods=50, freq="1h")
    
    df = pd.DataFrame({
        "open": 100 + np.random.randn(50).cumsum() * 0.5,
        "high": 102 + np.random.randn(50).cumsum() * 0.5,
        "low": 98 + np.random.randn(50).cumsum() * 0.5,
        "close": 100 + np.random.randn(50).cumsum() * 0.5,
        "volume": np.random.randint(1000, 10000, 50),
        # Indicator columns
        "ST_trend": [1] * 25 + [-1] * 25,
        "ST_flip_up": [False] * 24 + [True] + [False] * 25,
        "ST_flip_down": [False] * 25 + [True] + [False] * 24,
        "HMA_slope": np.linspace(0.1, -0.1, 50),
        "HMA_slope_pct": np.linspace(0.1, -0.1, 50),
        "RSI": np.linspace(60, 40, 50),
        "QQE_long": [True] * 25 + [False] * 25,
        "QQE_short": [False] * 25 + [True] * 25,
        "ADX": np.linspace(30, 20, 50),
        "ADX_strong": [True] * 30 + [False] * 20,
        "ATR_accept": [True] * 50
    }, index=dates)
    
    return df


def test_fusion_strategy_init():
    """Test FusionStrategy initialization."""
    config = {
        "min_confidence": 0.5,
        "fusion_mode": "rule_based",
        "entry_rules": {},
        "exit_rules": {}
    }
    
    strategy = FusionStrategy(config)
    assert strategy.min_confidence == 0.5
    assert strategy.fusion_mode == "rule_based"


def test_template_supertrend_hma():
    """Test supertrend_hma template."""
    config = {
        "fusion_mode": "rule_based",
        "entry_rules": {
            "long_entry": {"template": "supertrend_hma"}
        },
        "exit_rules": {
            "long_exit": {"template": "supertrend_hma"}
        },
        "min_confidence": 0.3
    }
    
    strategy = FusionStrategy(config)
    df = create_sample_data()
    
    df_signals = strategy.generate_signals(df)
    
    # Check signal columns exist
    assert "long_entry" in df_signals.columns
    assert "long_exit" in df_signals.columns
    
    # Check some signals are generated
    # First part should have long entries (ST_trend=1, HMA_slope>0, RSI>50)
    first_quarter = df_signals.iloc[:12]
    assert first_quarter["long_entry"].any()


def test_template_supertrend_qqe():
    """Test supertrend_qqe template."""
    config = {
        "fusion_mode": "rule_based",
        "entry_rules": {
            "long_entry": {"template": "supertrend_qqe"}
        },
        "exit_rules": {
            "long_exit": {"template": "supertrend_qqe"}
        },
        "min_confidence": 0.3
    }
    
    strategy = FusionStrategy(config)
    df = create_sample_data()
    
    df_signals = strategy.generate_signals(df)
    
    # Check signal columns exist
    assert "long_entry" in df_signals.columns
    assert "long_exit" in df_signals.columns


def test_custom_rule_evaluation():
    """Test custom rule evaluation."""
    config = {
        "fusion_mode": "rule_based",
        "entry_rules": {
            "long_entry": {
                "rule": {
                    "type": "and",
                    "rules": [
                        {
                            "type": "condition",
                            "indicator": "ST_trend",
                            "operator": "==",
                            "value": 1
                        },
                        {
                            "type": "condition",
                            "indicator": "RSI",
                            "operator": ">",
                            "value": 50
                        }
                    ]
                }
            }
        },
        "exit_rules": {},
        "min_confidence": 0.3
    }
    
    strategy = FusionStrategy(config)
    df = create_sample_data()
    
    df_signals = strategy.generate_signals(df)
    
    # First rows should have long entries (ST_trend=1 and RSI>50)
    first_rows = df_signals.iloc[:10]
    assert first_rows["long_entry"].any()
    
    # Last rows should not (ST_trend=-1)
    last_rows = df_signals.iloc[-10:]
    assert not last_rows["long_entry"].any()


def test_or_rule():
    """Test OR rule evaluation."""
    config = {
        "fusion_mode": "rule_based",
        "entry_rules": {
            "long_entry": {
                "rule": {
                    "type": "or",
                    "rules": [
                        {
                            "type": "condition",
                            "indicator": "RSI",
                            "operator": ">",
                            "value": 65
                        },
                        {
                            "type": "condition",
                            "indicator": "QQE_long",
                            "operator": "==",
                            "value": True
                        }
                    ]
                }
            }
        },
        "exit_rules": {},
        "min_confidence": 0.3
    }
    
    strategy = FusionStrategy(config)
    df = create_sample_data()
    
    df_signals = strategy.generate_signals(df)
    
    # Should have signals where either RSI>65 OR QQE_long=True
    assert df_signals["long_entry"].any()


def test_filters():
    """Test signal filters."""
    config = {
        "fusion_mode": "rule_based",
        "entry_rules": {
            "long_entry": {"template": "supertrend_hma"}
        },
        "exit_rules": {},
        "filters": {
            "min_volume": 5000,
            "use_atr_filter": True,
            "use_adx_filter": True
        },
        "min_confidence": 0.3
    }
    
    strategy = FusionStrategy(config)
    df = create_sample_data()
    
    # Set some rows to fail filters
    df.loc[df.index[0], "volume"] = 1000  # Below min_volume
    df.loc[df.index[1], "ATR_accept"] = False
    df.loc[df.index[2], "ADX_strong"] = False
    
    df_signals = strategy.generate_signals(df)
    
    # These rows should not have signals
    assert not df_signals.loc[df.index[0], "long_entry"]
    assert not df_signals.loc[df.index[1], "long_entry"]
    assert not df_signals.loc[df.index[2], "long_entry"]


def test_calculate_confidence():
    """Test confidence calculation."""
    config = {
        "fusion_mode": "rule_based",
        "entry_rules": {},
        "exit_rules": {}
    }
    
    strategy = FusionStrategy(config)
    
    # Create a row with strong signals
    row = pd.Series({
        "ST_trend": 1,
        "HMA_slope": 0.5,
        "RSI": 65,
        "ADX": 35,
        "QQE_long": True
    })
    
    confidence = strategy.calculate_confidence(row)
    assert 0 <= confidence <= 1
    assert confidence > 0.5  # Should be high with all positive indicators


def test_get_signal_reason():
    """Test signal reason generation."""
    config = {
        "fusion_mode": "rule_based",
        "entry_rules": {},
        "exit_rules": {}
    }
    
    strategy = FusionStrategy(config)
    
    row = pd.Series({
        "ST_trend": 1,
        "HMA_slope": 0.5,
        "HMA_slope_pct": 0.2,
        "RSI": 65,
        "ADX": 35,
        "ADX_strong": True,
        "QQE_long": True
    })
    
    reason = strategy.get_signal_reason(row, "LONG")
    assert isinstance(reason, str)
    assert len(reason) > 0
    # Should contain some indicator info
    assert any(x in reason for x in ["ST", "HMA", "RSI", "QQE", "ADX"])


def test_extract_latest_signals():
    """Test extracting latest signals."""
    config = {
        "fusion_mode": "rule_based",
        "entry_rules": {
            "long_entry": {"template": "supertrend_hma"}
        },
        "exit_rules": {},
        "min_confidence": 0.3
    }
    
    strategy = FusionStrategy(config)
    df = create_sample_data()
    
    df_signals = strategy.generate_signals(df)
    
    # Force a signal in the last row
    df_signals.loc[df_signals.index[-1], "long_entry"] = True
    
    signals = strategy.extract_latest_signals(
        df_signals,
        symbol="TEST.SYMBOL",
        timeframe="60min"
    )
    
    assert len(signals) == 1
    assert signals[0]["side"] == "LONG"
    assert signals[0]["symbol"] == "TEST.SYMBOL"
    assert signals[0]["timeframe"] == "60min"
    assert "confidence" in signals[0]
    assert "reason" in signals[0]


def test_empty_dataframe():
    """Test handling empty dataframe."""
    config = {
        "fusion_mode": "rule_based",
        "entry_rules": {},
        "exit_rules": {}
    }
    
    strategy = FusionStrategy(config)
    df = pd.DataFrame()
    
    signals = strategy.extract_latest_signals(df, "TEST", "60min")
    assert signals == []


def test_no_signals():
    """Test when no signals meet confidence threshold."""
    config = {
        "fusion_mode": "rule_based",
        "entry_rules": {
            "long_entry": {"template": "supertrend_hma"}
        },
        "exit_rules": {},
        "min_confidence": 0.99  # Very high threshold
    }
    
    strategy = FusionStrategy(config)
    df = create_sample_data()
    
    df_signals = strategy.generate_signals(df)
    df_signals.loc[df_signals.index[-1], "long_entry"] = True
    
    signals = strategy.extract_latest_signals(df_signals, "TEST", "60min")
    assert len(signals) == 0  # High confidence threshold filters out signals
