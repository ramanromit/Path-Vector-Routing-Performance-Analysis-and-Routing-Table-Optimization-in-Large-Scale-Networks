"""Topology generation and prefix allocation modules."""

from .generator import NetworkTopology, generate_scale_free_topology, generate_random_topology
from .prefix_allocator import PrefixAllocator

__all__ = [
    "NetworkTopology",
    "generate_scale_free_topology",
    "generate_random_topology",
    "PrefixAllocator",
]
