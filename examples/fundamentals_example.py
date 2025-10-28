#!/usr/bin/env python
"""
Example of using the fundamentals whitelist in the ffftttt trading system.

This example demonstrates:
1. Loading configuration
2. Creating a FundamentalsManager
3. Checking symbols against the whitelist
4. Building a filtered symbol list
"""
import yaml
from src.fundamentals.manager import FundamentalsManager


def main():
    # Load configuration
    with open("src/config/config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    fundamentals_config = config.get("fundamentals", {})
    watchlist = config.get("watchlist", [])
    
    print("=== Fundamentals Whitelist Example ===\n")
    print(f"Watchlist: {watchlist}")
    print(f"Fundamentals enabled: {fundamentals_config.get('enabled')}")
    print()
    
    # Create manager (without Futu client, will use yfinance fallback)
    manager = FundamentalsManager(fundamentals_config, futu_client=None)
    
    # Build whitelist for watchlist symbols
    print("Building whitelist...")
    whitelisted, results = manager.build_whitelist(watchlist)
    
    print(f"\nResults:")
    print(f"  Total symbols: {len(watchlist)}")
    print(f"  Passed: {len(whitelisted)}")
    print(f"  Failed: {len(watchlist) - len(whitelisted)}")
    print()
    
    # Show detailed results
    print("=== Detailed Results ===\n")
    for symbol in watchlist:
        if symbol in results:
            passes, reason, score = results[symbol]
            status = "✓ PASS" if passes else "✗ FAIL"
            print(f"{status} {symbol:15} | Score: {score:.3f} | {reason}")
        else:
            print(f"? UNKNOWN {symbol:15} | No data available")
    
    print("\n=== Whitelisted Symbols (ready for trading) ===")
    for symbol in whitelisted:
        print(f"  {symbol}")
    
    # Example: Check individual symbol
    print("\n=== Individual Symbol Check ===")
    test_symbol = "HK.00700"
    if test_symbol in watchlist:
        if test_symbol in results:
            passes, reason, score = results[test_symbol]
            print(f"Symbol: {test_symbol}")
            print(f"  Passes gate: {passes}")
            print(f"  Score: {score:.3f}")
            print(f"  Reason: {reason}")
        else:
            print(f"Symbol {test_symbol} has no fundamentals data")
    
    # Show configuration details
    print("\n=== Configuration ===")
    thresholds = fundamentals_config.get("thresholds", {})
    liquidity = thresholds.get("liquidity", {})
    global_thresh = thresholds.get("global", {})
    
    print(f"Liquidity threshold: {liquidity.get('min', 'N/A'):,}")
    print(f"PE range: {global_thresh.get('pe_min', 0)} - {global_thresh.get('pe_max', 'N/A')}")
    print(f"PB max: {global_thresh.get('pb_max', 'N/A')}")
    print(f"Market cap percentile min: {global_thresh.get('cap_percentile_min', 'N/A')}")
    
    # Show cache info
    cache_path = manager.cache.get_cache_path()
    print(f"\nCache location: {cache_path}")
    print(f"Cache exists: {cache_path.exists()}")


if __name__ == "__main__":
    main()
