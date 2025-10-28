import pandas as pd
import numpy as np
import pandas_ta as ta


def calculate_tsi(
    close: pd.Series,
    long: int = 25,
    short: int = 13,
    signal: int = 13
) -> pd.DataFrame:
    """
    Calculate True Strength Index (TSI).
    
    TSI = 100 * (Double Smoothed PC) / (Double Smoothed Absolute PC)
    where PC = Price Change
    
    Args:
        close: Close price series
        long: Long period for first smoothing
        short: Short period for second smoothing
        signal: Signal line period
        
    Returns:
        DataFrame with TSI and TSI signal columns
    """
    tsi_df = ta.tsi(close, long=long, short=short, signal=signal)
    
    if tsi_df is None:
        tsi_df = pd.DataFrame(index=close.index)
        tsi_df["TSI"] = np.nan
        tsi_df[f"TSIs_{signal}"] = np.nan
    else:
        tsi_col = f"TSI_{signal}_{long}_{short}"
        signal_col = f"TSIs_{signal}_{long}_{short}"
        
        if tsi_col in tsi_df.columns:
            tsi_df["TSI"] = tsi_df[tsi_col]
        if signal_col in tsi_df.columns:
            tsi_df["TSI_signal"] = tsi_df[signal_col]
    
    return tsi_df


def calculate_ewo(
    close: pd.Series,
    fast: int = 5,
    slow: int = 35
) -> pd.Series:
    """
    Calculate Elliott Wave Oscillator (EWO).
    
    EWO = EMA(fast) - EMA(slow)
    
    Args:
        close: Close price series
        fast: Fast EMA period
        slow: Slow EMA period
        
    Returns:
        Series with EWO values
    """
    ema_fast = ta.ema(close, length=fast)
    ema_slow = ta.ema(close, length=slow)
    
    if ema_fast is None or ema_slow is None:
        ewo = pd.Series(np.nan, index=close.index, name="EWO")
    else:
        ewo = ema_fast - ema_slow
        ewo.name = "EWO"
    
    return ewo


def calculate_ma(close: pd.Series, length: int = 50) -> pd.Series:
    """
    Calculate Simple Moving Average.
    
    Args:
        close: Close price series
        length: MA period
        
    Returns:
        Series with MA values
    """
    ma = ta.sma(close, length=length)
    return ma


def detect_crossover(series: pd.Series, threshold: float = 0) -> pd.Series:
    """
    Detect when a series crosses above a threshold.
    
    Args:
        series: Input series
        threshold: Threshold value
        
    Returns:
        Boolean series: True when crossing above
    """
    above = series > threshold
    above_shifted = above.shift(1).fillna(False)
    crossed = above & ~above_shifted
    return crossed.fillna(False)


def detect_crossunder(series: pd.Series, threshold: float = 0) -> pd.Series:
    """
    Detect when a series crosses below a threshold.
    
    Args:
        series: Input series
        threshold: Threshold value
        
    Returns:
        Boolean series: True when crossing below
    """
    below = series < threshold
    below_shifted = below.shift(1).fillna(False)
    crossed = below & ~below_shifted
    return crossed.fillna(False)


def add_all_indicators(
    df: pd.DataFrame,
    tsi_long: int = 25,
    tsi_short: int = 13,
    tsi_signal: int = 13,
    ewo_fast: int = 5,
    ewo_slow: int = 35,
    ma_length: int = 50
) -> pd.DataFrame:
    """
    Add all technical indicators to a DataFrame.
    
    Args:
        df: DataFrame with OHLCV data
        tsi_long: TSI long period
        tsi_short: TSI short period
        tsi_signal: TSI signal period
        ewo_fast: EWO fast period
        ewo_slow: EWO slow period
        ma_length: MA period
        
    Returns:
        DataFrame with added indicator columns
    """
    df_copy = df.copy()
    
    tsi_df = calculate_tsi(
        df_copy["close"],
        long=tsi_long,
        short=tsi_short,
        signal=tsi_signal
    )
    
    df_copy["TSI"] = tsi_df["TSI"] if "TSI" in tsi_df.columns else np.nan
    df_copy["TSI_signal"] = tsi_df[f"TSIs_{tsi_signal}"] if f"TSIs_{tsi_signal}" in tsi_df.columns else np.nan
    
    df_copy["EWO"] = calculate_ewo(
        df_copy["close"],
        fast=ewo_fast,
        slow=ewo_slow
    )
    
    df_copy["MA"] = calculate_ma(df_copy["close"], length=ma_length)
    
    df_copy["TSI_crossover"] = detect_crossover(df_copy["TSI"], threshold=0)
    df_copy["TSI_crossunder"] = detect_crossunder(df_copy["TSI"], threshold=0)
    df_copy["EWO_crossover"] = detect_crossover(df_copy["EWO"], threshold=0)
    df_copy["EWO_crossunder"] = detect_crossunder(df_copy["EWO"], threshold=0)
    
    return df_copy
