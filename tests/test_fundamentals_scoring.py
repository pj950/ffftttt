import pytest
from src.fundamentals.scoring import FundamentalsScorer


def test_liquidity_gate_pass():
    """Test liquidity gate with sufficient turnover."""
    config = {
        "enabled": True,
        "liquidity": {
            "min_turnover_amount": 50_000_000
        },
        "valuation": {
            "pe_min": 0,
            "pe_max": 60,
            "pb_max": 10
        },
        "size": {
            "min_percentile": 0.5
        },
        "scoring": {
            "size_weight": 0.4,
            "pe_weight": 0.3,
            "pb_weight": 0.3,
            "min_score": 0.5
        },
        "missing_data_action": "pass"
    }
    
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": 20,
        "pb": 3,
        "market_cap": 100_000_000_000,
        "turnover_20d_avg": 100_000_000
    }
    
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK",
        all_market_caps=[50_000_000_000, 100_000_000_000, 150_000_000_000]
    )
    
    assert passes == True
    assert "passed" in reason.lower()
    assert score > 0


def test_liquidity_gate_fail():
    """Test liquidity gate with insufficient turnover."""
    config = {
        "enabled": True,
        "liquidity": {
            "min_turnover_amount": 50_000_000
        },
        "valuation": {
            "pe_min": 0,
            "pe_max": 60,
            "pb_max": 10
        },
        "size": {
            "min_percentile": 0.5
        },
        "scoring": {
            "size_weight": 0.4,
            "pe_weight": 0.3,
            "pb_weight": 0.3,
            "min_score": 0.5
        },
        "missing_data_action": "pass"
    }
    
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": 20,
        "pb": 3,
        "market_cap": 100_000_000_000,
        "turnover_20d_avg": 10_000_000
    }
    
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK"
    )
    
    assert passes == False
    assert "liquidity" in reason.lower()


def test_valuation_gate_pe_out_of_range():
    """Test valuation gate with PE out of range."""
    config = {
        "enabled": True,
        "liquidity": {
            "min_turnover_amount": 50_000_000
        },
        "valuation": {
            "pe_min": 0,
            "pe_max": 60,
            "pb_max": 10
        },
        "size": {
            "min_percentile": 0.5
        },
        "scoring": {
            "size_weight": 0.4,
            "pe_weight": 0.3,
            "pb_weight": 0.3,
            "min_score": 0.5
        },
        "missing_data_action": "pass"
    }
    
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": 80,
        "pb": 3,
        "market_cap": 100_000_000_000,
        "turnover_20d_avg": 100_000_000
    }
    
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK"
    )
    
    assert passes == False
    assert "pe" in reason.lower()


def test_valuation_gate_pb_too_high():
    """Test valuation gate with PB too high."""
    config = {
        "enabled": True,
        "liquidity": {
            "min_turnover_amount": 50_000_000
        },
        "valuation": {
            "pe_min": 0,
            "pe_max": 60,
            "pb_max": 10
        },
        "size": {
            "min_percentile": 0.5
        },
        "scoring": {
            "size_weight": 0.4,
            "pe_weight": 0.3,
            "pb_weight": 0.3,
            "min_score": 0.5
        },
        "missing_data_action": "pass"
    }
    
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": 20,
        "pb": 15,
        "market_cap": 100_000_000_000,
        "turnover_20d_avg": 100_000_000
    }
    
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK"
    )
    
    assert passes == False
    assert "pb" in reason.lower()


def test_size_gate_market_cap_too_small():
    """Test size gate with market cap below percentile."""
    config = {
        "enabled": True,
        "liquidity": {
            "min_turnover_amount": 50_000_000
        },
        "valuation": {
            "pe_min": 0,
            "pe_max": 60,
            "pb_max": 10
        },
        "size": {
            "min_percentile": 0.5
        },
        "scoring": {
            "size_weight": 0.4,
            "pe_weight": 0.3,
            "pb_weight": 0.3,
            "min_score": 0.5
        },
        "missing_data_action": "pass"
    }
    
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": 20,
        "pb": 3,
        "market_cap": 10_000_000_000,
        "turnover_20d_avg": 100_000_000
    }
    
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK",
        all_market_caps=[100_000_000_000, 200_000_000_000, 300_000_000_000]
    )
    
    assert passes == False
    assert "percentile" in reason.lower()


def test_missing_data_pass_mode():
    """Test missing data with pass mode."""
    config = {
        "enabled": True,
        "liquidity": {
            "min_turnover_amount": 50_000_000
        },
        "valuation": {
            "pe_min": 0,
            "pe_max": 60,
            "pb_max": 10
        },
        "size": {
            "min_percentile": 0.5
        },
        "scoring": {
            "size_weight": 0.4,
            "pe_weight": 0.3,
            "pb_weight": 0.3,
            "min_score": 0.5
        },
        "missing_data_action": "pass"
    }
    
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": None,
        "pb": None,
        "market_cap": 100_000_000_000,
        "turnover_20d_avg": 100_000_000
    }
    
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK",
        all_market_caps=[50_000_000_000, 100_000_000_000, 150_000_000_000]
    )
    
    assert passes == True


def test_missing_data_block_mode():
    """Test missing data with block mode."""
    config = {
        "enabled": True,
        "liquidity": {
            "min_turnover_amount": 50_000_000
        },
        "valuation": {
            "pe_min": 0,
            "pe_max": 60,
            "pb_max": 10
        },
        "size": {
            "min_percentile": 0.5
        },
        "scoring": {
            "size_weight": 0.4,
            "pe_weight": 0.3,
            "pb_weight": 0.3,
            "min_score": 0.5
        },
        "missing_data_action": "block"
    }
    
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": None,
        "pb": 3,
        "market_cap": 100_000_000_000,
        "turnover_20d_avg": 100_000_000
    }
    
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK"
    )
    
    assert passes == False
    assert "missing" in reason.lower()


def test_market_specific_overrides():
    """Test market-specific valuation overrides."""
    config = {
        "enabled": True,
        "liquidity": {
            "min_turnover_amount": 50_000_000
        },
        "valuation": {
            "pe_min": 0,
            "pe_max": 60,
            "pb_max": 10
        },
        "overrides": {
            "US": {
                "pe_max": 80
            },
            "CN": {
                "pe_max": 50
            }
        },
        "size": {
            "min_percentile": 0.5
        },
        "scoring": {
            "size_weight": 0.4,
            "pe_weight": 0.3,
            "pb_weight": 0.3,
            "min_score": 0.5
        },
        "missing_data_action": "pass"
    }
    
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": 70,
        "pb": 3,
        "market_cap": 100_000_000_000,
        "turnover_20d_avg": 100_000_000
    }
    
    passes_us, _, _ = scorer.passes_fundamentals_gate(
        "US.AAPL",
        metrics,
        market="US",
        all_market_caps=[100_000_000_000]
    )
    
    passes_cn, _, _ = scorer.passes_fundamentals_gate(
        "CN.600000",
        metrics,
        market="CN",
        all_market_caps=[100_000_000_000]
    )
    
    assert passes_us == True
    assert passes_cn == False


def test_fundamentals_disabled():
    """Test with fundamentals disabled."""
    config = {
        "enabled": False,
    }
    
    scorer = FundamentalsScorer(config)
    
    metrics = {}
    
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK"
    )
    
    assert passes == True
    assert "disabled" in reason.lower()
    assert score == 1.0
