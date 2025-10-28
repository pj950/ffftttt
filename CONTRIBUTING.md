# Contributing Guide

Thank you for your interest in contributing to the Futu TSI/EWO Signal Generator!

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Futu OpenD (for testing with real data)

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd futu-tsi-ewo-signals

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Set up environment
bash scripts/bootstrap_env.sh
# Edit .env with your credentials
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_tsi_ewo.py -v

# Run specific test
pytest tests/test_tsi_ewo.py::test_calculate_tsi -v
```

## Project Structure

```
src/
├── config/          # Configuration files
├── data/            # Data fetching and processing
├── indicators/      # Technical indicators
├── strategies/      # Trading strategies
├── backtest/        # Backtesting engine
├── realtime/        # Real-time signal generation
├── notify/          # Notification services
└── fundamentals/    # Fundamentals filtering
    └── providers/   # Data providers
```

## Code Style Guidelines

### General Principles

1. **Follow PEP 8** - Python style guide
2. **Type hints** - Use type hints for function parameters and returns
3. **Docstrings** - Google-style docstrings for all public functions
4. **Minimal comments** - Code should be self-explanatory
5. **Configuration-driven** - Externalize parameters to config files

### Example Function

```python
from typing import List, Dict
import pandas as pd


def fetch_and_process_data(
    symbol: str,
    days_back: int = 30,
    timeframe: str = "60min"
) -> pd.DataFrame:
    """
    Fetch and process intraday data for a symbol.
    
    Args:
        symbol: Stock code (e.g., "HK.00700")
        days_back: Number of days to look back
        timeframe: Target timeframe (60min, 120min, 240min)
        
    Returns:
        DataFrame with processed OHLCV data
        
    Raises:
        ValueError: If symbol format is invalid
        ConnectionError: If Futu OpenD connection fails
    """
    # Implementation
    pass
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `FutuClient`, `TSIEWOStrategy`)
- **Functions**: snake_case (e.g., `calculate_tsi`, `fetch_data`)
- **Variables**: snake_case (e.g., `close_price`, `signal_count`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Private**: Leading underscore (e.g., `_internal_method`)

## Adding New Features

### Adding a New Indicator

1. Add calculation function to `src/indicators/`:

```python
# src/indicators/new_indicator.py
import pandas as pd
import pandas_ta as ta


def calculate_rsi(
    close: pd.Series,
    length: int = 14
) -> pd.Series:
    """
    Calculate Relative Strength Index.
    
    Args:
        close: Close price series
        length: RSI period
        
    Returns:
        Series with RSI values
    """
    rsi = ta.rsi(close, length=length)
    return rsi
```

2. Add tests:

```python
# tests/test_new_indicator.py
def test_calculate_rsi():
    prices = pd.Series([100, 101, 102, 101, 100])
    rsi = calculate_rsi(prices, length=3)
    assert rsi is not None
    assert len(rsi) == len(prices)
```

3. Update documentation in README.md

### Adding a New Strategy

1. Create new strategy class:

```python
# src/strategies/new_strategy.py
from src.strategies.tsi_ewo_strategy import TSIEWOStrategy


class NewStrategy(TSIEWOStrategy):
    """Custom strategy extending TSI/EWO base."""
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # Call parent
        df_copy = super().generate_signals(df)
        
        # Add custom logic
        # ...
        
        return df_copy
```

2. Add configuration support in `config.yaml`
3. Add tests
4. Update documentation

### Adding a New Fundamentals Provider

1. Implement provider interface:

```python
# src/fundamentals/providers/new_provider.py
from src.fundamentals.provider_base import FundamentalsProvider


class NewProvider(FundamentalsProvider):
    """Provider for XYZ data source."""
    
    def fetch_basic_metrics(self, symbol: str) -> Dict:
        """Fetch metrics from XYZ."""
        metrics = {
            "pe": None,
            "pb": None,
            "market_cap": None,
            "turnover_20d_avg": None,
            "volume": None,
        }
        
        # Implementation
        
        return metrics
```

2. Add tests
3. Update documentation

### Adding a New Notification Channel

1. Create notifier class:

```python
# src/notify/telegram.py
class TelegramNotifier:
    """Send notifications via Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
    
    def send_signal(self, signal: Dict) -> bool:
        """Send signal notification."""
        # Implementation
        pass
```

2. Add environment variable to `.env.example`
3. Update configuration
4. Add tests
5. Update documentation

## Testing Guidelines

### Test Structure

```python
def test_feature_name():
    """Test description."""
    # Arrange - Set up test data
    input_data = create_test_data()
    
    # Act - Execute the function
    result = function_under_test(input_data)
    
    # Assert - Verify the result
    assert result is not None
    assert len(result) == expected_length
    assert result.some_property == expected_value
```

### Test Coverage

- Aim for >80% code coverage
- Test normal cases
- Test edge cases (empty input, None values, etc.)
- Test error conditions

### Mock External Dependencies

```python
from unittest.mock import Mock, patch


def test_with_mock():
    """Test using mocked Futu client."""
    with patch('src.data.futu_client.FutuClient') as mock_client:
        mock_client.return_value.fetch_data.return_value = pd.DataFrame()
        
        # Test code using the mocked client
        result = function_that_uses_client()
        
        assert result is not None
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run tests**
   ```bash
   pytest tests/ -v
   ```

4. **Commit with descriptive message**
   ```bash
   git commit -m "feat: Add RSI indicator support"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/my-new-feature
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

Examples:
```
feat: Add Bollinger Bands indicator
fix: Handle missing fundamentals data correctly
docs: Update setup instructions for Windows
test: Add tests for signal deduplication
```

## Code Review Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Type hints are added
- [ ] Docstrings are complete
- [ ] No hardcoded credentials or secrets
- [ ] Configuration changes are documented
- [ ] Backwards compatibility is maintained (or breaking changes are documented)

## Common Development Tasks

### Running Backtest During Development

```python
# Quick test script
from src.data.futu_client import FutuClient
from src.indicators.tsi_ewo import add_all_indicators

with FutuClient() as client:
    df = client.fetch_intraday_data("HK.00700", days_back=5)
    df_1h = client.resample_to_timeframe(df, "60min", "Asia/Hong_Kong")
    df_indicators = add_all_indicators(df_1h)
    print(df_indicators.tail())
```

### Debugging Signal Generation

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run signal runner in once mode
python -m src.realtime.signal_runner --config src/config/config.yaml --once
```

### Testing Configuration Changes

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('src/config/config.yaml'))"

# Test with custom config
python -m src.backtest.run_backtest --config my_test_config.yaml
```

## Documentation

### Updating README

- Keep installation instructions up to date
- Add examples for new features
- Update troubleshooting section

### API Documentation

Use Google-style docstrings:

```python
def function(param1: int, param2: str) -> bool:
    """
    Brief description.
    
    Longer description with more details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is negative
        TypeError: When param2 is not a string
        
    Examples:
        >>> function(5, "test")
        True
    """
```

## Performance Optimization

### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = expensive_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function code
    pass
```

## Troubleshooting Development Issues

### Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall in development mode
pip install -e .
```

### Test Failures

```bash
# Run with verbose output
pytest tests/ -vv

# Run with print statements
pytest tests/ -s

# Run specific test with debugging
pytest tests/test_file.py::test_name --pdb
```

### Futu Connection Issues

```bash
# Check if OpenD is running
telnet 127.0.0.1 11111

# Check OpenD logs
# Location varies by OS and installation
```

## Resources

- [Futu OpenAPI Documentation](https://openapi.futunn.com/)
- [pandas Documentation](https://pandas.pydata.org/docs/)
- [vectorbt Documentation](https://vectorbt.dev/)
- [pandas_ta Documentation](https://github.com/twopirllc/pandas-ta)
- [pytest Documentation](https://docs.pytest.org/)

## Getting Help

- Check existing issues and documentation
- Create an issue with:
  - Clear description of the problem
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (Python version, OS, etc.)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
