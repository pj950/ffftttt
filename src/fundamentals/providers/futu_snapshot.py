from typing import Dict, List
import pandas as pd
from futu import RET_OK
from src.fundamentals.provider_base import FundamentalsProvider


class FutuSnapshotProvider(FundamentalsProvider):
    """
    Fetch fundamentals from Futu market snapshot and historical data.
    Fetches PE_TTM, PB, MktCap from snapshots and calculates 20-day ADTV from turnover amount.
    """
    
    def __init__(self, futu_client):
        self.futu_client = futu_client
    
    def fetch_basic_metrics(self, symbol: str) -> Dict:
        """
        Fetch basic metrics from Futu.
        
        Returns dict with: pe, pb, market_cap, turnover_20d_avg, volume
        PE is fetched as PE_TTM (trailing twelve months)
        turnover_20d_avg is the 20-day average daily turnover amount in native currency
        """
        metrics = {
            "pe": None,
            "pb": None,
            "market_cap": None,
            "turnover_20d_avg": None,
            "volume": None,
        }
        
        try:
            snapshot = self.futu_client.get_market_snapshot(symbol)
            
            if snapshot:
                # Try to get PE_TTM first, fallback to pe_ratio
                metrics["pe"] = snapshot.get("pe_ttm") or snapshot.get("pe_ratio")
                metrics["pb"] = snapshot.get("pb_ratio")
                # Try various field names for market cap
                metrics["market_cap"] = snapshot.get("market_cap") or snapshot.get("market_val")
                metrics["volume"] = snapshot.get("volume")
            
            # Calculate 20-day average daily turnover amount
            turnover_avg = self._calculate_turnover_20d_avg(symbol)
            metrics["turnover_20d_avg"] = turnover_avg
            
        except Exception as e:
            # Silent fail, returns None values
            pass
        
        return metrics
    
    def fetch_batch_metrics(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch metrics for multiple symbols in batch.
        
        Args:
            symbols: List of stock codes
            
        Returns:
            Dictionary mapping symbol to metrics dict
        """
        result = {}
        for symbol in symbols:
            result[symbol] = self.fetch_basic_metrics(symbol)
        return result
    
    def _calculate_turnover_20d_avg(self, symbol: str) -> float:
        """
        Calculate 20-day average turnover amount from historical data.
        """
        try:
            df = self.futu_client.fetch_historical_kline(
                symbol=symbol,
                ktype="day",
                max_count=20
            )
            
            if df.empty or "turnover" not in df.columns:
                return None
            
            avg_turnover = df["turnover"].tail(20).mean()
            return avg_turnover
            
        except Exception as e:
            return None
