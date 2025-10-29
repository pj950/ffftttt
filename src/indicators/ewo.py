import pandas as pd
import numpy as np
from typing import List
from src.indicators.registry import BaseIndicator, register_indicator
from src.indicators.tsi_ewo import calculate_ewo


@register_indicator("ewo")
class EWO(BaseIndicator):
    """
    Elliott Wave Oscillator (EWO) indicator.
    
    EWO is the difference between two EMAs, typically a fast and a slow one.
    It helps identify wave structure and momentum.
    
    Parameters:
        fast: Fast EMA period (default: 5)
        slow: Slow EMA period (default: 35)
    """
    
    def __init__(self, fast: int = 5, slow: int = 35, **kwargs):
        super().__init__(fast=fast, slow=slow, **kwargs)
        self.fast = fast
        self.slow = slow
    
    @property
    def name(self) -> str:
        return "ewo"
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate EWO indicator.
        
        Adds columns:
            - EWO: EWO value
            - EWO_crossover: EWO crosses above 0
            - EWO_crossunder: EWO crosses below 0
        """
        df_copy = df.copy()
        
        ewo = calculate_ewo(
            df_copy["close"],
            fast=self.fast,
            slow=self.slow
        )
        
        df_copy["EWO"] = ewo
        
        # Calculate crossovers
        df_copy["EWO_crossover"] = (
            (df_copy["EWO"] > 0) &
            (df_copy["EWO"].shift(1) <= 0)
        ).fillna(False)
        
        df_copy["EWO_crossunder"] = (
            (df_copy["EWO"] < 0) &
            (df_copy["EWO"].shift(1) >= 0)
        ).fillna(False)
        
        return df_copy
    
    def get_signal_columns(self) -> List[str]:
        return ["EWO", "EWO_crossover", "EWO_crossunder"]
