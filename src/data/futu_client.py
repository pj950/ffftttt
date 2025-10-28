import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import pytz
from futu import (
    OpenQuoteContext,
    KLType,
    SubType,
    RET_OK,
)


class FutuClient:
    def __init__(self, host: str = None, port: int = None):
        self.host = host or os.getenv("FUTU_OPEND_HOST", "127.0.0.1")
        self.port = int(port or os.getenv("FUTU_OPEND_PORT", "11111"))
        self.quote_ctx = None
        
    def connect(self):
        if self.quote_ctx is None:
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
        return self.quote_ctx
    
    def disconnect(self):
        if self.quote_ctx:
            self.quote_ctx.close()
            self.quote_ctx = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def fetch_historical_kline(
        self,
        symbol: str,
        ktype: str = "K_1M",
        start_date: str = None,
        end_date: str = None,
        max_count: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch historical K-line data from Futu.
        
        Args:
            symbol: Stock code (e.g., "HK.00700")
            ktype: K-line type (K_1M, K_5M, K_15M, K_30M, K_60M, K_DAY, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            max_count: Maximum number of data points
            
        Returns:
            DataFrame with columns: time_key, open, close, high, low, volume, turnover
        """
        if not self.quote_ctx:
            self.connect()
        
        ktype_map = {
            "1min": KLType.K_1M,
            "5min": KLType.K_5M,
            "15min": KLType.K_15M,
            "30min": KLType.K_30M,
            "60min": KLType.K_60M,
            "day": KLType.K_DAY,
        }
        
        futu_ktype = ktype_map.get(ktype, KLType.K_60M)
        
        ret, data, page_req_key = self.quote_ctx.request_history_kline(
            symbol,
            start=start_date,
            end=end_date,
            ktype=futu_ktype,
            max_count=max_count,
            fields=[
                KLType.K_1M,
            ]
        )
        
        if ret != RET_OK:
            raise Exception(f"Failed to fetch kline data for {symbol}: {data}")
        
        if data is None or data.empty:
            return pd.DataFrame()
        
        df = data.copy()
        df.rename(columns={"time_key": "time"}, inplace=True)
        df["time"] = pd.to_datetime(df["time"])
        df.set_index("time", inplace=True)
        
        return df
    
    def fetch_intraday_data(
        self,
        symbol: str,
        days_back: int = 30,
        base_ktype: str = "1min"
    ) -> pd.DataFrame:
        """
        Fetch intraday minute data and return as DataFrame.
        
        Args:
            symbol: Stock code
            days_back: Number of days to look back
            base_ktype: Base K-line type (default: 1min)
            
        Returns:
            DataFrame with OHLCV data
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        return self.fetch_historical_kline(
            symbol=symbol,
            ktype=base_ktype,
            start_date=start_date,
            end_date=end_date,
            max_count=10000
        )
    
    def resample_to_timeframe(
        self,
        df: pd.DataFrame,
        timeframe: str,
        timezone: str = "Asia/Hong_Kong"
    ) -> pd.DataFrame:
        """
        Resample minute data to higher timeframes (1h, 2h, 4h).
        
        Args:
            df: DataFrame with OHLCV data (time index)
            timeframe: Target timeframe (60min, 120min, 240min)
            timezone: Market timezone
            
        Returns:
            Resampled DataFrame
        """
        if df.empty:
            return df
        
        timeframe_map = {
            "60min": "60T",
            "120min": "120T",
            "240min": "240T",
            "1h": "60T",
            "2h": "120T",
            "4h": "240T",
        }
        
        resample_rule = timeframe_map.get(timeframe, "60T")
        
        df_copy = df.copy()
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index)
        
        df_copy.index = df_copy.index.tz_localize(timezone, ambiguous="infer", nonexistent="shift_forward")
        
        resampled = df_copy.resample(resample_rule, label="left", closed="left").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
            "turnover": "sum" if "turnover" in df_copy.columns else "sum",
        })
        
        resampled = resampled.dropna(subset=["open", "close"])
        
        return resampled
    
    def get_market_snapshot(self, symbol: str) -> Dict:
        """
        Get current market snapshot for a symbol.
        
        Args:
            symbol: Stock code
            
        Returns:
            Dictionary with snapshot data
        """
        if not self.quote_ctx:
            self.connect()
        
        ret, data = self.quote_ctx.get_market_snapshot([symbol])
        
        if ret != RET_OK:
            raise Exception(f"Failed to get snapshot for {symbol}: {data}")
        
        if data is None or data.empty:
            return {}
        
        snapshot = data.iloc[0].to_dict()
        return snapshot
    
    def get_basic_info(self, symbols: List[str]) -> pd.DataFrame:
        """
        Get basic stock information.
        
        Args:
            symbols: List of stock codes
            
        Returns:
            DataFrame with basic info
        """
        if not self.quote_ctx:
            self.connect()
        
        ret, data = self.quote_ctx.get_stock_basicinfo(
            market=None,
            stock_type=None,
            code_list=symbols
        )
        
        if ret != RET_OK:
            raise Exception(f"Failed to get basic info: {data}")
        
        return data
