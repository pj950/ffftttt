from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.fundamentals.cache import FundamentalsCache
from src.fundamentals.scoring import FundamentalsScorer
from src.fundamentals.providers.futu_snapshot import FutuSnapshotProvider
from src.fundamentals.providers.yfinance_fallback import YFinanceFallbackProvider


class FundamentalsManager:
    """
    Manage fundamentals data fetching, caching, and scoring.
    Coordinates between Futu primary data source and yfinance fallback.
    """
    
    def __init__(self, config: Dict, futu_client=None):
        self.config = config
        self.futu_client = futu_client
        self.cache = FundamentalsCache()
        self.scorer = FundamentalsScorer(config)
        
        # Initialize providers
        self.futu_provider = FutuSnapshotProvider(futu_client) if futu_client else None
        self.yf_provider = YFinanceFallbackProvider()
        
        self.enabled = config.get("enabled", True)
        self.refresh_policy = config.get("refresh", "daily")
    
    def get_fundamentals_for_symbols(
        self,
        symbols: List[str],
        force_refresh: bool = False
    ) -> Dict[str, Dict]:
        """
        Get fundamentals data for a list of symbols.
        Uses cache if available and fresh, otherwise fetches from providers.
        
        Args:
            symbols: List of stock symbols
            force_refresh: Force refresh even if cache is fresh
            
        Returns:
            Dictionary mapping symbol to metrics
        """
        if not self.enabled:
            return {symbol: {} for symbol in symbols}
        
        # Check cache
        if not force_refresh and self.cache.is_cache_fresh(self.refresh_policy):
            cached_data = self.cache.load_cache()
            if cached_data and "data" in cached_data:
                # Filter to requested symbols
                result = {}
                for symbol in symbols:
                    if symbol in cached_data["data"]:
                        result[symbol] = cached_data["data"][symbol]
                
                # If all symbols are in cache, return
                if len(result) == len(symbols):
                    return result
        
        # Fetch fresh data
        return self._fetch_fresh_data(symbols)
    
    def _fetch_fresh_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch fresh fundamentals data from providers.
        Uses Futu as primary, yfinance as fallback.
        """
        result = {}
        
        for symbol in symbols:
            metrics = self._fetch_symbol_metrics(symbol)
            result[symbol] = metrics
        
        return result
    
    def _fetch_symbol_metrics(self, symbol: str) -> Dict:
        """
        Fetch metrics for a single symbol.
        Tries Futu first, falls back to yfinance if data is missing.
        """
        metrics = {
            "pe": None,
            "pb": None,
            "market_cap": None,
            "turnover_20d_avg": None,
            "volume": None,
        }
        
        # Try Futu first
        if self.futu_provider:
            futu_metrics = self.futu_provider.fetch_basic_metrics(symbol)
            metrics.update({k: v for k, v in futu_metrics.items() if v is not None})
        
        # Fallback to yfinance for missing data (US/HK markets mainly)
        if self._needs_fallback(metrics, symbol):
            yf_metrics = self.yf_provider.fetch_basic_metrics(symbol)
            # Only update if Futu data was missing
            for key, value in yf_metrics.items():
                if metrics.get(key) is None and value is not None:
                    metrics[key] = value
        
        return metrics
    
    def _needs_fallback(self, metrics: Dict, symbol: str) -> bool:
        """
        Check if we need to use yfinance fallback.
        Only use for US/HK markets if data is missing.
        """
        # Check if any critical field is missing
        missing_data = (
            metrics.get("pe") is None or
            metrics.get("pb") is None or
            metrics.get("market_cap") is None
        )
        
        if not missing_data:
            return False
        
        # Only use yfinance for US/HK markets
        market = self._get_market_from_symbol(symbol)
        return market in ["US", "HK"]
    
    def _get_market_from_symbol(self, symbol: str) -> str:
        """Extract market from symbol (e.g., HK.00700 -> HK)."""
        if "." in symbol:
            return symbol.split(".", 1)[0]
        return "US"  # Default to US for symbols without prefix
    
    def build_whitelist(
        self,
        symbols: List[str],
        force_refresh: bool = False
    ) -> Tuple[List[str], Dict[str, Tuple[bool, str, float]]]:
        """
        Build fundamentals whitelist for given symbols.
        
        Args:
            symbols: List of stock symbols to evaluate
            force_refresh: Force refresh of fundamentals data
            
        Returns:
            Tuple of (whitelisted_symbols, all_results)
            all_results maps symbol to (passes, reason, score)
        """
        if not self.enabled:
            # If disabled, all symbols pass
            return symbols, {s: (True, "fundamentals_disabled", 1.0) for s in symbols}
        
        # Get fundamentals data
        fundamentals = self.get_fundamentals_for_symbols(symbols, force_refresh)
        
        # Calculate market caps for percentile calculation
        all_market_caps = [
            fundamentals[s].get("market_cap")
            for s in symbols
            if s in fundamentals
        ]
        
        # Evaluate each symbol
        results = {}
        whitelisted = []
        
        for symbol in symbols:
            if symbol not in fundamentals:
                results[symbol] = (False, "no_fundamentals_data", 0.0)
                continue
            
            market = self._get_market_from_symbol(symbol)
            metrics = fundamentals[symbol]
            
            passes, reason, score = self.scorer.passes_fundamentals_gate(
                symbol=symbol,
                metrics=metrics,
                market=market,
                all_market_caps=all_market_caps
            )
            
            results[symbol] = (passes, reason, score)
            
            if passes:
                whitelisted.append(symbol)
        
        return whitelisted, results
    
    def refresh_and_cache(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Refresh fundamentals data for symbols and save to cache.
        
        Args:
            symbols: List of symbols to refresh
            
        Returns:
            Dictionary of fundamentals data
        """
        data = self._fetch_fresh_data(symbols)
        
        # Save to cache
        self.cache.save_cache(data)
        
        return data
