import pandas as pd
from typing import Dict, Callable, Any, List
from abc import ABC, abstractmethod


class BaseIndicator(ABC):
    """Base class for all indicators."""
    
    def __init__(self, **params):
        """
        Initialize indicator with parameters.
        
        Args:
            **params: Indicator-specific parameters
        """
        self.params = params
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values and add them to the dataframe.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        pass
    
    @abstractmethod
    def get_signal_columns(self) -> List[str]:
        """
        Get list of column names that this indicator produces.
        
        Returns:
            List of column names
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get indicator name."""
        pass


class IndicatorRegistry:
    """
    Registry for dynamically loading and managing indicators.
    
    Supports:
    - Registration of indicator classes by name
    - Dynamic instantiation with config-driven parameters
    - Batch calculation of multiple indicators
    """
    
    def __init__(self):
        self._indicators: Dict[str, type] = {}
    
    def register(self, name: str, indicator_class: type):
        """
        Register an indicator class.
        
        Args:
            name: Unique identifier for the indicator
            indicator_class: Class that inherits from BaseIndicator
        """
        if not issubclass(indicator_class, BaseIndicator):
            raise ValueError(f"Indicator class must inherit from BaseIndicator")
        
        self._indicators[name] = indicator_class
    
    def create(self, name: str, **params) -> BaseIndicator:
        """
        Create an indicator instance.
        
        Args:
            name: Registered indicator name
            **params: Parameters to pass to indicator constructor
            
        Returns:
            Indicator instance
        """
        if name not in self._indicators:
            raise ValueError(f"Unknown indicator: {name}. Available: {list(self._indicators.keys())}")
        
        return self._indicators[name](**params)
    
    def get_available_indicators(self) -> List[str]:
        """Get list of registered indicator names."""
        return list(self._indicators.keys())
    
    def calculate_all(
        self,
        df: pd.DataFrame,
        indicator_configs: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Calculate multiple indicators on a dataframe.
        
        Args:
            df: DataFrame with OHLCV data
            indicator_configs: List of indicator configurations
                Each config should have: {"name": "indicator_name", "params": {...}}
        
        Returns:
            DataFrame with all indicator columns added
        """
        df_result = df.copy()
        
        for config in indicator_configs:
            name = config.get("name")
            params = config.get("params", {})
            
            if name not in self._indicators:
                print(f"⚠️  Skipping unknown indicator: {name}")
                continue
            
            try:
                indicator = self.create(name, **params)
                df_result = indicator.calculate(df_result)
            except Exception as e:
                print(f"⚠️  Error calculating {name}: {e}")
        
        return df_result


# Global registry instance
_global_registry = IndicatorRegistry()


def register_indicator(name: str):
    """
    Decorator to register an indicator class.
    
    Usage:
        @register_indicator("my_indicator")
        class MyIndicator(BaseIndicator):
            ...
    """
    def decorator(cls):
        _global_registry.register(name, cls)
        return cls
    return decorator


def get_registry() -> IndicatorRegistry:
    """Get the global indicator registry."""
    return _global_registry


def load_indicators_from_config(config: Dict) -> List[Dict[str, Any]]:
    """
    Load indicator configurations from config dict.
    
    Args:
        config: Configuration dictionary with "indicators" key
        
    Returns:
        List of indicator configurations ready for registry
    """
    indicators_config = config.get("indicators", {})
    indicator_list = []
    
    # Handle legacy TSI/EWO format
    if "tsi" in indicators_config:
        indicator_list.append({
            "name": "tsi",
            "params": indicators_config["tsi"]
        })
    
    if "ewo" in indicators_config:
        indicator_list.append({
            "name": "ewo",
            "params": indicators_config["ewo"]
        })
    
    # Handle new format: indicators.list
    if "list" in indicators_config:
        for ind_config in indicators_config["list"]:
            if isinstance(ind_config, dict):
                indicator_list.append(ind_config)
    
    return indicator_list
