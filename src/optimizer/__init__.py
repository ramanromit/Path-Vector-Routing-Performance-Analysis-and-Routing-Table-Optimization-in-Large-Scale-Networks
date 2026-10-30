"""Routing Table Optimization module."""

from .aggregation import PrefixAggregationOptimizer
from .default_route import DefaultRouteOptimizer
from .compression import PathCompressionOptimizer
from .engine import OptimizationStrategy, RoutingOptimizerSuite

__all__ = [
    "PrefixAggregationOptimizer",
    "DefaultRouteOptimizer",
    "PathCompressionOptimizer",
    "OptimizationStrategy",
    "RoutingOptimizerSuite",
]
