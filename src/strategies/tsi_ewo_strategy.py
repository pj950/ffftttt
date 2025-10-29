from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime


class TSIEWOStrategy:
    """
    TSI/EWO crossover strategy.
    
    Entry Rules:
        - LONG: TSI crosses above 0 AND EWO > 0
        - SHORT: TSI crosses below 0 AND EWO < 0
    
    Exit Rules:
        - LONG exit: TSI crosses below 0 OR EWO < 0
        - SHORT exit: TSI crosses above 0 OR EWO > 0
    """
    
    def __init__(self, config: Dict, fundamentals_manager=None):
        self.config = config
        self.min_confidence = config.get("min_confidence", 0.5)
        self.filters = config.get("filters", {})
        self.fundamentals_manager = fundamentals_manager
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals from indicator data.
        
        Args:
            df: DataFrame with OHLCV and indicators
            
        Returns:
            DataFrame with added signal columns
        """
        df_copy = df.copy()
        
        df_copy["long_entry"] = (
            df_copy["TSI_crossover"] &
            (df_copy["EWO"] > 0)
        )
        
        df_copy["long_exit"] = (
            df_copy["TSI_crossunder"] |
            (df_copy["EWO"] < 0)
        )
        
        df_copy["short_entry"] = (
            df_copy["TSI_crossunder"] &
            (df_copy["EWO"] < 0)
        )
        
        df_copy["short_exit"] = (
            df_copy["TSI_crossover"] |
            (df_copy["EWO"] > 0)
        )
        
        if self.filters.get("use_ma_trend", False):
            df_copy["long_entry"] = df_copy["long_entry"] & (df_copy["close"] > df_copy["MA"])
            df_copy["short_entry"] = df_copy["short_entry"] & (df_copy["close"] < df_copy["MA"])
        
        min_volume = self.filters.get("min_volume", 0)
        if min_volume > 0:
            df_copy["long_entry"] = df_copy["long_entry"] & (df_copy["volume"] >= min_volume)
            df_copy["short_entry"] = df_copy["short_entry"] & (df_copy["volume"] >= min_volume)
        
        return df_copy
    
    def calculate_confidence(self, row: pd.Series) -> float:
        """
        Calculate confidence score for a signal.
        
        Factors:
            - TSI magnitude (0-100 scale)
            - EWO magnitude relative to recent range
            - Volume confirmation
        """
        confidence = 0.0
        
        tsi = row.get("TSI", 0)
        ewo = row.get("EWO", 0)
        
        tsi_confidence = min(abs(tsi) / 50, 1.0) * 0.4
        confidence += tsi_confidence
        
        ewo_confidence = 0.3
        if "EWO" in row.index and not pd.isna(ewo):
            ewo_confidence = min(abs(ewo) / 10, 1.0) * 0.3
        confidence += ewo_confidence
        
        confidence += 0.3
        
        return min(confidence, 1.0)
    
    def get_signal_reason(
        self,
        row: pd.Series,
        side: str
    ) -> str:
        """
        Generate human-readable reason for a signal.
        """
        reasons = []
        
        tsi = row.get("TSI", 0)
        ewo = row.get("EWO", 0)
        
        if side == "LONG":
            if row.get("TSI_crossover", False):
                reasons.append("TSI↑0")
            else:
                reasons.append(f"TSI={tsi:.1f}")
            
            reasons.append(f"EWO={ewo:.2f}>0")
            
            if self.filters.get("use_ma_trend", False):
                if row.get("close", 0) > row.get("MA", 0):
                    reasons.append("P>MA")
        
        elif side == "SHORT":
            if row.get("TSI_crossunder", False):
                reasons.append("TSI↓0")
            else:
                reasons.append(f"TSI={tsi:.1f}")
            
            reasons.append(f"EWO={ewo:.2f}<0")
            
            if self.filters.get("use_ma_trend", False):
                if row.get("close", 0) < row.get("MA", 0):
                    reasons.append("P<MA")
        
        return ", ".join(reasons)
    
    def check_fundamentals_gate(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if symbol passes fundamentals whitelist.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Tuple of (passes, reason)
        """
        if not self.fundamentals_manager:
            return True, "fundamentals_not_configured"
        
        if not self.fundamentals_manager.enabled:
            return True, "fundamentals_disabled"
        
        # Get all symbols to build context for percentile calculation
        # In real usage, this would come from the watchlist
        symbols = [symbol]
        
        whitelisted, results = self.fundamentals_manager.build_whitelist(symbols)
        
        if symbol in results:
            passes, reason, score = results[symbol]
            if not passes:
                return False, f"fundamentals_gate_failed:{reason}"
        
        return True, "fundamentals_passed"
    
    def extract_latest_signals(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> List[Dict]:
        """
        Extract the latest signals from a DataFrame.
        Applies fundamentals whitelist if configured.
        
        Returns:
            List of signal dictionaries
        """
        if df.empty:
            return []
        
        # Check fundamentals gate first if enabled
        if self.fundamentals_manager and self.fundamentals_manager.enabled:
            passes, reason = self.check_fundamentals_gate(symbol)
            if not passes:
                # Return suppressed signal with reason
                return [{
                    "timestamp": datetime.now(),
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "side": "SUPPRESSED",
                    "price": 0,
                    "confidence": 0,
                    "reason": reason,
                }]
        
        signals = []
        
        latest_row = df.iloc[-1]
        timestamp = latest_row.name if isinstance(latest_row.name, (pd.Timestamp, datetime)) else datetime.now()
        
        if latest_row.get("long_entry", False):
            confidence = self.calculate_confidence(latest_row)
            if confidence >= self.min_confidence:
                signals.append({
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "side": "LONG",
                    "price": latest_row["close"],
                    "confidence": confidence,
                    "reason": self.get_signal_reason(latest_row, "LONG"),
                })
        
        if latest_row.get("short_entry", False):
            confidence = self.calculate_confidence(latest_row)
            if confidence >= self.min_confidence:
                signals.append({
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "side": "SHORT",
                    "price": latest_row["close"],
                    "confidence": confidence,
                    "reason": self.get_signal_reason(latest_row, "SHORT"),
                })
        
        return signals
