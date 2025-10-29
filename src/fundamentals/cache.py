import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class FundamentalsCache:
    """
    Manage caching of fundamentals data.
    Writes to cache/fundamentals_{YYYYMMDD}.json
    """
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_path(self, date: Optional[datetime] = None) -> Path:
        """
        Get the cache file path for a given date.
        
        Args:
            date: Date for the cache file (default: today)
            
        Returns:
            Path to cache file
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y%m%d")
        return self.cache_dir / f"fundamentals_{date_str}.json"
    
    def load_cache(self, date: Optional[datetime] = None) -> Optional[Dict]:
        """
        Load cached fundamentals data for a given date.
        
        Args:
            date: Date to load cache for (default: today)
            
        Returns:
            Dictionary of cached data or None if not found
        """
        cache_path = self.get_cache_path(date)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            # If cache is corrupt, return None
            return None
    
    def save_cache(self, data: Dict, date: Optional[datetime] = None) -> Path:
        """
        Save fundamentals data to cache.
        
        Args:
            data: Dictionary of fundamentals data to cache
            date: Date for the cache file (default: today)
            
        Returns:
            Path to saved cache file
        """
        cache_path = self.get_cache_path(date)
        
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "date": (date or datetime.now()).strftime("%Y-%m-%d"),
            "data": data
        }
        
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        return cache_path
    
    def is_cache_fresh(self, refresh_policy: str = "daily", date: Optional[datetime] = None) -> bool:
        """
        Check if cache is fresh according to refresh policy.
        
        Args:
            refresh_policy: "daily" or other policy
            date: Date to check (default: today)
            
        Returns:
            True if cache is fresh, False if it needs refresh
        """
        if refresh_policy == "daily":
            cache_path = self.get_cache_path(date)
            return cache_path.exists()
        
        # For other policies, always refresh
        return False
    
    def clear_old_caches(self, keep_days: int = 7):
        """
        Clear cache files older than keep_days.
        
        Args:
            keep_days: Number of days of cache to keep
        """
        if not self.cache_dir.exists():
            return
        
        cutoff_date = datetime.now().timestamp() - (keep_days * 86400)
        
        for cache_file in self.cache_dir.glob("fundamentals_*.json"):
            try:
                if cache_file.stat().st_mtime < cutoff_date:
                    cache_file.unlink()
            except Exception:
                pass
