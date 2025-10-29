import os
import sys
import argparse
import yaml
import json
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import pytz
from dotenv import load_dotenv

from src.data.futu_client import FutuClient
from src.indicators.tsi_ewo import add_all_indicators
from src.indicators import get_registry, load_indicators_from_config
from src.strategies.tsi_ewo_strategy import TSIEWOStrategy
from src.strategies.fusion import FusionStrategy
from src.notify.serverchan import ServerChanNotifier
from src.fundamentals.providers.futu_snapshot import FutuSnapshotProvider
from src.fundamentals.scoring import FundamentalsScorer


class SignalCooldownTracker:
    """Track signal cooldowns to prevent duplicates."""
    
    def __init__(self, cooldown_hours: int = 4):
        self.cooldown_hours = cooldown_hours
        self.last_signals: Dict[Tuple[str, str, str], datetime] = {}
    
    def should_emit(self, symbol: str, timeframe: str, side: str) -> bool:
        """Check if enough time has passed since last signal."""
        key = (symbol, timeframe, side)
        
        if key not in self.last_signals:
            return True
        
        last_time = self.last_signals[key]
        elapsed = datetime.now() - last_time
        
        return elapsed > timedelta(hours=self.cooldown_hours)
    
    def record_signal(self, symbol: str, timeframe: str, side: str):
        """Record that a signal was emitted."""
        key = (symbol, timeframe, side)
        self.last_signals[key] = datetime.now()


class SignalRunner:
    """Real-time signal generation and notification."""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.futu_client = None
        self.strategy = None
        self.notifier = None
        self.cooldown_tracker = None
        self.fundamentals_scorer = None
        self.fundamentals_provider = None
        self.log_file = None
        
        self._init_components()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    
    def _init_components(self):
        """Initialize all components."""
        self.futu_client = FutuClient()
        self.futu_client.connect()
        
        strategy_config = self.config.get("strategy", {})
        strategy_type = strategy_config.get("type", "tsi_ewo")
        
        # Initialize strategy based on type
        if strategy_type == "fusion":
            self.strategy = FusionStrategy(strategy_config)
        else:
            self.strategy = TSIEWOStrategy(strategy_config)
        
        notification_config = self.config.get("notifications", {}).get("serverchan", {})
        if notification_config.get("enabled", True):
            self.notifier = ServerChanNotifier()
        
        realtime_config = self.config.get("realtime", {})
        cooldown_config = realtime_config.get("cooldown", {})
        
        if cooldown_config.get("enabled", True):
            cooldown_hours = cooldown_config.get("period_hours", 4)
            self.cooldown_tracker = SignalCooldownTracker(cooldown_hours)
        
        fundamentals_config = self.config.get("fundamentals", {})
        if fundamentals_config.get("enabled", True):
            self.fundamentals_scorer = FundamentalsScorer(fundamentals_config)
            self.fundamentals_provider = FutuSnapshotProvider(self.futu_client)
        
        if realtime_config.get("log_to_file", True):
            log_file_name = realtime_config.get("log_file", "signals.log")
            self.log_file = open(log_file_name, "a")
    
    def __del__(self):
        """Cleanup resources."""
        if self.futu_client:
            self.futu_client.disconnect()
        if self.log_file:
            self.log_file.close()
    
    def is_market_open(self) -> bool:
        """Check if market is currently open."""
        market_hours = self.config.get("realtime", {}).get("market_hours", {})
        timezone_str = self.config.get("market", {}).get("timezone", "Asia/Hong_Kong")
        
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        
        start_time = market_hours.get("start", "09:30")
        end_time = market_hours.get("end", "16:00")
        
        start_hour, start_min = map(int, start_time.split(":"))
        end_hour, end_min = map(int, end_time.split(":"))
        
        market_start = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        market_end = now.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
        
        if now < market_start or now > market_end:
            return False
        
        exclude_ranges = market_hours.get("exclude_ranges", [])
        for exclude in exclude_ranges:
            exc_start = exclude.get("start", "12:00")
            exc_end = exclude.get("end", "13:00")
            
            exc_start_hour, exc_start_min = map(int, exc_start.split(":"))
            exc_end_hour, exc_end_min = map(int, exc_end.split(":"))
            
            exc_start_time = now.replace(hour=exc_start_hour, minute=exc_start_min, second=0, microsecond=0)
            exc_end_time = now.replace(hour=exc_end_hour, minute=exc_end_min, second=0, microsecond=0)
            
            if exc_start_time <= now <= exc_end_time:
                return False
        
        if now.weekday() >= 5:
            return False
        
        return True
    
    def check_fundamentals(self, symbols: List[str]) -> Tuple[Set[str], Dict[str, Dict]]:
        """
        Check fundamentals for all symbols.
        
        Returns:
            Tuple of (passed_symbols, all_metrics)
        """
        if not self.fundamentals_scorer or not self.fundamentals_provider:
            return set(symbols), {}
        
        passed_symbols = set()
        all_metrics = {}
        all_market_caps = []
        
        print("📊 Checking fundamentals...")
        
        for symbol in symbols:
            try:
                metrics = self.fundamentals_provider.fetch_basic_metrics(symbol)
                all_metrics[symbol] = metrics
                
                if metrics.get("market_cap") is not None:
                    all_market_caps.append(metrics["market_cap"])
            except Exception as e:
                print(f"  ⚠️  Failed to fetch fundamentals for {symbol}: {e}")
        
        market = self.config.get("market", {}).get("region", "HK")
        
        for symbol in symbols:
            metrics = all_metrics.get(symbol, {})
            
            passes, reason, score = self.fundamentals_scorer.passes_fundamentals_gate(
                symbol=symbol,
                metrics=metrics,
                market=market,
                all_market_caps=all_market_caps
            )
            
            if passes:
                passed_symbols.add(symbol)
                print(f"  ✅ {symbol}: {reason} (score={score:.2f})")
            else:
                print(f"  ❌ {symbol}: {reason}")
        
        return passed_symbols, all_metrics
    
    def generate_signals_for_symbol(
        self,
        symbol: str,
        timeframe: str
    ) -> List[Dict]:
        """Generate signals for a single symbol and timeframe."""
        lookback_days = self.config.get("lookback_days", 30)
        
        df = self.futu_client.fetch_intraday_data(
            symbol=symbol,
            days_back=lookback_days,
            base_ktype="1min"
        )
        
        if df.empty:
            return []
        
        df_resampled = self.futu_client.resample_to_timeframe(
            df,
            timeframe=timeframe,
            timezone=self.config["market"]["timezone"]
        )
        
        if df_resampled.empty or len(df_resampled) < 50:
            return []
        
        strategy_type = self.config.get("strategy", {}).get("type", "tsi_ewo")
        
        # Calculate indicators based on strategy type
        if strategy_type == "fusion":
            # Use registry-based indicator calculation
            indicator_configs = load_indicators_from_config(self.config)
            registry = get_registry()
            df_with_indicators = registry.calculate_all(df_resampled, indicator_configs)
        else:
            # Legacy TSI/EWO indicators
            indicator_config = self.config.get("indicators", {})
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
        
        df_with_signals = self.strategy.generate_signals(df_with_indicators)
        
        signals = self.strategy.extract_latest_signals(
            df_with_signals,
            symbol=symbol,
            timeframe=timeframe
        )
        
        return signals
    
    def emit_signal(self, signal: Dict):
        """Emit a signal (log and notify)."""
        symbol = signal["symbol"]
        timeframe = signal["timeframe"]
        side = signal["side"]
        
        if self.cooldown_tracker:
            if not self.cooldown_tracker.should_emit(symbol, timeframe, side):
                return
        
        timestamp_str = signal["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        signal_copy = signal.copy()
        signal_copy["timestamp"] = timestamp_str
        
        signal_json = json.dumps(signal_copy)
        print(f"🔔 SIGNAL: {signal_json}")
        
        if self.log_file:
            self.log_file.write(signal_json + "\n")
            self.log_file.flush()
        
        if self.notifier:
            notification_config = self.config.get("notifications", {}).get("serverchan", {})
            success = self.notifier.send_signal(signal_copy, notification_config)
            if success:
                print(f"  ✅ Notification sent via Server酱")
            else:
                print(f"  ⚠️  Notification failed (check SERVERCHAN_KEY)")
        
        if self.cooldown_tracker:
            self.cooldown_tracker.record_signal(symbol, timeframe, side)
    
    def run_once(self):
        """Run one iteration of signal generation."""
        if not self.is_market_open():
            return
        
        print("\n" + "=" * 60)
        print(f"Signal Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        symbols = self.config.get("watchlist", [])
        timeframes = self.config.get("timeframes", ["60min"])
        
        passed_symbols, _ = self.check_fundamentals(symbols)
        
        if not passed_symbols:
            print("⚠️  No symbols passed fundamentals filter")
            return
        
        print(f"\n🔍 Checking signals for {len(passed_symbols)} symbols × {len(timeframes)} timeframes...")
        
        all_signals = []
        
        for symbol in passed_symbols:
            for timeframe in timeframes:
                try:
                    signals = self.generate_signals_for_symbol(symbol, timeframe)
                    all_signals.extend(signals)
                except Exception as e:
                    print(f"  ⚠️  Error processing {symbol} [{timeframe}]: {e}")
        
        if all_signals:
            print(f"\n✅ Generated {len(all_signals)} signal(s)")
            for signal in all_signals:
                self.emit_signal(signal)
        else:
            print("\n✅ No new signals")
    
    def run_loop(self):
        """Run continuous signal generation loop."""
        check_interval = self.config.get("realtime", {}).get("check_interval", 60)
        
        print("=" * 60)
        print("TSI/EWO Real-time Signal Runner")
        print("=" * 60)
        print(f"Check interval: {check_interval}s")
        print(f"Market: {self.config.get('market', {}).get('region', 'HK')}")
        print(f"Timezone: {self.config.get('market', {}).get('timezone', 'Asia/Hong_Kong')}")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            while True:
                try:
                    self.run_once()
                except Exception as e:
                    print(f"⚠️  Error in run_once: {e}")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Stopping signal runner...")
            if self.futu_client:
                self.futu_client.disconnect()


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Run TSI/EWO real-time signal generator")
    parser.add_argument(
        "--config",
        type=str,
        default="src/config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for testing)"
    )
    
    args = parser.parse_args()
    
    runner = SignalRunner(args.config)
    
    if args.once:
        runner.run_once()
    else:
        runner.run_loop()


if __name__ == "__main__":
    main()
