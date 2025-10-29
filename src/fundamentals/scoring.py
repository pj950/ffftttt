from typing import Dict, List, Tuple
import numpy as np


class FundamentalsScorer:
    """
    Score and filter stocks based on fundamental criteria.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get("enabled", True)
        
        # Support both old and new config formats
        thresholds = config.get("thresholds", {})
        if thresholds:
            # New format
            self.liquidity_config = thresholds.get("liquidity", {})
            self.global_config = thresholds.get("global", {})
            self.overrides_config = thresholds.get("overrides", {})
            self.scoring_config = config.get("scoring", {})
            self.missing_action = config.get("gate_behavior_on_missing", "pass")
        else:
            # Old format (backward compatibility)
            self.liquidity_config = config.get("liquidity", {})
            self.global_config = config.get("valuation", {})
            self.overrides_config = config.get("overrides", {})
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
            metrics, all_market_caps, market
        )
        if not size_pass:
            return False, size_reason, 0.0
        
        score = self._calculate_composite_score(metrics, size_pct, market)
        
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
        
        # Support both old and new config formats
        min_turnover = self.liquidity_config.get("min", self.liquidity_config.get("min_turnover_amount", 50_000_000))
        
        if turnover < min_turnover:
            return False, f"liquidity_too_low:{turnover:.0f}<{min_turnover}"
        
        return True, "liquidity_ok"
    
    def _check_valuation(self, metrics: Dict, market: str) -> Tuple[bool, str]:
        """Check valuation gates (PE, PB)."""
        pe = metrics.get("pe")
        pb = metrics.get("pb")
        
        overrides = self.overrides_config.get(market, {})
        
        pe_min = overrides.get("pe_min", self.global_config.get("pe_min", 0))
        pe_max = overrides.get("pe_max", self.global_config.get("pe_max", 60))
        pb_max = overrides.get("pb_max", self.global_config.get("pb_max", 10))
        
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
        all_market_caps: List[float],
        market: str = "HK"
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
        
        # Support market-specific cap_percentile_min from overrides
        overrides = self.overrides_config.get(market, {})
        min_percentile = overrides.get("cap_percentile_min", self.global_config.get("cap_percentile_min", 0.5))
        # Backward compatibility
        if "size" in self.config:
            min_percentile = self.config["size"].get("min_percentile", min_percentile)
        
        if percentile < min_percentile:
            return False, f"market_cap_percentile_too_low:{percentile:.2f}<{min_percentile}", percentile
        
        return True, "size_ok", percentile
    
    def _calculate_composite_score(
        self,
        metrics: Dict,
        size_pct: float,
        market: str = "HK"
    ) -> float:
        """
        Calculate composite score from fundamentals.
        
        Scoring formula:
        - PE_Score = clamp((pe_max - PE) / pe_max, 0, 1)
        - PB_Score = clamp((pb_max - PB) / pb_max, 0, 1)
        - Size_Score = cap_percentile
        - Composite = 0.4*Size + 0.3*PE + 0.3*PB
        """
        pe = metrics.get("pe")
        pb = metrics.get("pb")
        
        # Support both old and new config formats
        weights = self.scoring_config.get("weights", {})
        if weights:
            # New format
            size_weight = weights.get("size", 0.4)
            pe_weight = weights.get("pe", 0.3)
            pb_weight = weights.get("pb", 0.3)
        else:
            # Old format (backward compatibility)
            size_weight = self.scoring_config.get("size_weight", 0.4)
            pe_weight = self.scoring_config.get("pe_weight", 0.3)
            pb_weight = self.scoring_config.get("pb_weight", 0.3)
        
        size_score = size_pct
        
        # Get market-specific thresholds
        overrides = self.overrides_config.get(market, {})
        pe_max = overrides.get("pe_max", self.global_config.get("pe_max", 60))
        pb_max = overrides.get("pb_max", self.global_config.get("pb_max", 10))
        
        # PE Score: clamp((pe_max - PE) / pe_max, 0, 1)
        pe_score = 0.5  # Default if PE is missing
        if pe is not None and pe > 0:
            pe_score = max(0, min(1, (pe_max - pe) / pe_max))
        
        # PB Score: clamp((pb_max - PB) / pb_max, 0, 1)
        pb_score = 0.5  # Default if PB is missing
        if pb is not None and pb > 0:
            pb_score = max(0, min(1, (pb_max - pb) / pb_max))
        
        composite = (
            size_weight * size_score +
            pe_weight * pe_score +
            pb_weight * pb_score
        )
        
        return composite
