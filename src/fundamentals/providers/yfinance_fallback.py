from typing import Dict
from src.fundamentals.provider_base import FundamentalsProvider


class YFinanceFallbackProvider(FundamentalsProvider):
    """
    Fallback provider using yfinance for US/HK stocks.
    Note: This is a placeholder implementation.
    Install yfinance separately if needed: pip install yfinance
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
            
            metrics["pe"] = info.get("trailingPE")
            metrics["pb"] = info.get("priceToBook")
            metrics["market_cap"] = info.get("marketCap")
            metrics["volume"] = info.get("volume")
            
            hist = ticker.history(period="1mo")
            if not hist.empty and "Volume" in hist.columns:
                avg_volume = hist["Volume"].tail(20).mean()
                avg_price = hist["Close"].tail(20).mean()
                metrics["turnover_20d_avg"] = avg_volume * avg_price
            
        except Exception as e:
            pass
        
        return metrics
    
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
