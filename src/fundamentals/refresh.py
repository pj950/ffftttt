#!/usr/bin/env python
"""
CLI tool to refresh fundamentals cache.

Usage:
    python -m src.fundamentals.refresh --config src/config/config.yaml
"""
import argparse
import sys
import yaml
from pathlib import Path
from datetime import datetime
from src.fundamentals.manager import FundamentalsManager


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Refresh fundamentals cache for watchlist symbols"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="src/config/config.yaml",
        help="Path to config file (default: src/config/config.yaml)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        help="Specific symbols to refresh (default: all from watchlist)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file path (default: auto from cache)"
    )
    
    args = parser.parse_args()
    
    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)
    
    # Get symbols
    symbols = args.symbols
    if not symbols:
        symbols = config.get("watchlist", [])
    
    if not symbols:
        print("No symbols to process. Specify --symbols or add to watchlist in config.")
        sys.exit(1)
    
    print(f"Refreshing fundamentals for {len(symbols)} symbols...")
    print(f"Symbols: {', '.join(symbols)}")
    
    # Initialize manager (without Futu client, will use yfinance fallback)
    fundamentals_config = config.get("fundamentals", {})
    manager = FundamentalsManager(fundamentals_config, futu_client=None)
    
    # Refresh data
    try:
        data = manager.refresh_and_cache(symbols)
        cache_path = manager.cache.get_cache_path()
        
        print(f"\n✓ Cache refreshed successfully")
        print(f"  Cached data for {len(data)} symbols")
        print(f"  Cache file: {cache_path}")
        
        # Build whitelist to show results
        whitelisted, results = manager.build_whitelist(symbols, force_refresh=False)
        
        print(f"\n=== Whitelist Results ===")
        print(f"Passed: {len(whitelisted)}/{len(symbols)}")
        
        for symbol in symbols:
            if symbol in results:
                passes, reason, score = results[symbol]
                status = "✓ PASS" if passes else "✗ FAIL"
                print(f"  {status} {symbol:12} | Score: {score:.2f} | {reason}")
            else:
                print(f"  ✗ FAIL {symbol:12} | No data")
        
        # Clean old caches
        manager.cache.clear_old_caches(keep_days=7)
        
    except Exception as e:
        print(f"\nError refreshing cache: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
