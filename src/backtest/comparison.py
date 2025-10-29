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
from src.indicators import get_registry, load_indicators_from_config
from src.strategies.tsi_ewo_strategy import TSIEWOStrategy
from src.strategies.fusion import FusionStrategy


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def run_backtest_with_strategy(
    df_with_indicators: pd.DataFrame,
    strategy_name: str,
    strategy_config: Dict,
    backtest_config: Dict
) -> Dict:
    """
    Run backtest with a specific strategy.
    
    Returns:
        Dictionary with backtest results
    """
    # Generate signals
    if strategy_name == "tsi_ewo":
        strategy = TSIEWOStrategy(strategy_config)
    elif strategy_name == "fusion":
        strategy = FusionStrategy(strategy_config)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    df_with_signals = strategy.generate_signals(df_with_indicators)
    
    entries = df_with_signals["long_entry"].fillna(False)
    exits = df_with_signals["long_exit"].fillna(False)
    
    if not entries.any():
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
        
        # Calculate average trade duration
        avg_duration = 0
        if portfolio.trades.count() > 0:
            durations = portfolio.trades.duration.values
            avg_duration = np.mean(durations) / pd.Timedelta(hours=1)
        
        # Calculate profit factor
        profit_factor = 0
        if portfolio.trades.count() > 0:
            winning_trades = portfolio.trades.pnl[portfolio.trades.pnl > 0]
            losing_trades = portfolio.trades.pnl[portfolio.trades.pnl < 0]
            
            if len(losing_trades) > 0 and losing_trades.sum() != 0:
                profit_factor = abs(winning_trades.sum() / losing_trades.sum())
        
        results = {
            "strategy": strategy_name,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate * 100,
            "total_trades": total_trades,
            "avg_duration_hours": avg_duration,
            "profit_factor": profit_factor,
        }
        
        return results
        
    except Exception as e:
        print(f"  ⚠️  Backtest failed for {strategy_name}: {e}")
        return None


def calculate_signal_lag(df: pd.DataFrame, signal_col: str = "long_entry") -> float:
    """
    Calculate average signal lag relative to price movements.
    
    This measures how quickly signals react to price changes.
    Lower values indicate less lag.
    """
    if signal_col not in df.columns or not df[signal_col].any():
        return np.nan
    
    signal_indices = df[df[signal_col]].index
    lags = []
    
    for sig_idx in signal_indices:
        # Look back to find when price started moving
        sig_pos = df.index.get_loc(sig_idx)
        if sig_pos < 5:
            continue
        
        lookback = df.iloc[max(0, sig_pos-10):sig_pos]
        if len(lookback) < 5:
            continue
        
        # Calculate returns
        returns = lookback["close"].pct_change()
        
        # Find when the move started (first significant positive return)
        for i, ret in enumerate(returns):
            if ret > 0.01:  # 1% move
                lags.append(len(lookback) - i)
                break
    
    return np.mean(lags) if lags else np.nan


def run_comparison_backtest(
    symbol: str,
    timeframe: str,
    config: Dict,
    futu_client: FutuClient
) -> List[Dict]:
    """
    Run comparison backtest for a single symbol and timeframe.
    
    Tests multiple indicator suites and strategies.
    
    Returns:
        List of backtest results
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
        return []
    
    df_resampled = futu_client.resample_to_timeframe(
        df,
        timeframe=timeframe,
        timezone=config["market"]["timezone"]
    )
    
    if df_resampled.empty or len(df_resampled) < 50:
        print(f"  ⚠️  Insufficient data for {symbol} [{timeframe}]")
        return []
    
    backtest_config = config.get("backtest", {})
    results_list = []
    
    # Test 1: Legacy TSI/EWO strategy
    print(f"    Testing TSI/EWO strategy...")
    indicator_config = config.get("indicators", {})
    tsi_config = indicator_config.get("tsi", {})
    ewo_config = indicator_config.get("ewo", {})
    
    df_tsi_ewo = add_all_indicators(
        df_resampled,
        tsi_long=tsi_config.get("long", 25),
        tsi_short=tsi_config.get("short", 13),
        tsi_signal=tsi_config.get("signal", 13),
        ewo_fast=ewo_config.get("fast", 5),
        ewo_slow=ewo_config.get("slow", 35),
    )
    
    strategy_config = config.get("strategy", {}).copy()
    result_tsi_ewo = run_backtest_with_strategy(
        df_tsi_ewo,
        "tsi_ewo",
        strategy_config,
        backtest_config
    )
    
    if result_tsi_ewo:
        result_tsi_ewo["symbol"] = symbol
        result_tsi_ewo["timeframe"] = timeframe
        result_tsi_ewo["signal_lag"] = calculate_signal_lag(df_tsi_ewo, "long_entry")
        results_list.append(result_tsi_ewo)
        print(f"      ✅ TSI/EWO: Return={result_tsi_ewo['total_return']:.2f}%, Trades={result_tsi_ewo['total_trades']}")
    
    # Test 2: Fusion with SuperTrend + HMA template
    print(f"    Testing SuperTrend+HMA fusion...")
    indicator_configs = load_indicators_from_config(config)
    registry = get_registry()
    df_fusion = registry.calculate_all(df_resampled, indicator_configs)
    
    fusion_config = strategy_config.copy()
    fusion_config["fusion_mode"] = "rule_based"
    fusion_config["entry_rules"] = {
        "long_entry": {"template": "supertrend_hma"},
        "short_entry": {"template": "supertrend_hma"}
    }
    fusion_config["exit_rules"] = {
        "long_exit": {"template": "supertrend_hma"},
        "short_exit": {"template": "supertrend_hma"}
    }
    
    result_fusion_hma = run_backtest_with_strategy(
        df_fusion,
        "fusion",
        fusion_config,
        backtest_config
    )
    
    if result_fusion_hma:
        result_fusion_hma["symbol"] = symbol
        result_fusion_hma["timeframe"] = timeframe
        result_fusion_hma["strategy"] = "fusion_supertrend_hma"
        result_fusion_hma["signal_lag"] = calculate_signal_lag(df_fusion, "long_entry")
        results_list.append(result_fusion_hma)
        print(f"      ✅ Fusion(ST+HMA): Return={result_fusion_hma['total_return']:.2f}%, Trades={result_fusion_hma['total_trades']}")
    
    # Test 3: Fusion with SuperTrend + QQE template
    print(f"    Testing SuperTrend+QQE fusion...")
    fusion_config_qqe = strategy_config.copy()
    fusion_config_qqe["fusion_mode"] = "rule_based"
    fusion_config_qqe["entry_rules"] = {
        "long_entry": {"template": "supertrend_qqe"},
        "short_entry": {"template": "supertrend_qqe"}
    }
    fusion_config_qqe["exit_rules"] = {
        "long_exit": {"template": "supertrend_qqe"},
        "short_exit": {"template": "supertrend_qqe"}
    }
    
    result_fusion_qqe = run_backtest_with_strategy(
        df_fusion,
        "fusion",
        fusion_config_qqe,
        backtest_config
    )
    
    if result_fusion_qqe:
        result_fusion_qqe["symbol"] = symbol
        result_fusion_qqe["timeframe"] = timeframe
        result_fusion_qqe["strategy"] = "fusion_supertrend_qqe"
        result_fusion_qqe["signal_lag"] = calculate_signal_lag(df_fusion, "long_entry")
        results_list.append(result_fusion_qqe)
        print(f"      ✅ Fusion(ST+QQE): Return={result_fusion_qqe['total_return']:.2f}%, Trades={result_fusion_qqe['total_trades']}")
    
    return results_list


def run_comparison(config_path: str):
    """
    Run comparison backtests for all symbols and timeframes.
    """
    load_dotenv()
    
    config = load_config(config_path)
    
    print("=" * 80)
    print("INDICATOR COMPARISON BACKTEST")
    print("=" * 80)
    
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
                results = run_comparison_backtest(
                    symbol=symbol,
                    timeframe=timeframe,
                    config=config,
                    futu_client=futu_client
                )
                
                all_results.extend(results)
    
    if not all_results:
        print("\n⚠️  No backtest results to report.")
        return
    
    results_df = pd.DataFrame(all_results)
    
    # Reorder columns
    column_order = [
        "symbol", "timeframe", "strategy", "total_return", "sharpe_ratio",
        "max_drawdown", "win_rate", "total_trades", "avg_duration_hours",
        "profit_factor", "signal_lag"
    ]
    results_df = results_df[[col for col in column_order if col in results_df.columns]]
    
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    print(results_df.to_string(index=False))
    
    # Calculate aggregate metrics by strategy
    print("\n" + "=" * 80)
    print("AGGREGATE METRICS BY STRATEGY")
    print("=" * 80)
    
    strategy_summary = results_df.groupby("strategy").agg({
        "total_return": "mean",
        "sharpe_ratio": "mean",
        "max_drawdown": "mean",
        "win_rate": "mean",
        "total_trades": "sum",
        "avg_duration_hours": "mean",
        "profit_factor": "mean",
        "signal_lag": "mean"
    }).round(2)
    
    print(strategy_summary.to_string())
    
    # Highlight improvements
    print("\n" + "=" * 80)
    print("IMPROVEMENTS vs TSI/EWO")
    print("=" * 80)
    
    if "tsi_ewo" in strategy_summary.index:
        baseline = strategy_summary.loc["tsi_ewo"]
        
        for strategy_name in strategy_summary.index:
            if strategy_name == "tsi_ewo":
                continue
            
            print(f"\n{strategy_name}:")
            
            for metric in ["total_return", "sharpe_ratio", "win_rate", "profit_factor"]:
                if metric in strategy_summary.columns:
                    improvement = strategy_summary.loc[strategy_name, metric] - baseline[metric]
                    pct_change = (improvement / baseline[metric] * 100) if baseline[metric] != 0 else 0
                    symbol = "📈" if improvement > 0 else "📉"
                    print(f"  {metric}: {symbol} {improvement:+.2f} ({pct_change:+.1f}%)")
            
            # Signal lag (lower is better)
            if "signal_lag" in strategy_summary.columns:
                lag_improvement = baseline["signal_lag"] - strategy_summary.loc[strategy_name, "signal_lag"]
                pct_change = (lag_improvement / baseline["signal_lag"] * 100) if baseline["signal_lag"] != 0 else 0
                symbol = "⚡" if lag_improvement > 0 else "🐌"
                print(f"  signal_lag: {symbol} {lag_improvement:+.2f} bars ({pct_change:+.1f}% faster)")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"{output_dir}/comparison_{timestamp}.csv"
    results_df.to_csv(csv_path, index=False)
    print(f"\n✅ Results saved to: {csv_path}")
    
    # Generate HTML report
    html_path = f"{output_dir}/comparison_{timestamp}.html"
    generate_html_report(results_df, strategy_summary, html_path)
    print(f"✅ HTML report saved to: {html_path}")


def generate_html_report(results_df: pd.DataFrame, strategy_summary: pd.DataFrame, output_path: str):
    """Generate an HTML comparison report."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Indicator Comparison Report</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #2c3e50; 
            border-bottom: 3px solid #3498db; 
            padding-bottom: 10px;
        }}
        h2 {{ 
            color: #34495e; 
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left; 
        }}
        th {{ 
            background-color: #3498db; 
            color: white; 
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        tr:hover {{ background-color: #e8f4f8; }}
        .metric-positive {{ color: #27ae60; font-weight: bold; }}
        .metric-negative {{ color: #e74c3c; font-weight: bold; }}
        .timestamp {{ 
            color: #7f8c8d; 
            font-size: 14px; 
            margin-bottom: 20px;
        }}
        .summary-box {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Indicator Comparison Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary-box">
            <h3>Comparison Overview</h3>
            <p>This report compares the performance of different indicator suites:</p>
            <ul>
                <li><strong>TSI/EWO</strong>: Legacy True Strength Index + Elliott Wave Oscillator</li>
                <li><strong>Fusion (ST+HMA)</strong>: SuperTrend + Hull Moving Average + RSI</li>
                <li><strong>Fusion (ST+QQE)</strong>: SuperTrend + QQE + ADX</li>
            </ul>
        </div>
        
        <h2>Detailed Results by Symbol & Timeframe</h2>
        {results_df.to_html(index=False, classes='table')}
        
        <h2>Aggregate Performance by Strategy</h2>
        {strategy_summary.to_html(classes='table')}
        
        <div class="summary-box">
            <h3>Key Findings</h3>
            <p>The new fusion strategies aim to reduce signal lag and improve win rate through:</p>
            <ul>
                <li>SuperTrend for clear trend identification with less noise</li>
                <li>HMA for faster response to price changes</li>
                <li>QQE for smoother momentum detection</li>
                <li>ADX for trend strength confirmation</li>
                <li>ATR percentile filters for volatility regime awareness</li>
            </ul>
        </div>
    </div>
</body>
</html>
    """
    
    with open(output_path, "w") as f:
        f.write(html_content)


def main():
    parser = argparse.ArgumentParser(description="Run indicator comparison backtest")
    parser.add_argument(
        "--config",
        type=str,
        default="src/config/config.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    run_comparison(args.config)


if __name__ == "__main__":
    main()
