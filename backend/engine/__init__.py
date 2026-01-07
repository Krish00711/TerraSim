"""
Agricultural Simulation Engine

This package contains the core simulation components for agricultural planning.

Modules:
    simulator: Monte Carlo simulation engine
    penalties: Environmental mismatch and terrain penalty calculations
    scoring: Success rate and risk level computation
    explainability: Natural language explanation generation
"""

from .simulator import MonteCarloSimulator
from .penalties import PenaltyEngine
from .scoring import compute_metrics, calculate_risk_level
from .explainability import generate_explanation

__version__ = "1.0.0"
__author__ = "Agricultural Simulation Team"

__all__ = [
    'MonteCarloSimulator',
    'PenaltyEngine',
    'compute_metrics',
    'calculate_risk_level',
    'generate_explanation'
]