"""Unit tests for Network Events Simulator and Metrics Collector."""

import pytest
from src.topology.generator import NetworkTopology, generate_scale_free_topology
from src.topology.prefix_allocator import PrefixAllocator
from src.routing.engine import PathVectorEngine
from src.events.simulator import NetworkEventSimulator
from src.metrics.collector import MetricsCollector, NetworkScaleMeasurement


def test_link_failure_and_reconvergence():
    r"""Tests link failure in a redundant topology (diamond):

          AS2
        /     \
    AS1         AS4
        \     /
          AS3

    When link AS1-AS2 fails, AS1 re-routes to AS4 via AS3.
    """
    topo = NetworkTopology("Diamond")
    topo.add_as_node(1, prefixes=["10.1.0.0/24"])
    topo.add_as_node(2, prefixes=["10.2.0.0/24"])
    topo.add_as_node(3, prefixes=["10.3.0.0/24"])
    topo.add_as_node(4, prefixes=["10.4.0.0/24"])

    topo.add_link(1, 2)
    topo.add_link(1, 3)
    topo.add_link(2, 4)
    topo.add_link(3, 4)

    engine = PathVectorEngine(topo)
    init_stats = engine.run_initial_convergence()
    assert init_stats.converged is True
    assert init_stats.reachability_ratio == 1.0

    # AS1 previously had a route to AS4 via AS2 or AS3 (both 2 hops)
    sim = NetworkEventSimulator(engine)
    fail_result = sim.trigger_link_failure(1, 2)

    assert fail_result.stats.converged is True
    # Reachability must still be 100% because AS1-AS3-AS4 is alive
    assert engine.evaluate_reachability() == 1.0

    # AS1's route to AS4 must now go strictly through AS3
    r1 = engine.routers[1]
    route_to_4 = r1.loc_rib.get("10.4.0.0/24")
    assert route_to_4 is not None
    assert route_to_4.next_hop == 3
    assert route_to_4.as_path == (3, 4)


def test_link_recovery():
    """Tests link restoration and path re-advertisement."""
    topo = NetworkTopology("Triangle")
    topo.add_as_node(1, prefixes=["10.1.0.0/24"])
    topo.add_as_node(2, prefixes=["10.2.0.0/24"])
    topo.add_as_node(3, prefixes=["10.3.0.0/24"])
    topo.add_link(1, 2)
    topo.add_link(2, 3)

    engine = PathVectorEngine(topo)
    engine.run_initial_convergence()

    # Route from AS1 to AS3 is 2 hops via AS2
    r1 = engine.routers[1]
    assert r1.loc_rib["10.3.0.0/24"].path_length == 2

    # Now add direct link AS1-AS3 (link recovery/addition)
    sim = NetworkEventSimulator(engine)
    recovery_result = sim.trigger_link_recovery(1, 3)

    assert recovery_result.stats.converged is True
    # AS1 now has a direct 1-hop path to AS3
    assert r1.loc_rib["10.3.0.0/24"].path_length == 1
    assert r1.loc_rib["10.3.0.0/24"].next_hop == 3


def test_node_addition():
    """Tests joining of a new node and announcing its prefix."""
    topo = NetworkTopology("Pair")
    topo.add_as_node(1, prefixes=["10.1.0.0/24"])
    topo.add_as_node(2, prefixes=["10.2.0.0/24"])
    topo.add_link(1, 2)

    engine = PathVectorEngine(topo)
    engine.run_initial_convergence()

    sim = NetworkEventSimulator(engine)
    join_result = sim.trigger_node_addition(
        new_as_id=3,
        peer_as_ids=[2],
        prefixes=["10.3.0.0/24"],
    )

    assert join_result.stats.converged is True
    assert engine.evaluate_reachability() == 1.0
    assert "10.3.0.0/24" in engine.routers[1].loc_rib


def test_metrics_collector():
    collector = MetricsCollector()
    m = NetworkScaleMeasurement(
        num_nodes=50,
        num_edges=100,
        total_prefixes=100,
        topology_type="ScaleFree",
        convergence_rounds=12,
        convergence_time_sec=0.25,
        total_messages=450,
        update_messages=400,
        withdrawal_messages=50,
        avg_table_size=98.5,
        max_table_size=100,
        total_table_entries=4925,
        avg_memory_kb=32.4,
        total_memory_mb=1.62,
        avg_path_length=3.2,
        reachability_pct=100.0,
    )
    collector.record_scale_measurement(m)
    df = collector.to_scale_dataframe()
    assert len(df) == 1
    assert df["num_nodes"].iloc[0] == 50
    assert df["reachability_pct"].iloc[0] == 100.0
