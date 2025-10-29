import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import List
from src.indicators.registry import BaseIndicator, register_indicator


@register_indicator("hma")
class HullMovingAverage(BaseIndicator):
    """
    Hull Moving Average (HMA) with slope calculation.
    
    HMA is a fast and smooth moving average that reduces lag.
    Formula: HMA = WMA(2*WMA(n/2) - WMA(n), sqrt(n))
    
    The slope indicates trend direction and strength.
    
    Parameters:
        period: HMA period (default: 16)
        slope_period: Period for slope calculation (default: 3)
    """
    
    def __init__(self, period: int = 16, slope_period: int = 3, **kwargs):
        super().__init__(period=period, slope_period=slope_period, **kwargs)
        self.period = period
        self.slope_period = slope_period
    
    @property
    def name(self) -> str:
        return "hma"
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Hull Moving Average and slope.
        
        Adds columns:
            - HMA: Hull Moving Average value
            - HMA_slope: Slope of HMA (rate of change)
            - HMA_slope_positive: Boolean, True when slope > 0
            - HMA_slope_negative: Boolean, True when slope < 0
        """
        df_copy = df.copy()
        
        close = df_copy["close"]
        
        # Calculate HMA
        hma = ta.hma(close, length=self.period)
        
        if hma is None:
            df_copy["HMA"] = np.nan
            df_copy["HMA_slope"] = 0
            df_copy["HMA_slope_positive"] = False
            df_copy["HMA_slope_negative"] = False
            return df_copy
        
        df_copy["HMA"] = hma
        
        # Calculate slope (rate of change)
        # Using linear regression slope over slope_period
        slope = np.zeros(len(hma))
        
        for i in range(self.slope_period, len(hma)):
            if pd.notna(hma.iloc[i]):
                y = hma.iloc[i-self.slope_period+1:i+1].values
                if len(y) == self.slope_period and not np.any(np.isnan(y)):
                    x = np.arange(self.slope_period)
                    # Simple linear regression
                    x_mean = x.mean()
                    y_mean = y.mean()
                    numerator = np.sum((x - x_mean) * (y - y_mean))
                    denominator = np.sum((x - x_mean) ** 2)
                    if denominator != 0:
                        slope[i] = numerator / denominator
        
        df_copy["HMA_slope"] = slope
        df_copy["HMA_slope_positive"] = df_copy["HMA_slope"] > 0
        df_copy["HMA_slope_negative"] = df_copy["HMA_slope"] < 0
        
        # Normalize slope for better comparison (percentage change)
        df_copy["HMA_slope_pct"] = (df_copy["HMA_slope"] / df_copy["close"]) * 100
        
        return df_copy
    
    def get_signal_columns(self) -> List[str]:
        return ["HMA", "HMA_slope", "HMA_slope_positive", "HMA_slope_negative", "HMA_slope_pct"]
