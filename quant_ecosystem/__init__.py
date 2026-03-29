"""
Elite quant ecosystem: four core agents plus evolution, regimes, debate, causal layer,
synthetic stress, microstructure proxies, cross-market, pattern radar, transparency,
allocation, world-context hooks, and the Stock Intel observer (facts only — no debate).

Use ``elite_intelligence.run_full_intelligence`` from the HTTP API or scripts.
"""

from .alpha_discovery import AlphaDiscoveryAgent, GeneticFeatureSearch, LLMHypothesisGenerator
from .allocation import allocate_capital
from .causal_engine import CausalGraph, default_macro_graph, event_impact_narrative, what_if_scenario
from .cross_market import DEFAULT_BUNDLE, fetch_bundle
from .debate import DebateCouncil
from .elite_intelligence import run_full_intelligence
from .evolution import (
    KillSwitchRegistry,
    StrategyDNA,
    StrategyPopulation,
    apply_invented_indicators,
    crossover_strategies,
    mutate_feature_set,
)
from .local_intelligence import LocalResearchEngine
from .market_simulator import Scenario, SimConfig, simulate_path, stress_suite
from .meta_learning import MetaDecision, MetaLearningAgent
from .microstructure import analyze_microstructure
from .model_arena import ModelArenaAgent
from .orchestrator import QuantEcosystemOrchestrator
from .pattern_radar import detect_anomalies, hidden_correlations, precision_matrix_edges
from .personal_trader import UserTradingProfile, adapt_signal, profile_from_dict
from .reality_check import RealityCheckAgent
from .regime import detect_regime, regime_strategy_weights
from .schemas import (
    AlphaHypothesis,
    BacktestConfig,
    EcosystemState,
    ModelCandidate,
    RealityReport,
    StockIntelSnapshot,
    TournamentResult,
)
from .stock_intel_agent import StockIntelAgent
from .transparency import TransparencyLedger, get_ledger
from .world_context import world_context

__all__ = [
    "AlphaDiscoveryAgent",
    "GeneticFeatureSearch",
    "LLMHypothesisGenerator",
    "ModelArenaAgent",
    "RealityCheckAgent",
    "MetaLearningAgent",
    "MetaDecision",
    "QuantEcosystemOrchestrator",
    "run_full_intelligence",
    "allocate_capital",
    "CausalGraph",
    "default_macro_graph",
    "event_impact_narrative",
    "what_if_scenario",
    "DEFAULT_BUNDLE",
    "fetch_bundle",
    "DebateCouncil",
    "KillSwitchRegistry",
    "StrategyDNA",
    "StrategyPopulation",
    "apply_invented_indicators",
    "crossover_strategies",
    "mutate_feature_set",
    "LocalResearchEngine",
    "Scenario",
    "SimConfig",
    "simulate_path",
    "stress_suite",
    "analyze_microstructure",
    "detect_anomalies",
    "hidden_correlations",
    "precision_matrix_edges",
    "UserTradingProfile",
    "adapt_signal",
    "profile_from_dict",
    "detect_regime",
    "regime_strategy_weights",
    "TransparencyLedger",
    "get_ledger",
    "world_context",
    "AlphaHypothesis",
    "BacktestConfig",
    "EcosystemState",
    "ModelCandidate",
    "RealityReport",
    "StockIntelSnapshot",
    "StockIntelAgent",
    "TournamentResult",
]
