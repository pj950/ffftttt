import pytest
import pandas as pd
import numpy as np
from src.indicators.registry import (
    BaseIndicator,
    IndicatorRegistry,
    get_registry,
    register_indicator
)


def test_registry_singleton():
    """Test that get_registry returns the same instance."""
    reg1 = get_registry()
    reg2 = get_registry()
    assert reg1 is reg2


def test_available_indicators():
    """Test that indicators are registered."""
    registry = get_registry()
    indicators = registry.get_available_indicators()
    
    # Check that new indicators are registered
    assert "supertrend" in indicators
    assert "hma" in indicators
    assert "qqe" in indicators
    assert "adx" in indicators
    assert "atr_percentile" in indicators
    assert "rsi" in indicators
    assert "tsi" in indicators
    assert "ewo" in indicators


def test_create_indicator():
    """Test creating an indicator instance."""
    registry = get_registry()
    
    # Create SuperTrend indicator
    st = registry.create("supertrend", atr_period=10, multiplier=3.0)
    assert st.name == "supertrend"
    assert st.params["atr_period"] == 10
    assert st.params["multiplier"] == 3.0


def test_create_unknown_indicator():
    """Test that creating unknown indicator raises error."""
    registry = get_registry()
    
    with pytest.raises(ValueError, match="Unknown indicator"):
        registry.create("nonexistent_indicator")


def test_indicator_calculate():
    """Test that indicators can calculate on sample data."""
    # Create sample OHLCV data
    dates = pd.date_range("2024-01-01", periods=100, freq="1h")
    np.random.seed(42)
    
    df = pd.DataFrame({
        "open": 100 + np.random.randn(100).cumsum(),
        "high": 100 + np.random.randn(100).cumsum() + 1,
        "low": 100 + np.random.randn(100).cumsum() - 1,
        "close": 100 + np.random.randn(100).cumsum(),
        "volume": np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # Ensure high >= low
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    
    registry = get_registry()
    
    # Test SuperTrend
    st = registry.create("supertrend", atr_period=10, multiplier=3.0)
    df_st = st.calculate(df)
    assert "ST_trend" in df_st.columns
    assert "ST_signal" in df_st.columns
    
    # Test HMA
    hma = registry.create("hma", period=16, slope_period=3)
    df_hma = hma.calculate(df)
    assert "HMA" in df_hma.columns
    assert "HMA_slope" in df_hma.columns
    
    # Test RSI
    rsi = registry.create("rsi", period=14)
    df_rsi = rsi.calculate(df)
    assert "RSI" in df_rsi.columns
    assert "RSI_bullish" in df_rsi.columns


def test_calculate_all():
    """Test calculating multiple indicators at once."""
    dates = pd.date_range("2024-01-01", periods=100, freq="1h")
    np.random.seed(42)
    
    df = pd.DataFrame({
        "open": 100 + np.random.randn(100).cumsum(),
        "high": 100 + np.random.randn(100).cumsum() + 1,
        "low": 100 + np.random.randn(100).cumsum() - 1,
        "close": 100 + np.random.randn(100).cumsum(),
        "volume": np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    
    registry = get_registry()
    
    indicator_configs = [
        {"name": "supertrend", "params": {"atr_period": 10, "multiplier": 3.0}},
        {"name": "hma", "params": {"period": 16}},
        {"name": "rsi", "params": {"period": 14}}
    ]
    
    df_result = registry.calculate_all(df, indicator_configs)
    
    # Check all indicators are present
    assert "ST_trend" in df_result.columns
    assert "HMA" in df_result.columns
    assert "RSI" in df_result.columns


def test_get_signal_columns():
    """Test that indicators report their output columns."""
    registry = get_registry()
    
    st = registry.create("supertrend")
    columns = st.get_signal_columns()
    assert isinstance(columns, list)
    assert len(columns) > 0
    assert "ST_trend" in columns


def test_custom_indicator_registration():
    """Test registering a custom indicator."""
    
    @register_indicator("test_indicator")
    class TestIndicator(BaseIndicator):
        def __init__(self, param1: int = 10, **kwargs):
            super().__init__(param1=param1, **kwargs)
            self.param1 = param1
        
        @property
        def name(self) -> str:
            return "test_indicator"
        
        def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
            df_copy = df.copy()
            df_copy["TEST"] = self.param1
            return df_copy
        
        def get_signal_columns(self):
            return ["TEST"]
    
    registry = get_registry()
    assert "test_indicator" in registry.get_available_indicators()
    
    test_ind = registry.create("test_indicator", param1=20)
    assert test_ind.param1 == 20
    
    # Test calculation
    df = pd.DataFrame({
        "close": [100, 101, 102],
        "open": [100, 100, 101],
        "high": [101, 102, 103],
        "low": [99, 100, 101],
        "volume": [1000, 1100, 1200]
    })
    
    df_result = test_ind.calculate(df)
    assert "TEST" in df_result.columns
    assert (df_result["TEST"] == 20).all()
