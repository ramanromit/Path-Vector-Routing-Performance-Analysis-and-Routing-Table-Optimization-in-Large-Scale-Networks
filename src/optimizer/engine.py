"""Integrated Routing Table Optimizer Suite and Forwarding Verification Engine.

Applies optimization strategies:
- CIDR Prefix Aggregation
- Default Route Injection
- AS-Path Compression
- Combined Hybrid Optimization

Implements Longest Prefix Match (LPM) forwarding simulation to prove 100% reachability
is preserved after table optimization.
"""

from enum import Enum
import ipaddress
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from ..topology.generator import ASType, NetworkTopology
from ..routing.engine import PathVectorEngine
from ..routing.router import Route, Router
from ..metrics.collector import OptimizationComparisonRecord
from .aggregation import PrefixAggregationOptimizer
from .default_route import DefaultRouteOptimizer
from .compression import PathCompressionOptimizer


class OptimizationStrategy(Enum):
    """Available routing table optimization techniques."""
    PREFIX_AGGREGATION = "Prefix Aggregation (CIDR)"
    DEFAULT_ROUTE = "Default Route Injection"
    PATH_COMPRESSION = "AS-Path Compression"
    HYBRID = "Hybrid (All Optimizations Combined)"


class RoutingOptimizerSuite:
    """Orchestrates optimization passes and validates forwarding reachability."""

    def __init__(self, engine: PathVectorEngine):
        self.engine = engine
        self.topology = engine.topology
        # optimized_tables: as_id -> {prefix_or_supernet: Route}
        self.optimized_tables: Dict[int, Dict[str, Route]] = {}

    def apply_optimization(
        self,
        strategy: OptimizationStrategy = OptimizationStrategy.HYBRID,
    ) -> OptimizationComparisonRecord:
        """Applies the specified optimization strategy across all routers in the network."""
        self.optimized_tables.clear()

        # Step 1: Capture baseline metrics
        baseline_sizes = [r.table_size for r in self.engine.routers.values()]
        baseline_memories = [r.get_memory_estimate_bytes() for r in self.engine.routers.values()]
        baseline_avg_size = float(np.mean(baseline_sizes))
        baseline_mem_mb = float(np.sum(baseline_memories)) / (1024 * 1024)
        baseline_reachability = self.engine.evaluate_reachability() * 100.0

        # Step 2: Apply strategy per router
        for as_id, router in self.engine.routers.items():
            node = self.topology.get_node(as_id)
            is_transit = node.as_type != ASType.STUB if node else False

            if strategy == OptimizationStrategy.PREFIX_AGGREGATION:
                opt_table = PrefixAggregationOptimizer.aggregate_router_table(router)

            elif strategy == OptimizationStrategy.DEFAULT_ROUTE:
                opt_table = DefaultRouteOptimizer.optimize_router(
                    router=router,
                    topology=self.topology,
                    allow_multi_homed=False,
                )

            elif strategy == OptimizationStrategy.PATH_COMPRESSION:
                opt_table = PathCompressionOptimizer.compress_router_table(
                    router=router,
                    is_transit_node=is_transit,
                )

            elif strategy == OptimizationStrategy.HYBRID:
                # 1. Apply default route injection for strictly single-homed stubs (guaranteed 100% reachability)
                opt_table = DefaultRouteOptimizer.optimize_router(
                    router=router,
                    topology=self.topology,
                    allow_multi_homed=False,
                )
                # 2. For remaining routes, aggregate contiguous prefixes
                temp_router = Router(as_id=as_id)
                temp_router.loc_rib = opt_table
                opt_table = PrefixAggregationOptimizer.aggregate_router_table(temp_router)
                # 3. Compress AS-paths for non-transit nodes
                temp_router.loc_rib = opt_table
                opt_table = PathCompressionOptimizer.compress_router_table(
                    temp_router,
                    is_transit_node=is_transit,
                )
            else:
                opt_table = dict(router.loc_rib)

            self.optimized_tables[as_id] = opt_table

        # Step 3: Compute optimized metrics
        opt_sizes = [len(tbl) for tbl in self.optimized_tables.values()]
        opt_avg_size = float(np.mean(opt_sizes))

        opt_memories = []
        for tbl in self.optimized_tables.values():
            m = sum(256 + len(r.as_path) * 4 for r in tbl.values())
            opt_memories.append(m)
        opt_mem_mb = float(np.sum(opt_memories)) / (1024 * 1024)

        # Step 4: Validate Reachability using Longest-Prefix-Match forwarding simulation
        opt_reachability = self.validate_forwarding_reachability() * 100.0

        record = OptimizationComparisonRecord(
            num_nodes=self.topology.num_nodes,
            strategy=strategy.value,
            baseline_table_size=baseline_avg_size,
            baseline_memory_mb=baseline_mem_mb,
            baseline_convergence_rounds=0,
            baseline_total_messages=0,
            baseline_reachability_pct=baseline_reachability,
            baseline_path_length=0.0,
            optimized_table_size=opt_avg_size,
            optimized_memory_mb=opt_mem_mb,
            optimized_convergence_rounds=0,
            optimized_total_messages=0,
            optimized_reachability_pct=opt_reachability,
            optimized_path_length=0.0,
        )

        if baseline_avg_size > 0:
            record.table_size_reduction_pct = max(
                0.0, ((baseline_avg_size - opt_avg_size) / baseline_avg_size) * 100.0
            )
        if baseline_mem_mb > 0:
            record.memory_savings_pct = max(
                0.0, ((baseline_mem_mb - opt_mem_mb) / baseline_mem_mb) * 100.0
            )

        return record

    def longest_prefix_match(self, as_id: int, target_prefix: str) -> Optional[Route]:
        """Performs Longest Prefix Matching (LPM) on the router's optimized table."""
        tbl = self.optimized_tables.get(as_id)
        if not tbl:
            return None

        # 1. Exact match
        if target_prefix in tbl:
            return tbl[target_prefix]

        # 2. Longest subnet/supernet match
        if not hasattr(self, "_parsed_tables"):
            self._parsed_tables: Dict[int, List[Tuple[ipaddress.IPv4Network, Route]]] = {}

        if as_id not in self._parsed_tables:
            parsed_list = []
            for pfx_str, r in tbl.items():
                if pfx_str != "0.0.0.0/0":
                    parsed_list.append((ipaddress.IPv4Network(pfx_str), r))
            # Sort by prefixlen descending so first match is longest
            parsed_list.sort(key=lambda item: item[0].prefixlen, reverse=True)
            self._parsed_tables[as_id] = parsed_list

        target_net = ipaddress.IPv4Network(target_prefix)
        for entry_net, route in self._parsed_tables[as_id]:
            if entry_net.supernet_of(target_net) or entry_net == target_net:
                return route

        # 3. Default route fallback
        if "0.0.0.0/0" in tbl:
            return tbl["0.0.0.0/0"]

        return None

    def validate_forwarding_reachability(self, max_hops: int = 50, sample_size: int = 2500) -> float:
        """Simulates packet forwarding hop-by-hop from source ASes to destination prefixes.

        Confirms whether a packet forwarded via the optimized tables reaches the true origin AS
        without looping or dropping. Validates 100% of pairs for small/medium graphs, and a
        representative sample of pairs for very large networks.
        """
        all_originated: Dict[str, int] = {}
        for r in self.engine.routers.values():
            for pfx in r.originated_prefixes:
                all_originated[pfx] = r.as_id

        if not all_originated or not self.optimized_tables:
            return 1.0

        # Reset parsed cache
        self._parsed_tables = {}

        # Generate test pairs
        all_sources = list(self.optimized_tables.keys())
        all_dest_prefixes = list(all_originated.items())
        total_possible = len(all_sources) * len(all_dest_prefixes)

        import random
        if total_possible <= sample_size:
            test_pairs = [(s, p, o) for s in all_sources for p, o in all_dest_prefixes]
        else:
            rng = random.Random(42)
            test_pairs = [
                (rng.choice(all_sources), *rng.choice(all_dest_prefixes))
                for _ in range(sample_size)
            ]

        successful_tests = 0

        for src_as, dest_prefix, true_origin_as in test_pairs:
            if src_as == true_origin_as:
                successful_tests += 1
                continue

            current_as = src_as
            visited: Set[int] = {current_as}
            hops = 0
            delivered = False

            while hops < max_hops:
                hops += 1
                route = self.longest_prefix_match(current_as, dest_prefix)
                if route is None:
                    break

                next_as = route.next_hop
                if next_as == current_as:
                    delivered = (current_as == true_origin_as)
                    break

                if next_as == true_origin_as:
                    delivered = True
                    break

                if next_as in visited:
                    break

                visited.add(next_as)
                current_as = next_as

            if delivered:
                successful_tests += 1

        return (successful_tests / len(test_pairs)) if test_pairs else 1.0
