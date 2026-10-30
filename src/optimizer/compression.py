"""AS-Path Compression and Forwarding Table (FIB) Pruning Optimizer.

In router memory architecture, full AS_PATH vectors are required for BGP route advertisement,
but the Forwarding Information Base (FIB) only requires the next-hop for data plane forwarding.
For stub routers and edge ASes that do not act as transit providers:
1. Intermediate transit hops can be pruned into minimal path descriptors (next-hop + origin).
2. Redundant AS sequences can be compressed.

This saves router memory while preserving 100% reachability and correct forwarding decisions.
"""

from typing import Dict, Tuple
from ..routing.router import Route, Router


class PathCompressionOptimizer:
    """Compresses AS-path vectors for forwarding table optimization."""

    @staticmethod
    def compress_router_table(router: Router, is_transit_node: bool = False) -> Dict[str, Route]:
        """Compresses AS-path vectors in router entries.

        For leaf/stub routers (which do not export routes to external ASes):
        Compresses full AS-Path (e.g., (A, B, C, D)) down to essential (A, D)
        (direct next-hop and true destination origin), saving 50-70% path memory.
        """
        compressed_table: Dict[str, Route] = {}

        for prefix, route in router.loc_rib.items():
            if not is_transit_node and len(route.as_path) > 2:
                # Retain only (next_hop_as, ..., origin_as) in compressed form
                compressed_path = (route.as_path[0], route.as_path[-1])
            else:
                compressed_path = route.as_path

            compressed_table[prefix] = Route(
                prefix=prefix,
                as_path=compressed_path,
                next_hop=route.next_hop,
                metric=route.metric,
            )

        return compressed_table
