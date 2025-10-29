from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime


class FusionStrategy:
    """
    Extensible fusion strategy that combines multiple indicators.
    
    Supports:
        - Rule-based fusion (AND/OR/threshold conditions)
        - Weight-based fusion (weighted sum of signals)
        - Multiple entry/exit templates
        - Fundamentals gating
    
    Entry/Exit Templates:
        - supertrend_hma: SuperTrend=up AND HMA_slope>0 AND RSI>50
        - supertrend_qqe: SuperTrend=up AND QQE>signal AND ADX>25
        - custom: User-defined rules from config
    """
    
    def __init__(self, config: Dict, fundamentals_manager=None):
        self.config = config
        self.min_confidence = config.get("min_confidence", 0.5)
        self.fusion_mode = config.get("fusion_mode", "rule_based")
        self.entry_rules = config.get("entry_rules", {})
        self.exit_rules = config.get("exit_rules", {})
        self.weights = config.get("weights", {})
        self.filters = config.get("filters", {})
        self.fundamentals_manager = fundamentals_manager
    
    def _evaluate_rule(self, row: pd.Series, rule: Dict) -> bool:
        """
        Evaluate a single rule against a data row.
        
        Rule format:
            {
                "type": "condition",  # or "and", "or"
                "indicator": "ST_trend",
                "operator": "==",  # or ">", "<", ">=", "<=", "!="
                "value": 1,
                "rules": []  # for nested and/or
            }
        """
        rule_type = rule.get("type", "condition")
        
        if rule_type == "and":
            sub_rules = rule.get("rules", [])
            return all(self._evaluate_rule(row, r) for r in sub_rules)
        
        elif rule_type == "or":
            sub_rules = rule.get("rules", [])
            return any(self._evaluate_rule(row, r) for r in sub_rules)
        
        elif rule_type == "condition":
            indicator = rule.get("indicator")
            operator = rule.get("operator", "==")
            value = rule.get("value")
            
            if indicator not in row.index:
                return False
            
            indicator_value = row[indicator]
            
            if pd.isna(indicator_value):
                return False
            
            # Handle boolean columns
            if isinstance(indicator_value, (bool, np.bool_)):
                if operator == "==":
                    return bool(indicator_value) == bool(value)
                else:
                    indicator_value = float(indicator_value)
            
            # Evaluate condition
            if operator == "==":
                return indicator_value == value
            elif operator == "!=":
                return indicator_value != value
            elif operator == ">":
                return indicator_value > value
            elif operator == "<":
                return indicator_value < value
            elif operator == ">=":
                return indicator_value >= value
            elif operator == "<=":
                return indicator_value <= value
            else:
                return False
        
        return False
    
    def _apply_template(self, row: pd.Series, template: str, side: str) -> bool:
        """
        Apply a predefined entry/exit template.
        
        Templates:
            - supertrend_hma: SuperTrend + HMA + RSI
            - supertrend_qqe: SuperTrend + QQE + ADX
            - tsi_ewo: Legacy TSI + EWO
        """
        if template == "supertrend_hma":
            if side == "long_entry":
                return (
                    row.get("ST_trend", 0) == 1 and
                    row.get("HMA_slope", 0) > 0 and
                    row.get("RSI", 50) > 50
                )
            elif side == "long_exit":
                return (
                    row.get("ST_flip_down", False) or
                    row.get("RSI", 50) < 45
                )
            elif side == "short_entry":
                return (
                    row.get("ST_trend", 0) == -1 and
                    row.get("HMA_slope", 0) < 0 and
                    row.get("RSI", 50) < 50
                )
            elif side == "short_exit":
                return (
                    row.get("ST_flip_up", False) or
                    row.get("RSI", 50) > 55
                )
        
        elif template == "supertrend_qqe":
            if side == "long_entry":
                return (
                    row.get("ST_trend", 0) == 1 and
                    row.get("QQE_long", False) and
                    row.get("ADX_strong", False)
                )
            elif side == "long_exit":
                return (
                    row.get("ST_flip_down", False) or
                    row.get("QQE_short", False)
                )
            elif side == "short_entry":
                return (
                    row.get("ST_trend", 0) == -1 and
                    row.get("QQE_short", False) and
                    row.get("ADX_strong", False)
                )
            elif side == "short_exit":
                return (
                    row.get("ST_flip_up", False) or
                    row.get("QQE_long", False)
                )
        
        elif template == "tsi_ewo":
            if side == "long_entry":
                return (
                    row.get("TSI_crossover", False) and
                    row.get("EWO", 0) > 0
                )
            elif side == "long_exit":
                return (
                    row.get("TSI_crossunder", False) or
                    row.get("EWO", 0) < 0
                )
            elif side == "short_entry":
                return (
                    row.get("TSI_crossunder", False) and
                    row.get("EWO", 0) < 0
                )
            elif side == "short_exit":
                return (
                    row.get("TSI_crossover", False) or
                    row.get("EWO", 0) > 0
                )
        
        return False
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals from indicator data.
        
        Args:
            df: DataFrame with OHLCV and indicator data
            
        Returns:
            DataFrame with added signal columns
        """
        df_copy = df.copy()
        
        # Initialize signal columns
        df_copy["long_entry"] = False
        df_copy["long_exit"] = False
        df_copy["short_entry"] = False
        df_copy["short_exit"] = False
        
        if self.fusion_mode == "rule_based":
            # Apply rule-based fusion
            for idx, row in df_copy.iterrows():
                # Long entry
                if "long_entry" in self.entry_rules:
                    entry_config = self.entry_rules["long_entry"]
                    
                    if "template" in entry_config:
                        df_copy.at[idx, "long_entry"] = self._apply_template(
                            row, entry_config["template"], "long_entry"
                        )
                    elif "rule" in entry_config:
                        df_copy.at[idx, "long_entry"] = self._evaluate_rule(
                            row, entry_config["rule"]
                        )
                
                # Long exit
                if "long_exit" in self.exit_rules:
                    exit_config = self.exit_rules["long_exit"]
                    
                    if "template" in exit_config:
                        df_copy.at[idx, "long_exit"] = self._apply_template(
                            row, exit_config["template"], "long_exit"
                        )
                    elif "rule" in exit_config:
                        df_copy.at[idx, "long_exit"] = self._evaluate_rule(
                            row, exit_config["rule"]
                        )
                
                # Short entry
                if "short_entry" in self.entry_rules:
                    entry_config = self.entry_rules["short_entry"]
                    
                    if "template" in entry_config:
                        df_copy.at[idx, "short_entry"] = self._apply_template(
                            row, entry_config["template"], "short_entry"
                        )
                    elif "rule" in entry_config:
                        df_copy.at[idx, "short_entry"] = self._evaluate_rule(
                            row, entry_config["rule"]
                        )
                
                # Short exit
                if "short_exit" in self.exit_rules:
                    exit_config = self.exit_rules["short_exit"]
                    
                    if "template" in exit_config:
                        df_copy.at[idx, "short_exit"] = self._apply_template(
                            row, exit_config["template"], "short_exit"
                        )
                    elif "rule" in exit_config:
                        df_copy.at[idx, "short_exit"] = self._evaluate_rule(
                            row, exit_config["rule"]
                        )
        
        elif self.fusion_mode == "weighted":
            # Apply weighted fusion (simple implementation)
            # Calculate weighted signal strength
            signal_strength = pd.Series(0.0, index=df_copy.index)
            
            for indicator, weight in self.weights.items():
                if indicator in df_copy.columns:
                    # Normalize indicator to -1 to 1 range if needed
                    signal_strength += df_copy[indicator] * weight
            
            # Generate signals based on threshold
            threshold = self.config.get("threshold", 0)
            df_copy["long_entry"] = signal_strength > threshold
            df_copy["short_entry"] = signal_strength < -threshold
            df_copy["long_exit"] = signal_strength < -threshold / 2
            df_copy["short_exit"] = signal_strength > threshold / 2
        
        # Apply filters
        if self.filters.get("use_atr_filter", False):
            if "ATR_accept" in df_copy.columns:
                df_copy["long_entry"] = df_copy["long_entry"] & df_copy["ATR_accept"]
                df_copy["short_entry"] = df_copy["short_entry"] & df_copy["ATR_accept"]
        
        if self.filters.get("use_adx_filter", False):
            if "ADX_strong" in df_copy.columns:
                df_copy["long_entry"] = df_copy["long_entry"] & df_copy["ADX_strong"]
                df_copy["short_entry"] = df_copy["short_entry"] & df_copy["ADX_strong"]
        
        min_volume = self.filters.get("min_volume", 0)
        if min_volume > 0:
            df_copy["long_entry"] = df_copy["long_entry"] & (df_copy["volume"] >= min_volume)
            df_copy["short_entry"] = df_copy["short_entry"] & (df_copy["volume"] >= min_volume)
        
        return df_copy
    
    def calculate_confidence(self, row: pd.Series) -> float:
        """
        Calculate confidence score for a signal.
        
        Factors considered:
            - Indicator alignment
            - Trend strength (ADX)
            - Volatility regime (ATR)
        """
        confidence = 0.0
        components = 0
        
        # SuperTrend contribution
        if "ST_trend" in row.index and pd.notna(row["ST_trend"]):
            if row["ST_trend"] != 0:
                confidence += 0.25
            components += 1
        
        # HMA slope contribution
        if "HMA_slope" in row.index and pd.notna(row["HMA_slope"]):
            slope_strength = min(abs(row["HMA_slope"]) / 0.1, 1.0)
            confidence += slope_strength * 0.2
            components += 1
        
        # RSI contribution
        if "RSI" in row.index and pd.notna(row["RSI"]):
            rsi_deviation = abs(row["RSI"] - 50) / 50
            confidence += rsi_deviation * 0.2
            components += 1
        
        # ADX contribution
        if "ADX" in row.index and pd.notna(row["ADX"]):
            adx_strength = min(row["ADX"] / 50, 1.0)
            confidence += adx_strength * 0.2
            components += 1
        
        # QQE contribution
        if "QQE_long" in row.index or "QQE_short" in row.index:
            if row.get("QQE_long", False) or row.get("QQE_short", False):
                confidence += 0.15
            components += 1
        
        # Normalize if we have fewer components
        if components > 0 and components < 5:
            confidence = confidence * (5 / components)
        
        return min(confidence, 1.0)
    
    def get_signal_reason(self, row: pd.Series, side: str) -> str:
        """
        Generate human-readable reason for a signal.
        """
        reasons = []
        
        if side == "LONG":
            if row.get("ST_trend", 0) == 1:
                reasons.append("ST↑")
            if row.get("HMA_slope", 0) > 0:
                reasons.append(f"HMA↗{row.get('HMA_slope_pct', 0):.2f}%")
            if "RSI" in row.index:
                reasons.append(f"RSI={row['RSI']:.0f}")
            if row.get("QQE_long", False):
                reasons.append("QQE+")
            if row.get("ADX_strong", False):
                reasons.append(f"ADX={row.get('ADX', 0):.0f}")
        
        elif side == "SHORT":
            if row.get("ST_trend", 0) == -1:
                reasons.append("ST↓")
            if row.get("HMA_slope", 0) < 0:
                reasons.append(f"HMA↘{row.get('HMA_slope_pct', 0):.2f}%")
            if "RSI" in row.index:
                reasons.append(f"RSI={row['RSI']:.0f}")
            if row.get("QQE_short", False):
                reasons.append("QQE-")
            if row.get("ADX_strong", False):
                reasons.append(f"ADX={row.get('ADX', 0):.0f}")
        
        return ", ".join(reasons) if reasons else "signal_triggered"
    
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
