from abc import ABC, abstractmethod
from typing import Dict, Optional


class FundamentalsProvider(ABC):
    """
    Base class for fundamentals data providers.
    """
    
    @abstractmethod
    def fetch_basic_metrics(self, symbol: str) -> Dict:
        """
        Fetch basic fundamental metrics for a symbol.
        
        Args:
            symbol: Stock code
            
        Returns:
            Dictionary with keys:
                - pe: Price-to-Earnings ratio
                - pb: Price-to-Book ratio
                - market_cap: Market capitalization
                - turnover_20d_avg: 20-day average daily turnover amount
                - volume: Current volume
        """
        pass
