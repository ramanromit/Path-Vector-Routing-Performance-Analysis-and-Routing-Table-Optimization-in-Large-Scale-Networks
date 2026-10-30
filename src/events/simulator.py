"""Network Events Simulator for Path Vector Routing.

Simulates dynamic topology events:
- Link Failure (triggering BGP WITHDRAWAL cascades and path hunting / reconvergence)
- Link Recovery (triggering alternate best path re-advertisements)
- Node Addition (new AS joining the topology and announcing its prefixes)
- Node Failure (complete AS shutdown and network-wide prefix withdrawal)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import time

from ..topology.generator import ASType
from ..routing.engine import ConvergenceStats, PathVectorEngine
from ..routing.messages import MessageType, RouteMessage
from ..routing.router import Route


@dataclass
class EventResult:
    """Outcome and performance impact of a network event."""
    event_type: str
    target: str
    stats: ConvergenceStats
    execution_time_sec: float
    description: str


class NetworkEventSimulator:
    """Manages and executes dynamic network events on an active PathVectorEngine."""

    def __init__(self, engine: PathVectorEngine):
        self.engine = engine

    def trigger_link_failure(self, as_u: int, as_v: int) -> EventResult:
        """Simulates an abrupt link failure between two connected ASes.

        Removes the edge from the topology, removes the peer from both routers,
        generates initial WITHDRAWAL messages, and executes the reconvergence loop.
        """
        start_time = time.perf_counter()

        if not self.engine.topology.graph.has_edge(as_u, as_v):
            raise ValueError(f"Link between AS{as_u} and AS{as_v} does not exist.")

        # 1. Update topology
        self.engine.topology.remove_link(as_u, as_v)

        # 2. Trigger neighbor teardown on both routers
        router_u = self.engine.routers[as_u]
        router_v = self.engine.routers[as_v]

        initial_messages: List[RouteMessage] = []
        initial_messages.extend(router_u.remove_neighbor(as_v))
        initial_messages.extend(router_v.remove_neighbor(as_u))

        # 3. Simulate reconvergence
        stats = self.engine.run_event_loop(initial_messages)
        duration = time.perf_counter() - start_time

        return EventResult(
            event_type="LINK_FAILURE",
            target=f"AS{as_u} <-> AS{as_v}",
            stats=stats,
            execution_time_sec=duration,
            description=f"Link failure between AS{as_u} and AS{as_v} resulted in {stats.total_messages} messages across {stats.rounds} rounds.",
        )

    def trigger_link_recovery(self, as_u: int, as_v: int) -> EventResult:
        """Restores a failed link between two ASes and re-advertises existing routes."""
        start_time = time.perf_counter()

        # 1. Update topology
        self.engine.topology.add_link(as_u, as_v)

        # 2. Update routers
        router_u = self.engine.routers[as_u]
        router_v = self.engine.routers[as_v]
        router_u.add_neighbor(as_v)
        router_v.add_neighbor(as_u)

        # 3. Exchange current Loc-RIB routes with each other across new link
        initial_messages: List[RouteMessage] = []
        for prefix, route in router_u.loc_rib.items():
            if as_v not in route.as_path:
                outbound_path = (as_u,) + route.as_path
                msg = RouteMessage(
                    msg_type=MessageType.UPDATE,
                    sender_as=as_u,
                    receiver_as=as_v,
                    prefix=prefix,
                    as_path=outbound_path,
                    next_hop=as_u,
                )
                advertised_route = Route(
                    prefix=prefix,
                    as_path=outbound_path,
                    next_hop=as_u,
                )
                router_u.adj_rib_out[as_v][prefix] = advertised_route
                initial_messages.append(msg)

        for prefix, route in router_v.loc_rib.items():
            if as_u not in route.as_path:
                outbound_path = (as_v,) + route.as_path
                msg = RouteMessage(
                    msg_type=MessageType.UPDATE,
                    sender_as=as_v,
                    receiver_as=as_u,
                    prefix=prefix,
                    as_path=outbound_path,
                    next_hop=as_v,
                )
                advertised_route = Route(
                    prefix=prefix,
                    as_path=outbound_path,
                    next_hop=as_v,
                )
                router_v.adj_rib_out[as_u][prefix] = advertised_route
                initial_messages.append(msg)

        # 4. Run reconvergence
        stats = self.engine.run_event_loop(initial_messages)
        duration = time.perf_counter() - start_time

        return EventResult(
            event_type="LINK_RECOVERY",
            target=f"AS{as_u} <-> AS{as_v}",
            stats=stats,
            execution_time_sec=duration,
            description=f"Link recovery between AS{as_u} and AS{as_v} reconverged in {stats.rounds} rounds with {stats.total_messages} messages.",
        )

    def trigger_node_addition(
        self,
        new_as_id: int,
        peer_as_ids: List[int],
        prefixes: List[str],
    ) -> EventResult:
        """Adds a newly joined AS to the network and announces its prefixes."""
        start_time = time.perf_counter()

        # 1. Add node to topology
        self.engine.topology.add_as_node(new_as_id, as_type=ASType.STUB, prefixes=prefixes)
        from ..routing.router import Router
        new_router = Router(as_id=new_as_id)
        for p in prefixes:
            new_router.add_originated_prefix(p)
        self.engine.routers[new_as_id] = new_router

        # 2. Add links to peers
        initial_messages: List[RouteMessage] = []
        for peer_id in peer_as_ids:
            if peer_id in self.engine.routers:
                self.engine.topology.add_link(new_as_id, peer_id)
                new_router.add_neighbor(peer_id)
                self.engine.routers[peer_id].add_neighbor(new_as_id)

                # Peer router advertises its Loc-RIB to new router
                peer_router = self.engine.routers[peer_id]
                for prefix, route in peer_router.loc_rib.items():
                    if new_as_id not in route.as_path:
                        outbound_path = (peer_id,) + route.as_path
                        msg = RouteMessage(
                            msg_type=MessageType.UPDATE,
                            sender_as=peer_id,
                            receiver_as=new_as_id,
                            prefix=prefix,
                            as_path=outbound_path,
                            next_hop=peer_id,
                        )
                        advertised_route = Route(
                            prefix=prefix,
                            as_path=outbound_path,
                            next_hop=peer_id,
                        )
                        peer_router.adj_rib_out[new_as_id][prefix] = advertised_route
                        initial_messages.append(msg)

        # 3. New router originates its prefixes to all peers
        initial_messages.extend(new_router.originate_all_routes())

        # 4. Reconverge
        stats = self.engine.run_event_loop(initial_messages)
        duration = time.perf_counter() - start_time

        return EventResult(
            event_type="NODE_ADDITION",
            target=f"AS{new_as_id}",
            stats=stats,
            execution_time_sec=duration,
            description=f"New node AS{new_as_id} joined with {len(prefixes)} prefixes. Network converged in {stats.rounds} rounds.",
        )
