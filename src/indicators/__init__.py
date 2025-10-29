# Import registry first
from src.indicators.registry import (
    BaseIndicator,
    IndicatorRegistry,
    get_registry,
    register_indicator,
    load_indicators_from_config
)

# Import all indicators to trigger registration
from src.indicators.supertrend import SuperTrend
from src.indicators.hma import HullMovingAverage
from src.indicators.qqe import QQE
from src.indicators.adx import ADX
from src.indicators.atr_percentile import ATRPercentile
from src.indicators.tsi import TSI
from src.indicators.ewo import EWO
from src.indicators.rsi import RSI

# Import legacy indicators
from src.indicators.tsi_ewo import (
    calculate_tsi,
    calculate_ewo,
    calculate_ma,
    detect_crossover,
    detect_crossunder,
    add_all_indicators
)

__all__ = [
    "BaseIndicator",
    "IndicatorRegistry",
    "get_registry",
    "register_indicator",
    "load_indicators_from_config",
    "SuperTrend",
    "HullMovingAverage",
    "QQE",
    "ADX",
    "ATRPercentile",
    "TSI",
    "EWO",
    "RSI",
    "calculate_tsi",
    "calculate_ewo",
    "calculate_ma",
    "detect_crossover",
    "detect_crossunder",
    "add_all_indicators"
]
