"""Unit tests for BGP Path Vector Routing Engine."""

import pytest
from src.topology.generator import NetworkTopology, generate_scale_free_topology
from src.topology.prefix_allocator import PrefixAllocator
from src.routing.messages import MessageType, RouteMessage
from src.routing.router import Route, Router
from src.routing.engine import PathVectorEngine


def test_linear_topology_convergence():
    """Tests convergence and path vector propagation on a 3-node line: AS1 - AS2 - AS3."""
    topo = NetworkTopology("Line3")
    topo.add_as_node(1, prefixes=["10.1.0.0/24"])
    topo.add_as_node(2, prefixes=["10.2.0.0/24"])
    topo.add_as_node(3, prefixes=["10.3.0.0/24"])
    topo.add_link(1, 2)
    topo.add_link(2, 3)

    engine = PathVectorEngine(topo)
    stats = engine.run_initial_convergence(max_rounds=50)

    assert stats.converged is True
    assert stats.reachability_ratio == 1.0
    assert stats.total_messages > 0

    # AS1 should have route to AS3 prefix via AS2 with path (2, 3)
    r1 = engine.routers[1]
    route_to_3 = r1.loc_rib.get("10.3.0.0/24")
    assert route_to_3 is not None
    assert route_to_3.next_hop == 2
    assert route_to_3.as_path == (2, 3)

    # AS3 should have route to AS1 prefix via AS2 with path (2, 1)
    r3 = engine.routers[3]
    route_to_1 = r3.loc_rib.get("10.1.0.0/24")
    assert route_to_1 is not None
    assert route_to_1.next_hop == 2
    assert route_to_1.as_path == (2, 1)


def test_triangle_loop_prevention_and_shortest_path():
    r"""Tests that loop prevention prevents counting-to-infinity and shortest path is selected in triangle:

    AS1 --- AS2
      \     /
       \   /
        AS3
    """
    topo = NetworkTopology("Triangle")
    topo.add_as_node(1, prefixes=["10.1.0.0/24"])
    topo.add_as_node(2, prefixes=["10.2.0.0/24"])
    topo.add_as_node(3, prefixes=["10.3.0.0/24"])
    topo.add_link(1, 2)
    topo.add_link(2, 3)
    topo.add_link(1, 3)

    engine = PathVectorEngine(topo)
    stats = engine.run_initial_convergence(max_rounds=50)

    assert stats.converged is True
    assert stats.reachability_ratio == 1.0

    # AS1 is directly connected to AS3, so path to AS3's prefix must be direct (3,)
    r1 = engine.routers[1]
    route_to_3 = r1.loc_rib.get("10.3.0.0/24")
    assert route_to_3 is not None
    assert route_to_3.next_hop == 3
    assert route_to_3.as_path == (3,)
    assert route_to_3.path_length == 1


def test_scale_free_network_convergence():
    """Tests convergence on a 20-node scale-free topology with PrefixAllocator."""
    topo = generate_scale_free_topology(num_nodes=20, m_attachments=2, seed=42)
    allocator = PrefixAllocator()
    allocator.allocate(topo, hierarchical=True)

    engine = PathVectorEngine(topo)
    stats = engine.run_initial_convergence(max_rounds=100)

    assert stats.converged is True
    assert stats.reachability_ratio == 1.0
    assert stats.avg_table_size >= 20  # Routers know all prefixes
    assert stats.total_memory_bytes > 0
    assert stats.avg_path_length >= 1.0
