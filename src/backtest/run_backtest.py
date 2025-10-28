import os
import argparse
import yaml
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np
import vectorbt as vbt
from datetime import datetime
from dotenv import load_dotenv

from src.data.futu_client import FutuClient
from src.indicators.tsi_ewo import add_all_indicators
from src.strategies.tsi_ewo_strategy import TSIEWOStrategy


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def run_backtest_for_symbol(
    symbol: str,
    timeframe: str,
    config: Dict,
    futu_client: FutuClient
) -> Dict:
    """
    Run backtest for a single symbol and timeframe.
    
    Returns:
        Dictionary with backtest results
    """
    lookback_days = config.get("lookback_days", 90)
    
    print(f"  Fetching data for {symbol} [{timeframe}]...")
    
    df = futu_client.fetch_intraday_data(
        symbol=symbol,
        days_back=lookback_days,
        base_ktype="1min"
    )
    
    if df.empty:
        print(f"  ⚠️  No data available for {symbol}")
        return None
    
    df_resampled = futu_client.resample_to_timeframe(
        df,
        timeframe=timeframe,
        timezone=config["market"]["timezone"]
    )
    
    if df_resampled.empty or len(df_resampled) < 50:
        print(f"  ⚠️  Insufficient data for {symbol} [{timeframe}]")
        return None
    
    indicator_config = config.get("indicators", {})
    tsi_config = indicator_config.get("tsi", {})
    ewo_config = indicator_config.get("ewo", {})
    
    df_with_indicators = add_all_indicators(
        df_resampled,
        tsi_long=tsi_config.get("long", 25),
        tsi_short=tsi_config.get("short", 13),
        tsi_signal=tsi_config.get("signal", 13),
        ewo_fast=ewo_config.get("fast", 5),
        ewo_slow=ewo_config.get("slow", 35),
    )
    
    strategy_config = config.get("strategy", {})
    strategy = TSIEWOStrategy(strategy_config)
    
    df_with_signals = strategy.generate_signals(df_with_indicators)
    
    backtest_config = config.get("backtest", {})
    
    entries = df_with_signals["long_entry"].fillna(False)
    exits = df_with_signals["long_exit"].fillna(False)
    
    if not entries.any():
        print(f"  ⚠️  No entry signals for {symbol} [{timeframe}]")
        return None
    
    try:
        portfolio = vbt.Portfolio.from_signals(
            close=df_with_signals["close"],
            entries=entries,
            exits=exits,
            init_cash=backtest_config.get("initial_cash", 100000),
            fees=backtest_config.get("fees", 0.001),
            slippage=backtest_config.get("slippage", 0.001),
            size=backtest_config.get("size", 0.1),
            size_type="targetpercent",
            freq="1h"
        )
        
        total_return = portfolio.total_return() * 100
        sharpe_ratio = portfolio.sharpe_ratio()
        max_drawdown = portfolio.max_drawdown() * 100
        win_rate = portfolio.trades.win_rate() if portfolio.trades.count() > 0 else 0
        total_trades = portfolio.trades.count()
        
        cagr = 0
        if len(df_with_signals) > 0:
            years = len(df_with_signals) / (365 * 24 / int(timeframe.replace("min", "")))
            if years > 0:
                cagr = ((1 + total_return / 100) ** (1 / years) - 1) * 100
        
        calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
        
        results = {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_return": total_return,
            "cagr": cagr,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate * 100,
            "total_trades": total_trades,
            "calmar_ratio": calmar,
        }
        
        print(f"  ✅ {symbol} [{timeframe}]: Return={total_return:.2f}%, Sharpe={sharpe_ratio:.2f}, Trades={total_trades}")
        
        return results
        
    except Exception as e:
        print(f"  ⚠️  Backtest failed for {symbol} [{timeframe}]: {e}")
        return None


def run_backtest(config_path: str):
    """
    Run backtests for all symbols and timeframes.
    """
    load_dotenv()
    
    config = load_config(config_path)
    
    print("=" * 60)
    print("TSI/EWO Strategy Backtest")
    print("=" * 60)
    
    output_dir = config.get("backtest", {}).get("output_dir", "backtest_results")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    symbols = config.get("watchlist", [])
    timeframes = config.get("timeframes", ["60min"])
    
    print(f"\nSymbols: {len(symbols)}")
    print(f"Timeframes: {timeframes}")
    print(f"Lookback: {config.get('lookback_days', 90)} days\n")
    
    all_results = []
    
    with FutuClient() as futu_client:
        for symbol in symbols:
            print(f"\n📊 Processing {symbol}...")
            
            for timeframe in timeframes:
                result = run_backtest_for_symbol(
                    symbol=symbol,
                    timeframe=timeframe,
                    config=config,
                    futu_client=futu_client
                )
                
                if result:
                    all_results.append(result)
    
    if not all_results:
        print("\n⚠️  No backtest results to report.")
        return
    
    results_df = pd.DataFrame(all_results)
    
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 60)
    print(results_df.to_string(index=False))
    
    print("\n" + "=" * 60)
    print("AGGREGATE METRICS")
    print("=" * 60)
    print(f"Average Return: {results_df['total_return'].mean():.2f}%")
    print(f"Average CAGR: {results_df['cagr'].mean():.2f}%")
    print(f"Average Sharpe: {results_df['sharpe_ratio'].mean():.2f}")
    print(f"Average Max DD: {results_df['max_drawdown'].mean():.2f}%")
    print(f"Average Win Rate: {results_df['win_rate'].mean():.2f}%")
    print(f"Total Trades: {results_df['total_trades'].sum():.0f}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"{output_dir}/backtest_results_{timestamp}.csv"
    results_df.to_csv(csv_path, index=False)
    print(f"\n✅ Results saved to: {csv_path}")
    
    if config.get("backtest", {}).get("generate_html", False):
        html_path = f"{output_dir}/backtest_results_{timestamp}.html"
        html_content = results_df.to_html(index=False)
        with open(html_path, "w") as f:
            f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Backtest Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>TSI/EWO Strategy Backtest Results</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    {html_content}
</body>
</html>
            """)
        print(f"✅ HTML report saved to: {html_path}")


def main():
    parser = argparse.ArgumentParser(description="Run TSI/EWO strategy backtest")
    parser.add_argument(
        "--config",
        type=str,
        default="src/config/config.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    run_backtest(args.config)


if __name__ == "__main__":
    main()
