"""Discrete Event Simulation Engine for Path Vector Routing.

Executes round-based discrete-event propagation of BGP UPDATE and WITHDRAWAL messages,
detects convergence, measures control overhead, and evaluates network-wide reachability.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from ..topology.generator import NetworkTopology
from .messages import MessageType, RouteMessage
from .router import Route, Router


@dataclass
class ConvergenceStats:
    """Statistics captured during a simulation run."""
    converged: bool
    rounds: int
    total_messages: int
    update_messages: int
    withdrawal_messages: int
    avg_table_size: float
    max_table_size: int
    total_table_entries: int
    avg_path_length: float
    reachability_ratio: float
    total_memory_bytes: int
    messages_per_round: List[int] = field(default_factory=list)


class PathVectorEngine:
    """Discrete Event Simulator for BGP Path Vector Routing."""

    def __init__(self, topology: NetworkTopology):
        self.topology = topology
        self.routers: Dict[int, Router] = {}
        self._initialize_routers()

    def _initialize_routers(self) -> None:
        """Instantiates routers and binds peer neighbors and prefixes from topology."""
        self.routers.clear()

        # Create Router instances
        for as_id, node in self.topology.nodes.items():
            router = Router(as_id=as_id)
            for p in node.prefixes:
                router.add_originated_prefix(p)
            self.routers[as_id] = router

        # Connect neighbors according to topology graph edges
        for u, v in self.topology.graph.edges():
            if u in self.routers and v in self.routers:
                self.routers[u].add_neighbor(v)
                self.routers[v].add_neighbor(u)

    def run_initial_convergence(self, max_rounds: int = 500) -> ConvergenceStats:
        """Initiates route announcements and runs until network reaches steady-state convergence."""
        initial_messages: List[RouteMessage] = []
        for router in self.routers.values():
            initial_messages.extend(router.originate_all_routes())

        return self.run_event_loop(initial_messages, max_rounds=max_rounds)

    def run_event_loop(
        self,
        pending_messages: List[RouteMessage],
        max_rounds: int = 500,
    ) -> ConvergenceStats:
        """Simulates discrete rounds of message propagation until convergence."""
        current_queue: List[RouteMessage] = list(pending_messages)
        round_num = 0
        total_updates = 0
        total_withdrawals = 0
        messages_per_round: List[int] = []

        while current_queue and round_num < max_rounds:
            round_num += 1
            round_msg_count = len(current_queue)
            messages_per_round.append(round_msg_count)

            # Categorize message counts
            for msg in current_queue:
                if msg.is_withdrawal:
                    total_withdrawals += 1
                else:
                    total_updates += 1

            # Dispatch messages to target routers in parallel for this round
            # Group by receiver
            messages_by_receiver: Dict[int, List[RouteMessage]] = {}
            for msg in current_queue:
                messages_by_receiver.setdefault(msg.receiver_as, []).append(msg)

            next_queue: List[RouteMessage] = []
            for receiver_as, msgs in messages_by_receiver.items():
                router = self.routers.get(receiver_as)
                if router is None:
                    continue
                for msg in msgs:
                    outgoing = router.receive_message(msg)
                    next_queue.extend(outgoing)

            current_queue = next_queue

        converged = len(current_queue) == 0

        # Compute post-convergence metrics
        stats = self._calculate_current_stats(
            converged=converged,
            rounds=round_num,
            total_updates=total_updates,
            total_withdrawals=total_withdrawals,
            messages_per_round=messages_per_round,
        )
        return stats

    def _calculate_current_stats(
        self,
        converged: bool,
        rounds: int,
        total_updates: int,
        total_withdrawals: int,
        messages_per_round: List[int],
    ) -> ConvergenceStats:
        """Gathers aggregate routing table, memory, path length, and reachability metrics."""
        table_sizes = [r.table_size for r in self.routers.values()]
        memories = [r.get_memory_estimate_bytes() for r in self.routers.values()]

        # Path lengths across all installed routes in Loc-RIBs
        path_lengths: List[int] = []
        for r in self.routers.values():
            for prefix, route in r.loc_rib.items():
                if route.origin_as != r.as_id:  # Only measure paths to remote destinations
                    path_lengths.append(len(route.as_path))

        avg_path_len = float(np.mean(path_lengths)) if path_lengths else 0.0

        # Calculate Reachability
        reachability = self.evaluate_reachability()

        return ConvergenceStats(
            converged=converged,
            rounds=rounds,
            total_messages=total_updates + total_withdrawals,
            update_messages=total_updates,
            withdrawal_messages=total_withdrawals,
            avg_table_size=float(np.mean(table_sizes)) if table_sizes else 0.0,
            max_table_size=int(np.max(table_sizes)) if table_sizes else 0,
            total_table_entries=int(np.sum(table_sizes)) if table_sizes else 0,
            avg_path_length=avg_path_len,
            reachability_ratio=reachability,
            total_memory_bytes=int(np.sum(memories)),
            messages_per_round=messages_per_round,
        )

    def evaluate_reachability(self) -> float:
        """Evaluates what fraction of all expected (source, target_prefix) pairs are reachable."""
        # Collect all active originated prefixes in the network
        all_originated: Dict[str, int] = {}
        for r in self.routers.values():
            for pfx in r.originated_prefixes:
                all_originated[pfx] = r.as_id

        if not all_originated or not self.routers:
            return 1.0

        reachable_count = 0
        total_pairs = 0

        for src_as, router in self.routers.items():
            for prefix, origin_as in all_originated.items():
                total_pairs += 1
                if origin_as == src_as:
                    reachable_count += 1
                elif prefix in router.loc_rib:
                    # Verify route is valid and loop-free
                    route = router.loc_rib[prefix]
                    if src_as not in route.as_path and route.origin_as == origin_as:
                        reachable_count += 1

        return reachable_count / total_pairs if total_pairs > 0 else 1.0

    def get_route(self, src_as: int, prefix: str) -> Optional[Route]:
        """Looks up the installed route for a prefix in a given router."""
        router = self.routers.get(src_as)
        if router:
            return router.loc_rib.get(prefix)
        return None
