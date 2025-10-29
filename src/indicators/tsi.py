import pandas as pd
import numpy as np
from typing import List
from src.indicators.registry import BaseIndicator, register_indicator
from src.indicators.tsi_ewo import calculate_tsi


@register_indicator("tsi")
class TSI(BaseIndicator):
    """
    True Strength Index (TSI) indicator.
    
    TSI measures momentum by comparing double-smoothed price changes
    to double-smoothed absolute price changes.
    
    Parameters:
        long: Long period for first smoothing (default: 25)
        short: Short period for second smoothing (default: 13)
        signal: Signal line period (default: 13)
    """
    
    def __init__(self, long: int = 25, short: int = 13, signal: int = 13, **kwargs):
        super().__init__(long=long, short=short, signal=signal, **kwargs)
        self.long = long
        self.short = short
        self.signal = signal
    
    @property
    def name(self) -> str:
        return "tsi"
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate TSI indicator.
        
        Adds columns:
            - TSI: TSI value
            - TSI_signal: Signal line
            - TSI_crossover: TSI crosses above 0
            - TSI_crossunder: TSI crosses below 0
        """
        df_copy = df.copy()
        
        tsi_df = calculate_tsi(
            df_copy["close"],
            long=self.long,
            short=self.short,
            signal=self.signal
        )
        
        df_copy["TSI"] = tsi_df["TSI"] if "TSI" in tsi_df.columns else np.nan
        df_copy["TSI_signal"] = tsi_df[f"TSIs_{self.signal}"] if f"TSIs_{self.signal}" in tsi_df.columns else np.nan
        
        # Calculate crossovers
        df_copy["TSI_crossover"] = (
            (df_copy["TSI"] > 0) &
            (df_copy["TSI"].shift(1) <= 0)
        ).fillna(False)
        
        df_copy["TSI_crossunder"] = (
            (df_copy["TSI"] < 0) &
            (df_copy["TSI"].shift(1) >= 0)
        ).fillna(False)
        
        return df_copy
    
    def get_signal_columns(self) -> List[str]:
        return ["TSI", "TSI_signal", "TSI_crossover", "TSI_crossunder"]
