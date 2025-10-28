# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-10-28

### Added
- Initial MVP release
- Futu OpenD client integration for fetching intraday data
- Technical indicators: TSI (True Strength Index) and EWO (Elliott Wave Oscillator)
- TSI/EWO crossover strategy with configurable rules
- Fundamentals whitelist with liquidity, valuation, and size gates
- Backtesting pipeline using vectorbt with performance metrics (CAGR, Sharpe, Win Rate, Max DD, Calmar)
- Real-time signal generation with market hours awareness
- Signal cooldown and deduplication to prevent alert fatigue
- Server酱 (ServerChan) integration for WeChat notifications
- YAML-based configuration system
- Support for multiple timeframes (1h, 2h, 4h)
- Support for multiple markets (HK, US, CN) with market-specific overrides
- Comprehensive test suite with pytest
- Command-line interfaces for backtesting and real-time signal generation
- Documentation: README, QUICKSTART, and inline docstrings

### Features in Detail

#### Data Layer
- Fetch historical and intraday K-line data from Futu
- Resample minute data to higher timeframes
- Market snapshot and basic stock info retrieval

#### Indicators
- TSI: Double-smoothed momentum indicator with configurable periods
- EWO: Elliott Wave Oscillator (EMA difference)
- Moving Average (MA) for trend filtering
- Crossover/crossunder detection utilities

#### Strategy
- LONG entry: TSI crosses above 0 AND EWO > 0
- LONG exit: TSI crosses below 0 OR EWO < 0
- Confidence scoring based on indicator strength
- Optional filters: minimum volume, MA trend confirmation

#### Fundamentals
- Liquidity gate: 20-day average daily turnover threshold
- Valuation gates: PE ratio and PB ratio limits
- Size gate: Market cap percentile filtering
- Composite scoring with configurable weights
- Market-specific overrides (US, CN, HK)
- Configurable behavior for missing data (pass or block)

#### Backtesting
- vectorbt-based portfolio simulation
- Configurable fees, slippage, and position sizing
- Metrics: Total Return, CAGR, Sharpe Ratio, Max Drawdown, Win Rate, Calmar Ratio
- CSV and HTML report generation

#### Real-time Signals
- Market hours awareness with lunch break exclusions
- Automatic symbol filtering based on fundamentals
- Signal cooldown to prevent duplicates
- JSON output to stdout and log file
- WeChat notifications via Server酱

### Configuration
- Watchlist management
- Timeframe selection
- Indicator parameter tuning
- Strategy filter configuration
- Fundamentals threshold settings
- Backtest parameters
- Real-time runner settings
- Notification templates

### Documentation
- Comprehensive README with setup instructions
- Quick Start Guide for 5-minute setup
- Inline code documentation
- Test coverage for core functionality
- Troubleshooting guide
- Usage examples

### Dependencies
- vectorbt >=0.25.0
- pandas >=2.0.0
- numpy >=1.24.0
- pandas-ta >=0.3.14b
- futu-api >=6.8.0
- pyyaml >=6.0
- requests >=2.31.0
- python-dotenv >=1.0.0
- pytest >=7.4.0

## [Unreleased]

### Planned Features
- Support for SHORT signals
- Additional technical indicators (RSI, MACD, Bollinger Bands)
- Multi-strategy portfolio mode
- Performance tracking and analytics dashboard
- Database storage for signals and results
- Telegram notification support
- Email notification support
- Advanced backtesting features (walk-forward optimization)
- Live paper trading mode
- Risk management features (position sizing, stop loss, take profit)
- Multi-threaded data fetching for faster processing
- WebSocket integration for real-time data streaming
