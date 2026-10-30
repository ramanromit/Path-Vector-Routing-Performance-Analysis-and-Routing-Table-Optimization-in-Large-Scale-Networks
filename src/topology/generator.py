"""Network Topology Generator for Path Vector Routing Simulation.

Generates realistic Autonomous System (AS) topologies using:
1. Scale-Free (Barabási–Albert) preferential attachment model (mimicking Internet AS graph)
2. Random (Erdős–Rényi) model for baseline comparisons
3. Hierarchical classification into Tier-1 (Core), Tier-2 (Transit), and Stub (Leaf) ASes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx
import numpy as np


class ASType(Enum):
    """Classification of Autonomous Systems by structural role in topology."""
    CORE = "Tier-1 (Core)"
    TRANSIT = "Tier-2 (Transit)"
    STUB = "Stub (Leaf)"


@dataclass
class ASNode:
    """Represents an Autonomous System node in the network."""
    as_id: int
    as_type: ASType = ASType.STUB
    prefixes: List[str] = field(default_factory=list)
    neighbors: Set[int] = field(default_factory=set)

    @property
    def is_stub(self) -> bool:
        return self.as_type == ASType.STUB


class NetworkTopology:
    """Encapsulates the graph topology, AS classifications, and graph operations."""

    def __init__(self, name: str = "AS-Topology"):
        self.name = name
        self.graph: nx.Graph = nx.Graph()
        self.nodes: Dict[int, ASNode] = {}

    @property
    def num_nodes(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def num_edges(self) -> int:
        return self.graph.number_of_edges()

    def get_node(self, as_id: int) -> Optional[ASNode]:
        return self.nodes.get(as_id)

    def get_neighbors(self, as_id: int) -> List[int]:
        if as_id in self.graph:
            return list(self.graph.neighbors(as_id))
        return []

    def add_as_node(self, as_id: int, as_type: ASType = ASType.STUB, prefixes: Optional[List[str]] = None) -> ASNode:
        """Adds or updates an AS node in the topology."""
        if prefixes is None:
            prefixes = []
        if as_id not in self.nodes:
            node = ASNode(as_id=as_id, as_type=as_type, prefixes=prefixes)
            self.nodes[as_id] = node
            self.graph.add_node(as_id, data=node)
        else:
            node = self.nodes[as_id]
            node.as_type = as_type
            if prefixes:
                node.prefixes = prefixes
        return node

    def add_link(self, as_u: int, as_v: int) -> None:
        """Adds a bidirectional peering/transit link between two ASes."""
        if as_u not in self.nodes:
            self.add_as_node(as_u)
        if as_v not in self.nodes:
            self.add_as_node(as_v)

        self.graph.add_edge(as_u, as_v)
        self.nodes[as_u].neighbors.add(as_v)
        self.nodes[as_v].neighbors.add(as_u)

    def remove_link(self, as_u: int, as_v: int) -> bool:
        """Removes a link between two ASes (simulates link failure)."""
        if self.graph.has_edge(as_u, as_v):
            self.graph.remove_edge(as_u, as_v)
            self.nodes[as_u].neighbors.discard(as_v)
            self.nodes[as_v].neighbors.discard(as_u)
            return True
        return False

    def remove_as_node(self, as_id: int) -> bool:
        """Removes an AS node and all attached links (simulates AS crash/withdrawal)."""
        if as_id in self.nodes:
            for neighbor in list(self.nodes[as_id].neighbors):
                self.nodes[neighbor].neighbors.discard(as_id)
            del self.nodes[as_id]
            self.graph.remove_node(as_id)
            return True
        return False

    def is_connected(self) -> bool:
        """Checks if the topology is fully connected."""
        if self.num_nodes == 0:
            return True
        return nx.is_connected(self.graph)

    def ensure_connected(self) -> None:
        """Connects disconnected components to the largest component via the highest-degree core node."""
        if self.num_nodes <= 1 or nx.is_connected(self.graph):
            return

        components = list(nx.connected_components(self.graph))
        components.sort(key=len, reverse=True)
        primary = components[0]
        primary_hub = max(primary, key=lambda n: self.graph.degree[n])

        for comp in components[1:]:
            comp_hub = max(comp, key=lambda n: self.graph.degree[n])
            self.add_link(primary_hub, comp_hub)

    def classify_tiers(self) -> None:
        """Classifies nodes into Tier-1 (Core), Tier-2 (Transit), and Stub (Leaf)

        Based on degree centrality and structural connectivity:
        - Core (Tier-1): Top 5% by degree or degree >= 8
        - Stub (Leaf): Degree <= 2
        - Transit (Tier-2): Intermediate nodes
        """
        if self.num_nodes == 0:
            return

        degrees = dict(self.graph.degree())
        sorted_nodes = sorted(degrees.keys(), key=lambda n: degrees[n], reverse=True)

        core_cutoff_idx = max(1, int(len(sorted_nodes) * 0.05))
        core_nodes = set(sorted_nodes[:core_cutoff_idx])

        for node_id, node in self.nodes.items():
            deg = degrees.get(node_id, 0)
            if node_id in core_nodes or deg >= 10:
                node.as_type = ASType.CORE
            elif deg <= 2:
                node.as_type = ASType.STUB
            else:
                node.as_type = ASType.TRANSIT

    def get_summary(self) -> Dict:
        """Returns structural statistics of the network."""
        degrees = [d for _, d in self.graph.degree()]
        tier_counts = {t.value: 0 for t in ASType}
        for n in self.nodes.values():
            tier_counts[n.as_type.value] += 1

        is_conn = self.is_connected()
        diameter = nx.diameter(self.graph) if is_conn and self.num_nodes > 1 else None

        return {
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "is_connected": is_conn,
            "avg_degree": float(np.mean(degrees)) if degrees else 0.0,
            "max_degree": int(np.max(degrees)) if degrees else 0,
            "diameter": diameter,
            "tier_distribution": tier_counts,
        }


def generate_scale_free_topology(
    num_nodes: int,
    m_attachments: int = 2,
    seed: int = 42,
    stub_ratio: float = 0.4,
) -> NetworkTopology:
    """Generates a realistic Internet AS topology using the Transit-Stub model.

    The Internet topology consists of:
    1. A meshed core and transit tier (generated via Barabási–Albert scale-free preferential attachment, m >= 2)
       providing redundant paths, multi-path routing, and alternative routes for failure recovery.
    2. Customer stub ASes connected to 1 or 2 transit providers (mirroring single-homed enterprise networks
       and dual-homed regional stubs).

    Args:
        num_nodes: Total number of ASes to generate.
        m_attachments: Edges to attach in the core/transit network.
        seed: Random seed for deterministic reproducibility.
        stub_ratio: Fraction of nodes that are leaf customer stubs (default 40%).

    Returns:
        A fully-connected NetworkTopology instance.
    """
    import random
    rng = random.Random(seed)

    if num_nodes <= 10:
        # For small graphs, standard scale-free
        g = nx.barabasi_albert_graph(n=num_nodes, m=min(2, num_nodes - 1), seed=seed)
    else:
        # Transit-Stub architecture
        num_stubs = max(1, int(num_nodes * stub_ratio))
        num_core = num_nodes - num_stubs

        # Core & transit mesh
        g = nx.barabasi_albert_graph(n=num_core, m=max(2, m_attachments), seed=seed)

        # Attach customer stubs to core/transit nodes with preferential attachment
        core_nodes = list(g.nodes())
        degrees = [g.degree(n) for n in core_nodes]
        total_deg = sum(degrees)
        prob = [d / total_deg for d in degrees]

        for stub_idx in range(num_core, num_nodes):
            g.add_node(stub_idx)
            # 60% single-homed stub (1 provider), 40% dual-homed stub (2 providers)
            num_providers = 1 if rng.random() < 0.6 else 2
            chosen_providers = rng.choices(core_nodes, weights=prob, k=num_providers)
            for p in set(chosen_providers):
                g.add_edge(stub_idx, p)

    topo = NetworkTopology(name=f"TransitStub_N{num_nodes}")

    # Relabel nodes from 1 to num_nodes (1-indexed AS numbers)
    mapping = {old: old + 1 for old in g.nodes()}
    g = nx.relabel_nodes(g, mapping)

    for node_id in g.nodes():
        topo.add_as_node(node_id)

    for u, v in g.edges():
        topo.add_link(u, v)

    topo.ensure_connected()
    topo.classify_tiers()
    return topo


def generate_random_topology(num_nodes: int, p: float = 0.05, seed: int = 42) -> NetworkTopology:
    """Generates an Erdős–Rényi random network topology for baseline benchmarking.

    Args:
        num_nodes: Total number of ASes.
        p: Probability for edge creation.
        seed: Random seed.

    Returns:
        A connected NetworkTopology instance.
    """
    g = nx.erdos_renyi_graph(n=num_nodes, p=p, seed=seed)
    topo = NetworkTopology(name=f"Random_N{num_nodes}")

    mapping = {old: old + 1 for old in g.nodes()}
    g = nx.relabel_nodes(g, mapping)

    for node_id in g.nodes():
        topo.add_as_node(node_id)

    for u, v in g.edges():
        topo.add_link(u, v)

    topo.ensure_connected()
    topo.classify_tiers()
    return topo
