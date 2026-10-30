"""Default Route Injection Optimizer for Stub Autonomous Systems.

In Internet routing, stub/leaf ASes with a single upstream provider (or primary provider)
do not need the full Internet routing table. They only need:
1. Locally originated prefixes
2. A single default route (0.0.0.0/0) pointing to their upstream transit provider.

This reduces routing table size in edge routers by up to 80-95% with zero reachability loss.
"""

from typing import Dict, Set
from ..topology.generator import NetworkTopology
from ..routing.router import Route, Router


class DefaultRouteOptimizer:
    """Injects default routes (0.0.0.0/0) into single-homed and leaf stub routers."""

    @staticmethod
    def optimize_router(
        router: Router,
        topology: NetworkTopology,
        allow_multi_homed: bool = False,
    ) -> Dict[str, Route]:
        """Replaces remote routes with a default route if the router is a stub.

        Args:
            router: The router to optimize.
            topology: The network topology context.
            allow_multi_homed: If True, multi-homed stubs pick lowest AS peer as default.

        Returns:
            Optimized routing table.
        """
        neighbors = topology.get_neighbors(router.as_id)

        # Single-homed stub condition: exactly 1 peer/neighbor
        is_single_homed = len(neighbors) == 1
        is_candidate_stub = is_single_homed or (allow_multi_homed and len(neighbors) <= 2)

        if not is_candidate_stub or len(neighbors) == 0:
            # Not a stub; keep full routing table
            return dict(router.loc_rib)

        upstream_peer = min(neighbors)  # deterministic upstream provider

        optimized_table: Dict[str, Route] = {}

        # 1. Retain all locally originated prefixes
        for prefix in router.originated_prefixes:
            if prefix in router.loc_rib:
                optimized_table[prefix] = router.loc_rib[prefix]

        # 2. Inject default route 0.0.0.0/0 pointing to upstream provider
        optimized_table["0.0.0.0/0"] = Route(
            prefix="0.0.0.0/0",
            as_path=(upstream_peer,),
            next_hop=upstream_peer,
            metric=0,
        )

        return optimized_table
