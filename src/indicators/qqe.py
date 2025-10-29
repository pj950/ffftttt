import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import List
from src.indicators.registry import BaseIndicator, register_indicator


@register_indicator("qqe")
class QQE(BaseIndicator):
    """
    Quantitative Qualitative Estimation (QQE) indicator.
    
    QQE is a smoother version of RSI with a signal line based on ATR.
    It helps identify trend changes and provides entry/exit signals.
    
    Parameters:
        rsi_period: Period for RSI calculation (default: 14)
        smoothing: Smoothing factor for RSI (default: 5)
        qqe_factor: Multiplier for QQE bands (default: 4.236)
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        smoothing: int = 5,
        qqe_factor: float = 4.236,
        **kwargs
    ):
        super().__init__(
            rsi_period=rsi_period,
            smoothing=smoothing,
            qqe_factor=qqe_factor,
            **kwargs
        )
        self.rsi_period = rsi_period
        self.smoothing = smoothing
        self.qqe_factor = qqe_factor
    
    @property
    def name(self) -> str:
        return "qqe"
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate QQE indicator.
        
        Adds columns:
            - QQE_line: Main QQE line
            - QQE_signal: Signal line
            - QQE_cross_up: QQE crosses above signal
            - QQE_cross_down: QQE crosses below signal
            - QQE_long: QQE above 50 and above signal
            - QQE_short: QQE below 50 and below signal
        """
        df_copy = df.copy()
        
        close = df_copy["close"]
        
        # Calculate RSI
        rsi = ta.rsi(close, length=self.rsi_period)
        
        if rsi is None:
            df_copy["QQE_line"] = 50
            df_copy["QQE_signal"] = 50
            df_copy["QQE_cross_up"] = False
            df_copy["QQE_cross_down"] = False
            df_copy["QQE_long"] = False
            df_copy["QQE_short"] = False
            return df_copy
        
        # Smooth RSI using EMA
        rsi_ma = ta.ema(rsi, length=self.smoothing)
        
        if rsi_ma is None:
            rsi_ma = rsi
        
        # Calculate RSI change for ATR-style calculation
        rsi_change = rsi_ma.diff().abs()
        
        # Calculate Wilders smoothing of RSI change (like ATR)
        dar = ta.ema(rsi_change, length=2 * self.rsi_period - 1)
        
        if dar is None:
            dar = pd.Series(0, index=rsi_ma.index)
        
        # Calculate QQE bands
        qqe_up = rsi_ma + dar * self.qqe_factor
        qqe_down = rsi_ma - dar * self.qqe_factor
        
        # Initialize QQE line
        qqe_line = pd.Series(index=df_copy.index, dtype=float)
        qqe_line.iloc[0] = rsi_ma.iloc[0] if pd.notna(rsi_ma.iloc[0]) else 50
        
        trend = 1  # 1 for uptrend, -1 for downtrend
        
        for i in range(1, len(df_copy)):
            if pd.isna(rsi_ma.iloc[i]):
                qqe_line.iloc[i] = qqe_line.iloc[i-1]
                continue
            
            if trend == 1:
                if rsi_ma.iloc[i] < qqe_down.iloc[i-1]:
                    trend = -1
                    qqe_line.iloc[i] = qqe_up.iloc[i]
                else:
                    qqe_line.iloc[i] = max(qqe_down.iloc[i], qqe_line.iloc[i-1])
            else:
                if rsi_ma.iloc[i] > qqe_up.iloc[i-1]:
                    trend = 1
                    qqe_line.iloc[i] = qqe_down.iloc[i]
                else:
                    qqe_line.iloc[i] = min(qqe_up.iloc[i], qqe_line.iloc[i-1])
        
        df_copy["QQE_line"] = rsi_ma
        df_copy["QQE_signal"] = qqe_line
        
        # Calculate crossovers
        df_copy["QQE_cross_up"] = (
            (df_copy["QQE_line"] > df_copy["QQE_signal"]) &
            (df_copy["QQE_line"].shift(1) <= df_copy["QQE_signal"].shift(1))
        ).fillna(False)
        
        df_copy["QQE_cross_down"] = (
            (df_copy["QQE_line"] < df_copy["QQE_signal"]) &
            (df_copy["QQE_line"].shift(1) >= df_copy["QQE_signal"].shift(1))
        ).fillna(False)
        
        # Calculate long/short conditions
        df_copy["QQE_long"] = (df_copy["QQE_line"] > 50) & (df_copy["QQE_line"] > df_copy["QQE_signal"])
        df_copy["QQE_short"] = (df_copy["QQE_line"] < 50) & (df_copy["QQE_line"] < df_copy["QQE_signal"])
        
        return df_copy
    
    def get_signal_columns(self) -> List[str]:
        return [
            "QQE_line",
            "QQE_signal",
            "QQE_cross_up",
            "QQE_cross_down",
            "QQE_long",
            "QQE_short"
        ]
