"""Unit tests for Network Topology and Prefix Allocation."""

import pytest
from src.topology.generator import (
    ASType,
    NetworkTopology,
    generate_scale_free_topology,
    generate_random_topology,
)
from src.topology.prefix_allocator import PrefixAllocator


def test_scale_free_topology_generation():
    num_nodes = 20
    topo = generate_scale_free_topology(num_nodes=num_nodes, m_attachments=2, seed=42)

    assert topo.num_nodes == num_nodes
    assert topo.num_edges >= num_nodes - 1
    assert topo.is_connected()

    summary = topo.get_summary()
    assert summary["num_nodes"] == num_nodes
    assert summary["is_connected"] is True
    assert summary["avg_degree"] > 1.5
    assert summary["diameter"] is not None

    # Verify tiers are classified
    tier_dist = summary["tier_distribution"]
    assert tier_dist[ASType.CORE.value] >= 1
    assert tier_dist[ASType.STUB.value] >= 1


def test_random_topology_generation():
    num_nodes = 25
    topo = generate_random_topology(num_nodes=num_nodes, p=0.15, seed=123)

    assert topo.num_nodes == num_nodes
    assert topo.is_connected()
    assert topo.num_edges > 0


def test_topology_link_and_node_operations():
    topo = NetworkTopology(name="TestNet")
    topo.add_link(1, 2)
    topo.add_link(2, 3)
    topo.add_link(3, 4)

    assert topo.num_nodes == 4
    assert topo.num_edges == 3
    assert topo.is_connected()
    assert topo.get_neighbors(2) == [1, 3]

    # Test link removal (failure)
    removed = topo.remove_link(2, 3)
    assert removed is True
    assert not topo.is_connected()
    assert topo.num_edges == 2

    # Reconnect
    topo.add_link(2, 3)
    assert topo.is_connected()

    # Test node removal
    removed_node = topo.remove_as_node(4)
    assert removed_node is True
    assert topo.num_nodes == 3
    assert 4 not in topo.nodes


def test_prefix_allocator():
    topo = generate_scale_free_topology(num_nodes=10, m_attachments=2, seed=42)
    allocator = PrefixAllocator(base_network="10.0.0.0/16")
    prefix_map = allocator.allocate(topo, hierarchical=True)

    assert len(prefix_map) == 10
    total_allocated = allocator.total_prefixes
    assert total_allocated >= 20  # At least 2 prefixes per node

    # Check origin mapping
    for as_id, prefixes in prefix_map.items():
        assert len(prefixes) >= 2
        for p in prefixes:
            assert allocator.get_origin_as(p) == as_id
