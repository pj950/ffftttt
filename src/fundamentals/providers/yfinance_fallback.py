from typing import Dict, List
from src.fundamentals.provider_base import FundamentalsProvider


class YFinanceFallbackProvider(FundamentalsProvider):
    """
    Fallback provider using yfinance for US/HK/CN stocks when Futu data is missing.
    Normalizes symbols for US/HK markets and fetches PE (trailing), PB, marketCap.
    Estimates liquidity from volume * price when available.
    """
    
    def __init__(self):
        self.yf = None
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            pass
    
    def fetch_basic_metrics(self, symbol: str) -> Dict:
        """
        Fetch basic metrics from Yahoo Finance.
        
        Returns dict with: pe, pb, market_cap, turnover_20d_avg, volume
        PE is trailingPE (TTM equivalent)
        turnover_20d_avg is estimated from 20-day avg volume * avg price
        """
        metrics = {
            "pe": None,
            "pb": None,
            "market_cap": None,
            "turnover_20d_avg": None,
            "volume": None,
        }
        
        if not self.yf:
            return metrics
        
        try:
            yf_symbol = self._convert_symbol(symbol)
            ticker = self.yf.Ticker(yf_symbol)
            info = ticker.info
            
            # Fetch PE (trailing = TTM), PB, and market cap
            metrics["pe"] = info.get("trailingPE")
            metrics["pb"] = info.get("priceToBook")
            metrics["market_cap"] = info.get("marketCap")
            metrics["volume"] = info.get("volume")
            
            # Estimate 20-day average daily turnover amount (volume * price)
            hist = ticker.history(period="1mo")
            if not hist.empty and "Volume" in hist.columns and "Close" in hist.columns:
                # Calculate daily turnover (volume * close price)
                daily_turnover = hist["Volume"] * hist["Close"]
                # Get 20-day average
                metrics["turnover_20d_avg"] = daily_turnover.tail(20).mean()
            
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
    
    def _convert_symbol(self, symbol: str) -> str:
        """
        Convert Futu symbol format to Yahoo Finance format.
        E.g., HK.00700 -> 0700.HK
        """
        if "." not in symbol:
            return symbol
        
        market, code = symbol.split(".", 1)
        
        if market == "HK":
            return f"{code}.HK"
        elif market == "US":
            return code
        elif market == "CN":
            return f"{code}.SS" if code.startswith("6") else f"{code}.SZ"
        
        return symbol
