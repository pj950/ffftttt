import pytest
import pandas as pd
import numpy as np
from src.indicators.tsi_ewo import (
    calculate_tsi,
    calculate_ewo,
    calculate_ma,
    detect_crossover,
    detect_crossunder,
    add_all_indicators,
)


def test_calculate_tsi():
    """Test TSI calculation."""
    np.random.seed(42)
    prices = pd.Series(np.random.randn(100).cumsum() + 100)
    
    tsi_df = calculate_tsi(prices, long=25, short=13, signal=13)
    
    assert "TSI" in tsi_df.columns
    assert len(tsi_df) == len(prices)
    assert not tsi_df["TSI"].isna().all()


def test_calculate_ewo():
    """Test EWO calculation."""
    np.random.seed(42)
    prices = pd.Series(np.random.randn(100).cumsum() + 100)
    
    ewo = calculate_ewo(prices, fast=5, slow=35)
    
    assert ewo is not None
    assert len(ewo) == len(prices)
    assert ewo.name == "EWO"
    assert not ewo.isna().all()


def test_calculate_ma():
    """Test MA calculation."""
    prices = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
    
    ma = calculate_ma(prices, length=3)
    
    assert ma is not None
    assert len(ma) == len(prices)
    assert not ma.isna().all()
    assert ma.iloc[-1] == pytest.approx(18.0, rel=0.01)


def test_detect_crossover():
    """Test crossover detection."""
    series = pd.Series([-2, -1, 0.5, 1, 2, 1, 0.5, -0.5, -1])
    
    crossovers = detect_crossover(series, threshold=0)
    
    assert crossovers.iloc[2] == True
    assert crossovers.iloc[0] == False
    assert crossovers.iloc[3] == False


def test_detect_crossunder():
    """Test crossunder detection."""
    series = pd.Series([2, 1, 0.5, -0.5, -1, -0.5, 0.5, 1, 2])
    
    crossunders = detect_crossunder(series, threshold=0)
    
    assert crossunders.iloc[3] == True
    assert crossunders.iloc[0] == False
    assert crossunders.iloc[6] == False


def test_add_all_indicators():
    """Test adding all indicators to a DataFrame."""
    np.random.seed(42)
    
    dates = pd.date_range('2023-01-01', periods=100, freq='1h')
    df = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100),
    }, index=dates)
    
    df_with_indicators = add_all_indicators(df)
    
    expected_columns = ['TSI', 'TSI_signal', 'EWO', 'MA', 
                       'TSI_crossover', 'TSI_crossunder',
                       'EWO_crossover', 'EWO_crossunder']
    
    for col in expected_columns:
        assert col in df_with_indicators.columns
    
    assert len(df_with_indicators) == len(df)


def test_indicators_with_insufficient_data():
    """Test indicators with insufficient data."""
    df = pd.DataFrame({
        'open': [100],
        'high': [102],
        'low': [98],
        'close': [100],
        'volume': [1000],
    })
    
    df_with_indicators = add_all_indicators(df)
    
    assert 'TSI' in df_with_indicators.columns
    assert 'EWO' in df_with_indicators.columns
