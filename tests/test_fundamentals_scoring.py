import pytest
from src.fundamentals.scoring import FundamentalsScorer


def get_test_config(overrides=None):
    """Get a standard test config with optional overrides."""
    config = {
        "enabled": True,
        "thresholds": {
            "liquidity": {
                "min": 50_000_000
            },
            "global": {
                "pe_min": 0,
                "pe_max": 60,
                "pb_max": 10,
                "cap_percentile_min": 0.5
            },
            "overrides": {
                "US": {
                    "pe_max": 50,
                    "pb_max": 12,
                    "cap_percentile_min": 0.6
                },
                "CN": {
                    "pe_max": 80,
                    "pb_max": 12,
                    "cap_percentile_min": 0.5
                }
            }
        },
        "scoring": {
            "weights": {
                "size": 0.4,
                "pe": 0.3,
                "pb": 0.3
            },
            "min_score": 0.5
        },
        "gate_behavior_on_missing": "pass"
    }
    
    if overrides:
        config.update(overrides)
    
    return config


def test_liquidity_gate_pass():
    """Test liquidity gate with sufficient turnover."""
    config = get_test_config()
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
    config = get_test_config()
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
    config = get_test_config()
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
    config = get_test_config()
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
    config = get_test_config()
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
    config = get_test_config()
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
    config = get_test_config({
        "gate_behavior_on_missing": "block"
    })
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
    config = get_test_config()
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": 55,
        "pb": 3,
        "market_cap": 100_000_000_000,
        "turnover_20d_avg": 100_000_000
    }
    
    # Should pass in CN (pe_max=80)
    passes_cn, _, _ = scorer.passes_fundamentals_gate(
        "CN.600000",
        metrics,
        market="CN",
        all_market_caps=[100_000_000_000]
    )
    
    # Should fail in US (pe_max=50)
    passes_us, _, _ = scorer.passes_fundamentals_gate(
        "US.AAPL",
        metrics,
        market="US",
        all_market_caps=[100_000_000_000]
    )
    
    # Should pass in HK (pe_max=60 from global)
    passes_hk, _, _ = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK",
        all_market_caps=[100_000_000_000]
    )
    
    assert passes_cn == True
    assert passes_us == False
    assert passes_hk == True


def test_market_specific_cap_percentile():
    """Test market-specific cap percentile thresholds."""
    config = get_test_config()
    scorer = FundamentalsScorer(config)
    
    # Test with a market cap at 55th percentile
    metrics = {
        "pe": 20,
        "pb": 3,
        "market_cap": 110_000_000_000,  # 55th percentile
        "turnover_20d_avg": 100_000_000
    }
    
    all_caps = [i * 10_000_000_000 for i in range(1, 21)]  # 10B to 200B
    
    # Should pass in HK (min=0.5)
    passes_hk, _, _ = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK",
        all_market_caps=all_caps
    )
    
    # Should fail in US (min=0.6)
    passes_us, _, _ = scorer.passes_fundamentals_gate(
        "US.AAPL",
        metrics,
        market="US",
        all_market_caps=all_caps
    )
    
    assert passes_hk == True
    assert passes_us == False


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


def test_composite_score_calculation():
    """Test composite score calculation with new formula."""
    config = get_test_config()
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": 30,  # PE_Score = (60-30)/60 = 0.5
        "pb": 5,   # PB_Score = (10-5)/10 = 0.5
        "market_cap": 100_000_000_000,  # 66th percentile (2 out of 3)
        "turnover_20d_avg": 100_000_000
    }
    
    all_caps = [50_000_000_000, 100_000_000_000, 150_000_000_000]
    
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK",
        all_market_caps=all_caps
    )
    
    # Expected: 0.4*(2/3) + 0.3*0.5 + 0.3*0.5 = 0.4*0.667 + 0.15 + 0.15 = 0.567
    assert passes == True
    assert score > 0.5


def test_composite_score_too_low():
    """Test failing composite score threshold."""
    config = get_test_config()
    scorer = FundamentalsScorer(config)
    
    metrics = {
        "pe": 58,  # PE_Score = (60-58)/60 = 0.033
        "pb": 9,   # PB_Score = (10-9)/10 = 0.1
        "market_cap": 60_000_000_000,  # Low percentile
        "turnover_20d_avg": 100_000_000
    }
    
    all_caps = [50_000_000_000, 60_000_000_000, 150_000_000_000]
    
    passes, reason, score = scorer.passes_fundamentals_gate(
        "HK.00700",
        metrics,
        market="HK",
        all_market_caps=all_caps
    )
    
    # Score should be low and fail
    assert passes == False
    assert "score" in reason.lower()
    assert score < 0.5


def test_backward_compatibility_old_config():
    """Test that old config format still works."""
    old_config = {
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
    
    scorer = FundamentalsScorer(old_config)
    
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
    assert score > 0
