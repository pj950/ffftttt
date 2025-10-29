import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import List
from src.indicators.registry import BaseIndicator, register_indicator


@register_indicator("atr_percentile")
class ATRPercentile(BaseIndicator):
    """
    ATR Percentile - volatility regime filter.
    
    Calculates the percentile rank of current ATR relative to historical ATR.
    Useful for filtering signals based on volatility regime:
    - Low percentile (< 20): Low volatility, potential breakout opportunity
    - Mid percentile (20-80): Normal volatility
    - High percentile (> 80): High volatility, caution advised
    
    Parameters:
        atr_period: Period for ATR calculation (default: 14)
        lookback: Lookback period for percentile calculation (default: 100)
        min_percentile: Minimum percentile for trade acceptance (default: 0.2)
        max_percentile: Maximum percentile for trade acceptance (default: 0.85)
    """
    
    def __init__(
        self,
        atr_period: int = 14,
        lookback: int = 100,
        min_percentile: float = 0.2,
        max_percentile: float = 0.85,
        **kwargs
    ):
        super().__init__(
            atr_period=atr_period,
            lookback=lookback,
            min_percentile=min_percentile,
            max_percentile=max_percentile,
            **kwargs
        )
        self.atr_period = atr_period
        self.lookback = lookback
        self.min_percentile = min_percentile
        self.max_percentile = max_percentile
    
    @property
    def name(self) -> str:
        return "atr_percentile"
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate ATR percentile filter.
        
        Adds columns:
            - ATR: Average True Range
            - ATR_pct: ATR as percentage of close price
            - ATR_percentile: Percentile rank of ATR (0-100)
            - ATR_regime: 'low', 'normal', or 'high'
            - ATR_accept: Boolean, True if within acceptable range
        """
        df_copy = df.copy()
        
        # Calculate ATR
        atr = ta.atr(
            high=df_copy["high"],
            low=df_copy["low"],
            close=df_copy["close"],
            length=self.atr_period
        )
        
        if atr is None:
            df_copy["ATR"] = np.nan
            df_copy["ATR_pct"] = np.nan
            df_copy["ATR_percentile"] = 50
            df_copy["ATR_regime"] = "normal"
            df_copy["ATR_accept"] = True
            return df_copy
        
        df_copy["ATR"] = atr
        
        # Calculate ATR as percentage of price
        df_copy["ATR_pct"] = (df_copy["ATR"] / df_copy["close"]) * 100
        
        # Calculate rolling percentile
        percentile_values = []
        
        for i in range(len(df_copy)):
            if i < self.atr_period:
                percentile_values.append(50)  # Default to middle
            else:
                start_idx = max(0, i - self.lookback + 1)
                window_atr = df_copy["ATR"].iloc[start_idx:i+1]
                
                if pd.notna(df_copy["ATR"].iloc[i]) and len(window_atr.dropna()) > 0:
                    current_atr = df_copy["ATR"].iloc[i]
                    # Calculate percentile: what percentage of values are below current
                    below_count = (window_atr < current_atr).sum()
                    total_count = len(window_atr.dropna())
                    percentile = (below_count / total_count) * 100 if total_count > 0 else 50
                    percentile_values.append(percentile)
                else:
                    percentile_values.append(50)
        
        df_copy["ATR_percentile"] = percentile_values
        
        # Classify regime
        def classify_regime(percentile):
            if percentile < 20:
                return "low"
            elif percentile > 80:
                return "high"
            else:
                return "normal"
        
        df_copy["ATR_regime"] = df_copy["ATR_percentile"].apply(classify_regime)
        
        # Check if within acceptable range
        df_copy["ATR_accept"] = (
            (df_copy["ATR_percentile"] >= self.min_percentile * 100) &
            (df_copy["ATR_percentile"] <= self.max_percentile * 100)
        )
        
        return df_copy
    
    def get_signal_columns(self) -> List[str]:
        return [
            "ATR",
            "ATR_pct",
            "ATR_percentile",
            "ATR_regime",
            "ATR_accept"
        ]
