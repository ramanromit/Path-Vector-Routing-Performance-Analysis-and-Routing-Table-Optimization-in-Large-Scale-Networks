"""IP Prefix Allocator for Autonomous Systems.

Allocates realistic IPv4 CIDR blocks to Autonomous Systems.
Supports allocating contiguous blocks (e.g., pairs or quads of /24s) to allow
testing CIDR Route Summarization / Prefix Aggregation in Phase 4.
"""

import ipaddress
from typing import Dict, List, Optional
from .generator import ASType, NetworkTopology


class PrefixAllocator:
    """Allocates IPv4 network prefixes to AS nodes in a topology."""

    def __init__(self, base_network: str = "10.0.0.0/8"):
        self.base_network = ipaddress.IPv4Network(base_network)
        self.allocated_prefixes: Dict[str, int] = {}  # prefix_str -> origin_as_id
        self.as_to_prefixes: Dict[int, List[str]] = {}  # as_id -> [prefix_str, ...]

    def allocate(
        self,
        topology: NetworkTopology,
        prefixes_per_as: int = 2,
        hierarchical: bool = True,
    ) -> Dict[int, List[str]]:
        """Allocates IPv4 prefixes to each node in the topology.

        If hierarchical=True:
        - Core (Tier-1) nodes get 4 contiguous /24 prefixes (aggregatable to /22)
        - Transit (Tier-2) nodes get 2 contiguous /24 prefixes (aggregatable to /23)
        - Stub nodes get 1 or 2 prefixes
        If hierarchical=False:
        - Every node gets `prefixes_per_as` prefixes

        Returns:
            Dictionary mapping as_id to list of allocated prefix strings.
        """
        self.allocated_prefixes.clear()
        self.as_to_prefixes.clear()

        # Generate a deterministic pool of /24 subnets from base network
        # E.g., 10.0.0.0/24, 10.0.1.0/24, ...
        # 10.0.0.0/8 yields 65,536 /24 subnets
        subnet_iterator = self.base_network.subnets(new_prefix=24)

        for as_id in sorted(topology.nodes.keys()):
            node = topology.nodes[as_id]
            if hierarchical:
                if node.as_type == ASType.CORE:
                    count = 4
                elif node.as_type == ASType.TRANSIT:
                    count = 2
                else:
                    count = 2  # 2 contiguous /24s allow stub aggregation
            else:
                count = prefixes_per_as

            node_prefixes = []
            for _ in range(count):
                subnet = next(subnet_iterator)
                subnet_str = str(subnet)
                node_prefixes.append(subnet_str)
                self.allocated_prefixes[subnet_str] = as_id

            node.prefixes = node_prefixes
            self.as_to_prefixes[as_id] = node_prefixes

        return self.as_to_prefixes

    def get_origin_as(self, prefix: str) -> Optional[int]:
        """Returns the originating AS number for a given prefix."""
        return self.allocated_prefixes.get(prefix)

    @property
    def total_prefixes(self) -> int:
        return len(self.allocated_prefixes)
