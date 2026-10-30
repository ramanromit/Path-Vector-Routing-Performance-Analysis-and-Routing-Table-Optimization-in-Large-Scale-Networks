"""Unit tests for Routing Table Optimizer Suite and Reachability Verification."""

import pytest
from src.topology.generator import NetworkTopology, generate_scale_free_topology
from src.topology.prefix_allocator import PrefixAllocator
from src.routing.engine import PathVectorEngine
from src.optimizer.engine import OptimizationStrategy, RoutingOptimizerSuite
from src.optimizer.aggregation import PrefixAggregationOptimizer
from src.routing.router import Route, Router


def test_prefix_aggregation_logic():
    """Tests that contiguous /24 prefixes with same next-hop and path are summarized into /23."""
    router = Router(as_id=1)
    router.add_originated_prefix("10.0.0.0/24")

    # Add routes to contiguous prefixes 10.2.0.0/24 and 10.2.1.0/24 via neighbor 2
    router.loc_rib["10.2.0.0/24"] = Route(
        prefix="10.2.0.0/24",
        as_path=(2,),
        next_hop=2,
    )
    router.loc_rib["10.2.1.0/24"] = Route(
        prefix="10.2.1.0/24",
        as_path=(2,),
        next_hop=2,
    )

    assert router.table_size == 3

    opt_table = PrefixAggregationOptimizer.aggregate_router_table(router)

    # 10.2.0.0/24 and 10.2.1.0/24 should merge into 10.2.0.0/23
    assert "10.2.0.0/23" in opt_table
    assert "10.2.0.0/24" not in opt_table
    assert "10.2.1.0/24" not in opt_table
    assert len(opt_table) == 2  # 10.0.0.0/24 + 10.2.0.0/23


def test_scale_free_network_optimization_and_reachability():
    """Runs full network optimization on 15-node scale-free topology.

    Verifies:
    1. Table size is reduced (table_size_reduction_pct > 0).
    2. Memory footprint is reduced (memory_savings_pct > 0).
    3. Reachability is 100% preserved (reachability == 100.0).
    """
    topo = generate_scale_free_topology(num_nodes=15, m_attachments=2, seed=42)
    allocator = PrefixAllocator()
    allocator.allocate(topo, hierarchical=True)

    engine = PathVectorEngine(topo)
    init_stats = engine.run_initial_convergence()
    assert init_stats.converged is True
    assert init_stats.reachability_ratio == 1.0

    optimizer = RoutingOptimizerSuite(engine)

    # Test Prefix Aggregation Strategy
    rec_agg = optimizer.apply_optimization(OptimizationStrategy.PREFIX_AGGREGATION)
    assert rec_agg.optimized_table_size < rec_agg.baseline_table_size
    assert rec_agg.optimized_reachability_pct == 100.0

    # Test Hybrid Strategy
    rec_hybrid = optimizer.apply_optimization(OptimizationStrategy.HYBRID)
    assert rec_hybrid.optimized_table_size < rec_agg.optimized_table_size
    assert rec_hybrid.optimized_memory_mb < rec_hybrid.baseline_memory_mb
    assert rec_hybrid.optimized_reachability_pct == 100.0
