import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import List
from src.indicators.registry import BaseIndicator, register_indicator


@register_indicator("adx")
class ADX(BaseIndicator):
    """
    Average Directional Index (ADX) - trend strength indicator.
    
    ADX measures the strength of a trend, not its direction.
    Values above 25 typically indicate a strong trend.
    Values below 20 indicate a weak or absent trend.
    
    Also calculates +DI and -DI for directional information.
    
    Parameters:
        period: Period for ADX calculation (default: 14)
        threshold: Threshold for strong trend (default: 25)
    """
    
    def __init__(self, period: int = 14, threshold: float = 25, **kwargs):
        super().__init__(period=period, threshold=threshold, **kwargs)
        self.period = period
        self.threshold = threshold
    
    @property
    def name(self) -> str:
        return "adx"
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate ADX indicator.
        
        Adds columns:
            - ADX: ADX value (trend strength)
            - DI_plus: Positive Directional Indicator
            - DI_minus: Negative Directional Indicator
            - ADX_strong: Boolean, True when ADX > threshold
            - ADX_trending: Boolean, True when ADX > threshold and +DI > -DI (uptrend)
            - ADX_trending_down: Boolean, True when ADX > threshold and -DI > +DI (downtrend)
        """
        df_copy = df.copy()
        
        # Calculate ADX using pandas_ta
        adx_df = ta.adx(
            high=df_copy["high"],
            low=df_copy["low"],
            close=df_copy["close"],
            length=self.period
        )
        
        if adx_df is None or adx_df.empty:
            df_copy["ADX"] = np.nan
            df_copy["DI_plus"] = np.nan
            df_copy["DI_minus"] = np.nan
            df_copy["ADX_strong"] = False
            df_copy["ADX_trending"] = False
            df_copy["ADX_trending_down"] = False
            return df_copy
        
        # Extract columns
        adx_col = f"ADX_{self.period}"
        di_plus_col = f"DMP_{self.period}"
        di_minus_col = f"DMN_{self.period}"
        
        df_copy["ADX"] = adx_df[adx_col] if adx_col in adx_df.columns else np.nan
        df_copy["DI_plus"] = adx_df[di_plus_col] if di_plus_col in adx_df.columns else np.nan
        df_copy["DI_minus"] = adx_df[di_minus_col] if di_minus_col in adx_df.columns else np.nan
        
        # Calculate derived signals
        df_copy["ADX_strong"] = df_copy["ADX"] > self.threshold
        df_copy["ADX_trending"] = (
            (df_copy["ADX"] > self.threshold) &
            (df_copy["DI_plus"] > df_copy["DI_minus"])
        ).fillna(False)
        
        df_copy["ADX_trending_down"] = (
            (df_copy["ADX"] > self.threshold) &
            (df_copy["DI_minus"] > df_copy["DI_plus"])
        ).fillna(False)
        
        # ADX rising indicates strengthening trend
        df_copy["ADX_rising"] = df_copy["ADX"] > df_copy["ADX"].shift(1)
        
        return df_copy
    
    def get_signal_columns(self) -> List[str]:
        return [
            "ADX",
            "DI_plus",
            "DI_minus",
            "ADX_strong",
            "ADX_trending",
            "ADX_trending_down",
            "ADX_rising"
        ]
