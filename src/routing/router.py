"""BGP Router Implementation with Path Vector Routing Information Base (RIB).

Implements:
- Adj-RIB-In (received routes per peer)
- Loc-RIB (selected best routes)
- Adj-RIB-Out (advertised routes per peer)
- Strict Loop Prevention (AS_PATH inspection)
- Standard BGP Best-Path Selection Algorithm
- Incremental UPDATE / WITHDRAWAL generation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from .messages import MessageType, RouteMessage


@dataclass(frozen=True)
class Route:
    """Represents a path vector route entry."""
    prefix: str
    as_path: Tuple[int, ...]
    next_hop: int
    metric: int = 0

    @property
    def path_length(self) -> int:
        return len(self.as_path)

    @property
    def origin_as(self) -> int:
        return self.as_path[-1] if self.as_path else self.next_hop


class Router:
    """Autonomous System BGP Path Vector Router."""

    def __init__(self, as_id: int):
        self.as_id = as_id
        self.neighbors: Set[int] = set()
        self.originated_prefixes: Set[str] = set()

        # BGP Routing Information Bases
        # adj_rib_in: neighbor_as -> {prefix: Route}
        self.adj_rib_in: Dict[int, Dict[str, Route]] = {}

        # loc_rib: prefix -> selected best Route
        self.loc_rib: Dict[str, Route] = {}

        # adj_rib_out: neighbor_as -> {prefix: Route}
        self.adj_rib_out: Dict[int, Dict[str, Route]] = {}

    def add_neighbor(self, neighbor_as: int) -> None:
        self.neighbors.add(neighbor_as)
        if neighbor_as not in self.adj_rib_in:
            self.adj_rib_in[neighbor_as] = {}
        if neighbor_as not in self.adj_rib_out:
            self.adj_rib_out[neighbor_as] = {}

    def remove_neighbor(self, neighbor_as: int) -> List[RouteMessage]:
        """Handles peer link failure: purges routes learned from neighbor and recalculates."""
        self.neighbors.discard(neighbor_as)
        outbound_messages: List[RouteMessage] = []

        affected_prefixes = list(self.adj_rib_in.get(neighbor_as, {}).keys())
        if neighbor_as in self.adj_rib_in:
            del self.adj_rib_in[neighbor_as]
        if neighbor_as in self.adj_rib_out:
            del self.adj_rib_out[neighbor_as]

        for prefix in affected_prefixes:
            msgs = self._reevaluate_prefix(prefix)
            outbound_messages.extend(msgs)

        return outbound_messages

    def add_originated_prefix(self, prefix: str) -> None:
        self.originated_prefixes.add(prefix)
        # Originated route in local AS has empty as_path, next_hop is self
        route = Route(prefix=prefix, as_path=(), next_hop=self.as_id)
        self.loc_rib[prefix] = route

    def originate_all_routes(self) -> List[RouteMessage]:
        """Generates initial announcements to all neighbors for originated prefixes."""
        messages: List[RouteMessage] = []
        for prefix in self.originated_prefixes:
            route = Route(prefix=prefix, as_path=(), next_hop=self.as_id)
            self.loc_rib[prefix] = route

            outbound_path = (self.as_id,)
            for neighbor in self.neighbors:
                msg = RouteMessage(
                    msg_type=MessageType.UPDATE,
                    sender_as=self.as_id,
                    receiver_as=neighbor,
                    prefix=prefix,
                    as_path=outbound_path,
                    next_hop=self.as_id,
                )
                advertised_route = Route(
                    prefix=prefix,
                    as_path=outbound_path,
                    next_hop=self.as_id,
                )
                self.adj_rib_out[neighbor][prefix] = advertised_route
                messages.append(msg)
        return messages

    def receive_message(self, msg: RouteMessage) -> List[RouteMessage]:
        """Processes an incoming UPDATE or WITHDRAWAL message and returns outgoing messages."""
        if msg.receiver_as != self.as_id:
            return []

        sender = msg.sender_as

        if msg.is_withdrawal:
            return self._handle_withdrawal(sender, msg.prefix)
        else:
            return self._handle_update(sender, msg)

    def _handle_update(self, sender: int, msg: RouteMessage) -> List[RouteMessage]:
        """Processes an incoming UPDATE. Discards if loop is detected."""
        # 1. Loop Prevention: if our AS is already in the path, reject message
        if msg.contains_as(self.as_id):
            return []

        # 2. Store in Adj-RIB-In
        route = Route(
            prefix=msg.prefix,
            as_path=msg.as_path,
            next_hop=sender,
            metric=msg.metric,
        )
        if sender not in self.adj_rib_in:
            self.adj_rib_in[sender] = {}
        self.adj_rib_in[sender][msg.prefix] = route

        # 3. Decision Process
        return self._reevaluate_prefix(msg.prefix)

    def _handle_withdrawal(self, sender: int, prefix: str) -> List[RouteMessage]:
        """Processes incoming WITHDRAWAL from a peer."""
        if sender in self.adj_rib_in and prefix in self.adj_rib_in[sender]:
            del self.adj_rib_in[sender][prefix]

        return self._reevaluate_prefix(prefix)

    def _reevaluate_prefix(self, prefix: str) -> List[RouteMessage]:
        """Re-runs BGP decision process for a prefix and advertises updates if best path changed."""
        old_best = self.loc_rib.get(prefix)

        # If this prefix is locally originated, local route is always preferred
        if prefix in self.originated_prefixes:
            new_best = Route(prefix=prefix, as_path=(), next_hop=self.as_id)
        else:
            new_best = self._select_best_route(prefix)

        # If no change in best path, do nothing
        if old_best == new_best:
            return []

        # Update Loc-RIB
        if new_best is not None:
            self.loc_rib[prefix] = new_best
        else:
            if prefix in self.loc_rib:
                del self.loc_rib[prefix]

        # Generate updates/withdrawals for peers
        outbound: List[RouteMessage] = []
        for neighbor in self.neighbors:
            if new_best is None:
                # Send WITHDRAWAL if we previously advertised this prefix to neighbor
                if neighbor in self.adj_rib_out and prefix in self.adj_rib_out[neighbor]:
                    del self.adj_rib_out[neighbor][prefix]
                    outbound.append(
                        RouteMessage(
                            msg_type=MessageType.WITHDRAWAL,
                            sender_as=self.as_id,
                            receiver_as=neighbor,
                            prefix=prefix,
                        )
                    )
            else:
                # Do not advertise back along the path (split-horizon / loop filter)
                if neighbor in new_best.as_path:
                    continue

                # Prepend self.as_id to AS_PATH for outbound advertisement
                outbound_path = (self.as_id,) + new_best.as_path
                advertised_route = Route(
                    prefix=prefix,
                    as_path=outbound_path,
                    next_hop=self.as_id,
                )

                # Only send if different from what was previously advertised
                if self.adj_rib_out[neighbor].get(prefix) != advertised_route:
                    self.adj_rib_out[neighbor][prefix] = advertised_route
                    outbound.append(
                        RouteMessage(
                            msg_type=MessageType.UPDATE,
                            sender_as=self.as_id,
                            receiver_as=neighbor,
                            prefix=prefix,
                            as_path=outbound_path,
                            next_hop=self.as_id,
                        )
                    )

        return outbound

    def _select_best_route(self, prefix: str) -> Optional[Route]:
        """BGP Decision Algorithm:

        1. Filter loop-free paths (already checked upon intake, but verified).
        2. Shortest AS-Path length.
        3. Deterministic tie-breaker: lowest next_hop AS number.
        """
        candidates: List[Route] = []
        for neighbor, peer_routes in self.adj_rib_in.items():
            if prefix in peer_routes:
                route = peer_routes[prefix]
                if self.as_id not in route.as_path:
                    candidates.append(route)

        if not candidates:
            return None

        # Sort: first by path length (ascending), then by next_hop (ascending)
        candidates.sort(key=lambda r: (r.path_length, r.next_hop))
        return candidates[0]

    @property
    def table_size(self) -> int:
        """Returns number of active routes in Loc-RIB."""
        return len(self.loc_rib)

    def get_memory_estimate_bytes(self) -> int:
        """Estimates router memory usage for BGP tables (Loc-RIB + Adj-RIB-In)."""
        total_bytes = 0
        # Loc-RIB memory
        for route in self.loc_rib.values():
            total_bytes += 256 + (len(route.as_path) * 4)

        # Adj-RIB-In memory
        for peer_routes in self.adj_rib_in.values():
            for route in peer_routes.values():
                total_bytes += 128 + (len(route.as_path) * 4)

        return total_bytes
