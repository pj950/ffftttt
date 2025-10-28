from typing import Dict, List, Tuple
import numpy as np


class FundamentalsScorer:
    """
    Score and filter stocks based on fundamental criteria.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get("enabled", True)
        
        self.liquidity_config = config.get("liquidity", {})
        self.valuation_config = config.get("valuation", {})
        self.size_config = config.get("size", {})
        self.scoring_config = config.get("scoring", {})
        self.missing_action = config.get("missing_data_action", "pass")
    
    def passes_fundamentals_gate(
        self,
        symbol: str,
        metrics: Dict,
        market: str = "HK",
        all_market_caps: List[float] = None
    ) -> Tuple[bool, str, float]:
        """
        Check if a symbol passes fundamental gates.
        
        Args:
            symbol: Stock code
            metrics: Dictionary with pe, pb, market_cap, turnover_20d_avg
            market: Market region (HK, US, CN)
            all_market_caps: List of market caps for percentile calculation
            
        Returns:
            Tuple of (passes: bool, reason: str, score: float)
        """
        if not self.enabled:
            return True, "fundamentals_disabled", 1.0
        
        liquidity_pass, liquidity_reason = self._check_liquidity(metrics)
        if not liquidity_pass:
            return False, liquidity_reason, 0.0
        
        valuation_pass, valuation_reason = self._check_valuation(metrics, market)
        if not valuation_pass:
            return False, valuation_reason, 0.0
        
        size_pass, size_reason, size_pct = self._check_size(
            metrics, all_market_caps
        )
        if not size_pass:
            return False, size_reason, 0.0
        
        score = self._calculate_composite_score(metrics, size_pct)
        
        min_score = self.scoring_config.get("min_score", 0.5)
        if score < min_score:
            return False, f"composite_score_too_low:{score:.2f}<{min_score}", score
        
        return True, "passed", score
    
    def _check_liquidity(self, metrics: Dict) -> Tuple[bool, str]:
        """Check liquidity gate."""
        turnover = metrics.get("turnover_20d_avg")
        
        if turnover is None:
            if self.missing_action == "pass":
                return True, "liquidity_missing_passed"
            else:
                return False, "liquidity_data_missing"
        
        min_turnover = self.liquidity_config.get("min_turnover_amount", 50_000_000)
        
        if turnover < min_turnover:
            return False, f"liquidity_too_low:{turnover:.0f}<{min_turnover}"
        
        return True, "liquidity_ok"
    
    def _check_valuation(self, metrics: Dict, market: str) -> Tuple[bool, str]:
        """Check valuation gates (PE, PB)."""
        pe = metrics.get("pe")
        pb = metrics.get("pb")
        
        overrides = self.config.get("overrides", {}).get(market, {})
        
        pe_min = overrides.get("pe_min", self.valuation_config.get("pe_min", 0))
        pe_max = overrides.get("pe_max", self.valuation_config.get("pe_max", 60))
        pb_max = overrides.get("pb_max", self.valuation_config.get("pb_max", 10))
        
        if pe is not None:
            if pe <= pe_min or pe > pe_max:
                return False, f"pe_out_of_range:{pe:.2f}_not_in_({pe_min},{pe_max}]"
        else:
            if self.missing_action == "block":
                return False, "pe_data_missing"
        
        if pb is not None:
            if pb > pb_max:
                return False, f"pb_too_high:{pb:.2f}>{pb_max}"
        else:
            if self.missing_action == "block":
                return False, "pb_data_missing"
        
        return True, "valuation_ok"
    
    def _check_size(
        self,
        metrics: Dict,
        all_market_caps: List[float]
    ) -> Tuple[bool, str, float]:
        """Check size gate (market cap percentile)."""
        market_cap = metrics.get("market_cap")
        
        if market_cap is None:
            if self.missing_action == "pass":
                return True, "market_cap_missing_passed", 0.5
            else:
                return False, "market_cap_missing", 0.0
        
        if not all_market_caps or len(all_market_caps) == 0:
            return True, "no_comparison_data", 0.5
        
        valid_caps = [cap for cap in all_market_caps if cap is not None]
        if len(valid_caps) == 0:
            return True, "no_valid_comparison_data", 0.5
        
        percentile = np.sum(np.array(valid_caps) <= market_cap) / len(valid_caps)
        
        min_percentile = self.size_config.get("min_percentile", 0.5)
        
        if percentile < min_percentile:
            return False, f"market_cap_percentile_too_low:{percentile:.2f}<{min_percentile}", percentile
        
        return True, "size_ok", percentile
    
    def _calculate_composite_score(
        self,
        metrics: Dict,
        size_pct: float
    ) -> float:
        """Calculate composite score from fundamentals."""
        pe = metrics.get("pe")
        pb = metrics.get("pb")
        
        size_weight = self.scoring_config.get("size_weight", 0.4)
        pe_weight = self.scoring_config.get("pe_weight", 0.3)
        pb_weight = self.scoring_config.get("pb_weight", 0.3)
        
        size_score = size_pct
        
        pe_score = 0.5
        if pe is not None and pe > 0:
            pe_max = self.valuation_config.get("pe_max", 60)
            pe_score = max(0, min(1, 1 - (pe / pe_max)))
        
        pb_score = 0.5
        if pb is not None and pb > 0:
            pb_max = self.valuation_config.get("pb_max", 10)
            pb_score = max(0, min(1, 1 - (pb / pb_max)))
        
        composite = (
            size_weight * size_score +
            pe_weight * pe_score +
            pb_weight * pb_score
        )
        
        return composite
