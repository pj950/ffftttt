import pytest
import pandas as pd
from src.strategies.tsi_ewo_strategy import TSIEWOStrategy
from src.fundamentals.manager import FundamentalsManager


def test_strategy_with_fundamentals_disabled():
    """Test strategy when fundamentals are disabled."""
    config = {
        "min_confidence": 0.5,
        "filters": {}
    }
    
    fundamentals_config = {
        "enabled": False
    }
    
    manager = FundamentalsManager(fundamentals_config, futu_client=None)
    strategy = TSIEWOStrategy(config, fundamentals_manager=manager)
    
    # Create sample data with signals
    df = pd.DataFrame({
        "close": [100, 101, 102],
        "TSI": [-5, 5, 10],
        "EWO": [1, 2, 3],
        "TSI_crossover": [False, True, False],
        "TSI_crossunder": [False, False, False],
        "volume": [1000000, 1000000, 1000000],
        "long_entry": [False, False, False],
        "short_entry": [False, False, False]
    })
    
    df = strategy.generate_signals(df)
    signals = strategy.extract_latest_signals(df, "HK.00700", "60min")
    
    # With fundamentals disabled, should check technical signals
    # In this case there are no entry signals in the data
    assert isinstance(signals, list)


def test_strategy_with_fundamentals_no_manager():
    """Test strategy when no fundamentals manager is configured."""
    config = {
        "min_confidence": 0.5,
        "filters": {}
    }
    
    strategy = TSIEWOStrategy(config, fundamentals_manager=None)
    
    # Create sample data with signals
    df = pd.DataFrame({
        "close": [100, 101, 102],
        "TSI": [-5, 5, 10],
        "EWO": [1, 2, 3],
        "TSI_crossover": [False, True, False],
        "TSI_crossunder": [False, False, False],
        "volume": [1000000, 1000000, 1000000],
        "long_entry": [False, False, False],
        "short_entry": [False, False, False]
    })
    
    df = strategy.generate_signals(df)
    signals = strategy.extract_latest_signals(df, "HK.00700", "60min")
    
    # Should check technical signals when no manager is configured
    assert isinstance(signals, list)


def test_fundamentals_manager_basic():
    """Test basic fundamentals manager functionality."""
    config = {
        "enabled": True,
        "thresholds": {
            "liquidity": {"min": 50_000_000},
            "global": {
                "pe_min": 0,
                "pe_max": 60,
                "pb_max": 10,
                "cap_percentile_min": 0.5
            },
            "overrides": {}
        },
        "scoring": {
            "weights": {"size": 0.4, "pe": 0.3, "pb": 0.3},
            "min_score": 0.5
        },
        "gate_behavior_on_missing": "pass"
    }
    
    manager = FundamentalsManager(config, futu_client=None)
    
    # Test with sample symbols
    whitelisted, results = manager.build_whitelist(["US.AAPL", "HK.00700"])
    
    # Results should be available
    assert len(results) == 2
    assert "US.AAPL" in results
    assert "HK.00700" in results
