"""CIDR Route Summarization and Prefix Aggregation Optimizer.

Merges contiguous IPv4 prefixes sharing identical next-hop and AS-path attributes
into supernets (e.g., 10.1.0.0/24 + 10.1.1.0/24 -> 10.1.0.0/23).
Preserves 100% reachability while significantly shrinking routing table entries.
"""

from collections import defaultdict
import ipaddress
from typing import Dict, List, Set, Tuple
from ..routing.router import Route, Router


class PrefixAggregationOptimizer:
    """Aggregates contiguous IP prefixes with matching forwarding attributes."""

    @staticmethod
    def aggregate_router_table(router: Router) -> Dict[str, Route]:
        """Performs CIDR route aggregation on a router's Loc-RIB.

        Groups entries by (next_hop, as_path), collapses contiguous networks,
        and constructs an optimized routing table.

        Returns:
            Optimized routing table mapping summarized prefix to Route.
        """
        # Group prefixes by identical forwarding action (next_hop, as_path)
        groups: Dict[Tuple[int, Tuple[int, ...]], List[ipaddress.IPv4Network]] = defaultdict(list)
        route_meta: Dict[Tuple[int, Tuple[int, ...]], Route] = {}

        for prefix_str, route in router.loc_rib.items():
            if prefix_str == "0.0.0.0/0":
                continue  # Default route handled separately
            key = (route.next_hop, route.as_path)
            net = ipaddress.IPv4Network(prefix_str)
            groups[key].append(net)
            if key not in route_meta:
                route_meta[key] = route

        optimized_table: Dict[str, Route] = {}

        # If default route exists, preserve it
        if "0.0.0.0/0" in router.loc_rib:
            optimized_table["0.0.0.0/0"] = router.loc_rib["0.0.0.0/0"]

        for key, net_list in groups.items():
            # ipaddress.collapse_addresses merges contiguous /24s into /23s, /22s, etc.
            collapsed_nets = list(ipaddress.collapse_addresses(net_list))
            base_route = route_meta[key]

            for net in collapsed_nets:
                collapsed_prefix = str(net)
                optimized_table[collapsed_prefix] = Route(
                    prefix=collapsed_prefix,
                    as_path=base_route.as_path,
                    next_hop=base_route.next_hop,
                    metric=base_route.metric,
                )

        return optimized_table
