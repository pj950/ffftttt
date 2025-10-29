import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import List
from src.indicators.registry import BaseIndicator, register_indicator


@register_indicator("rsi")
class RSI(BaseIndicator):
    """
    Relative Strength Index (RSI) indicator.
    
    RSI measures the speed and magnitude of price changes.
    Values above 70 typically indicate overbought conditions.
    Values below 30 typically indicate oversold conditions.
    
    Parameters:
        period: Period for RSI calculation (default: 14)
        overbought: Overbought threshold (default: 70)
        oversold: Oversold threshold (default: 30)
    """
    
    def __init__(
        self,
        period: int = 14,
        overbought: float = 70,
        oversold: float = 30,
        **kwargs
    ):
        super().__init__(
            period=period,
            overbought=overbought,
            oversold=oversold,
            **kwargs
        )
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    @property
    def name(self) -> str:
        return "rsi"
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI indicator.
        
        Adds columns:
            - RSI: RSI value (0-100)
            - RSI_overbought: Boolean, True when RSI > overbought threshold
            - RSI_oversold: Boolean, True when RSI < oversold threshold
            - RSI_bullish: Boolean, True when RSI > 50
            - RSI_bearish: Boolean, True when RSI < 50
        """
        df_copy = df.copy()
        
        rsi = ta.rsi(df_copy["close"], length=self.period)
        
        if rsi is None:
            df_copy["RSI"] = 50
            df_copy["RSI_overbought"] = False
            df_copy["RSI_oversold"] = False
            df_copy["RSI_bullish"] = False
            df_copy["RSI_bearish"] = False
            return df_copy
        
        df_copy["RSI"] = rsi
        
        # Calculate derived signals
        df_copy["RSI_overbought"] = df_copy["RSI"] > self.overbought
        df_copy["RSI_oversold"] = df_copy["RSI"] < self.oversold
        df_copy["RSI_bullish"] = df_copy["RSI"] > 50
        df_copy["RSI_bearish"] = df_copy["RSI"] < 50
        
        return df_copy
    
    def get_signal_columns(self) -> List[str]:
        return [
            "RSI",
            "RSI_overbought",
            "RSI_oversold",
            "RSI_bullish",
            "RSI_bearish"
        ]
