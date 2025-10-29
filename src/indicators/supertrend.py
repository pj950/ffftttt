import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import List
from src.indicators.registry import BaseIndicator, register_indicator


@register_indicator("supertrend")
class SuperTrend(BaseIndicator):
    """
    SuperTrend indicator based on ATR bands.
    
    SuperTrend uses Average True Range (ATR) to create dynamic support/resistance bands.
    When price closes above the upper band, it signals an uptrend.
    When price closes below the lower band, it signals a downtrend.
    
    Parameters:
        atr_period: Period for ATR calculation (default: 10)
        multiplier: Multiplier for ATR bands (default: 3.0)
    """
    
    def __init__(self, atr_period: int = 10, multiplier: float = 3.0, **kwargs):
        super().__init__(atr_period=atr_period, multiplier=multiplier, **kwargs)
        self.atr_period = atr_period
        self.multiplier = multiplier
    
    @property
    def name(self) -> str:
        return "supertrend"
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate SuperTrend indicator.
        
        Adds columns:
            - ST_trend: 1 for uptrend, -1 for downtrend
            - ST_upper: Upper band
            - ST_lower: Lower band
            - ST_signal: Current support/resistance level
            - ST_direction: 1 for long, -1 for short, 0 for neutral
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
            df_copy["ST_trend"] = 0
            df_copy["ST_upper"] = np.nan
            df_copy["ST_lower"] = np.nan
            df_copy["ST_signal"] = np.nan
            df_copy["ST_direction"] = 0
            return df_copy
        
        # Calculate basic bands
        hl_avg = (df_copy["high"] + df_copy["low"]) / 2
        upper_band = hl_avg + (self.multiplier * atr)
        lower_band = hl_avg - (self.multiplier * atr)
        
        # Initialize arrays
        st_trend = np.zeros(len(df_copy))
        final_upper = np.zeros(len(df_copy))
        final_lower = np.zeros(len(df_copy))
        supertrend = np.zeros(len(df_copy))
        
        # Set initial values
        final_upper[0] = upper_band.iloc[0]
        final_lower[0] = lower_band.iloc[0]
        st_trend[0] = 1
        supertrend[0] = final_lower[0]
        
        # Calculate SuperTrend
        for i in range(1, len(df_copy)):
            # Update upper band
            if upper_band.iloc[i] < final_upper[i-1] or df_copy["close"].iloc[i-1] > final_upper[i-1]:
                final_upper[i] = upper_band.iloc[i]
            else:
                final_upper[i] = final_upper[i-1]
            
            # Update lower band
            if lower_band.iloc[i] > final_lower[i-1] or df_copy["close"].iloc[i-1] < final_lower[i-1]:
                final_lower[i] = lower_band.iloc[i]
            else:
                final_lower[i] = final_lower[i-1]
            
            # Determine trend
            if st_trend[i-1] == 1:
                if df_copy["close"].iloc[i] <= final_lower[i]:
                    st_trend[i] = -1
                    supertrend[i] = final_upper[i]
                else:
                    st_trend[i] = 1
                    supertrend[i] = final_lower[i]
            else:
                if df_copy["close"].iloc[i] >= final_upper[i]:
                    st_trend[i] = 1
                    supertrend[i] = final_lower[i]
                else:
                    st_trend[i] = -1
                    supertrend[i] = final_upper[i]
        
        df_copy["ST_trend"] = st_trend
        df_copy["ST_upper"] = final_upper
        df_copy["ST_lower"] = final_lower
        df_copy["ST_signal"] = supertrend
        
        # Calculate direction changes
        df_copy["ST_direction"] = df_copy["ST_trend"]
        df_copy["ST_flip_up"] = (df_copy["ST_trend"] == 1) & (df_copy["ST_trend"].shift(1) == -1)
        df_copy["ST_flip_down"] = (df_copy["ST_trend"] == -1) & (df_copy["ST_trend"].shift(1) == 1)
        
        return df_copy
    
    def get_signal_columns(self) -> List[str]:
        return ["ST_trend", "ST_upper", "ST_lower", "ST_signal", "ST_direction", "ST_flip_up", "ST_flip_down"]
