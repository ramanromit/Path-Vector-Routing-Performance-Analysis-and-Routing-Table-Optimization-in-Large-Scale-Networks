"""FastAPI Backend Server connecting Dashboard Frontend to Path Vector Routing Simulation.

Provides high-performance REST APIs:
- GET  /api/scales           : Empirical benchmark data across 7 network scales
- GET  /api/routes           : Live Loc-RIB forwarding table routes from simulation
- POST /api/simulate/run     : Runs discrete-event BGP convergence
- POST /api/simulate/failure : Triggers link failure and measures reconvergence churn
- POST /api/simulate/recovery: Restores failed link and updates shortest paths
- POST /api/optimize         : Executes CIDR Aggregation, Default Route, or Hybrid optimization
- POST /api/trace            : Real Longest-Prefix-Match hop-by-hop packet forwarding simulation
- GET  /api/charts           : List of 300 DPI analytical visualization charts
- GET  /api/report           : Markdown research report content
"""

import json
import os
import sys
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.topology.generator import ASType, NetworkTopology, generate_scale_free_topology
from src.topology.prefix_allocator import PrefixAllocator
from src.routing.engine import ConvergenceStats, PathVectorEngine
from src.events.simulator import NetworkEventSimulator
from src.optimizer.engine import OptimizationStrategy, RoutingOptimizerSuite

app = FastAPI(
    title="Obsidian Path Vector Telemetry Server",
    description="Backend API powering the Obsidian Utility Console dashboard for Path Vector Routing",
    version="1.0.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cached state for fast interactivity
ACTIVE_STATE = {
    "scale": 25,
    "topology": None,
    "allocator": None,
    "engine": None,
    "optimizer": None,
    "is_optimized": True,
    "current_strategy": OptimizationStrategy.HYBRID,
    "failed_link": None,
}

METRICS_CACHE = {}


def load_metrics_cache():
    """Loads pre-computed empirical benchmark metrics from results/data/metrics.json."""
    metrics_path = os.path.join(PROJECT_ROOT, "results", "data", "metrics.json")
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                METRICS_CACHE["scale_measurements"] = {
                    m["num_nodes"]: m for m in data.get("scale_measurements", [])
                }
                METRICS_CACHE["comparison_records"] = data.get("comparison_records", [])
        except Exception as e:
            print(f"Warning: Could not read metrics.json: {e}")


ENGINE_CACHE = {}


def get_or_create_engine(num_nodes: int = 25):
    """Retrieves or creates a PathVectorEngine instance for given scale with multi-scale caching."""
    if num_nodes in ENGINE_CACHE:
        cached = ENGINE_CACHE[num_nodes]
        ACTIVE_STATE["scale"] = num_nodes
        ACTIVE_STATE["topology"] = cached["topology"]
        ACTIVE_STATE["allocator"] = cached["allocator"]
        ACTIVE_STATE["engine"] = cached["engine"]
        ACTIVE_STATE["optimizer"] = cached["optimizer"]
        ACTIVE_STATE["failed_link"] = cached.get("failed_link", None)
        return cached["engine"], cached["optimizer"]

    # For fast interactive responsiveness, instantiate target scale
    print(f"[SERVER] Initializing Path Vector engine for N={num_nodes} nodes...")
    init_start = time.perf_counter()

    topo = generate_scale_free_topology(num_nodes=num_nodes, m_attachments=2, seed=42)
    allocator = PrefixAllocator()
    allocator.allocate(topo, hierarchical=True)

    engine = PathVectorEngine(topo)
    engine.run_initial_convergence(max_rounds=50)

    optimizer = RoutingOptimizerSuite(engine)
    if ACTIVE_STATE["is_optimized"]:
        optimizer.apply_optimization(ACTIVE_STATE["current_strategy"])

    cached_entry = {
        "topology": topo,
        "allocator": allocator,
        "engine": engine,
        "optimizer": optimizer,
        "failed_link": None,
    }
    ENGINE_CACHE[num_nodes] = cached_entry

    ACTIVE_STATE["scale"] = num_nodes
    ACTIVE_STATE["topology"] = topo
    ACTIVE_STATE["allocator"] = allocator
    ACTIVE_STATE["engine"] = engine
    ACTIVE_STATE["optimizer"] = optimizer
    ACTIVE_STATE["failed_link"] = None

    init_elapsed = time.perf_counter() - init_start
    print(f"[SERVER] Engine ready for N={num_nodes} in {init_elapsed:.3f}s")

    return engine, optimizer


# Initialize caches
load_metrics_cache()
# Pre-initialize interactive scales (10, 25, 50) for instantaneous switching
for s in [10, 25, 50]:
    try:
        get_or_create_engine(s)
    except Exception as e:
        print(f"[SERVER] Warning: Engine pre-init for N={s} failed: {e}")

# Default active state is scale 25
if 25 in ENGINE_CACHE:
    get_or_create_engine(25)


# ==============================================================================
# REST API Endpoints
# ==============================================================================

@app.get("/api/status")
def get_system_status():
    """Returns general backend system status and active simulation state."""
    return {
        "status": "OPERATIONAL",
        "protocol": "BGP-4 Path Vector",
        "active_scale": ACTIVE_STATE["scale"],
        "is_optimized": ACTIVE_STATE["is_optimized"],
        "strategy": ACTIVE_STATE["current_strategy"].value if ACTIVE_STATE["is_optimized"] else "None (Raw)",
        "failed_link": ACTIVE_STATE["failed_link"],
        "total_nodes_in_mesh": ACTIVE_STATE["topology"].num_nodes if ACTIVE_STATE["topology"] else 0,
        "total_links_in_mesh": ACTIVE_STATE["topology"].num_edges if ACTIVE_STATE["topology"] else 0,
    }


@app.get("/api/scales")
def get_scales_benchmark():
    """Returns empirical benchmark metrics across all network scales (10 to 1000 ASes)."""
    if "scale_measurements" not in METRICS_CACHE:
        load_metrics_cache()

    return {
        "scales": list(METRICS_CACHE.get("scale_measurements", {}).values()),
        "comparisons": METRICS_CACHE.get("comparison_records", []),
    }


@app.get("/api/routes")
def get_routing_table(
    scale: int = Query(default=100, ge=10, le=1000),
    as_id: int = Query(default=1, ge=1),
    filter_type: str = Query(default="all"),
    search: Optional[str] = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
):
    """Returns paginated Loc-RIB forwarding table routes for a given AS node."""
    engine, optimizer = get_or_create_engine(scale)
    router = engine.routers.get(as_id)
    if not router:
        as_id = 1
        router = engine.routers.get(1)

    # Determine which table to read (Optimized or Raw Loc-RIB)
    if ACTIVE_STATE["is_optimized"] and as_id in optimizer.optimized_tables:
        table_dict = optimizer.optimized_tables[as_id]
    else:
        table_dict = router.loc_rib

    routes_list = []
    for prefix_str, r in table_dict.items():
        is_default = prefix_str == "0.0.0.0/0"
        is_supernet = "/22" in prefix_str or "/23" in prefix_str

        # Determine type label
        if is_default:
            pfx_type = "Default Route"
        elif is_supernet:
            pfx_type = "CIDR Supernet"
        elif r.origin_as <= 5:
            pfx_type = "Tier-1 Core"
        elif r.origin_as > (scale * 0.6):
            pfx_type = "Stub Prefix"
        else:
            pfx_type = "Transit Prefix"

        # Apply category filter
        if filter_type == "core" and "Core" not in pfx_type:
            continue
        if filter_type == "stubs" and "Stub" not in pfx_type and not is_default:
            continue
        if filter_type == "aggregated" and not is_supernet and not is_default:
            continue

        # Apply search query
        if search:
            q = search.lower()
            path_str = " ".join(f"AS{a}" for a in r.as_path).lower()
            if q not in prefix_str.lower() and q not in f"as{r.next_hop}" and q not in path_str:
                continue

        routes_list.append({
            "prefix": prefix_str,
            "type": pfx_type,
            "next_hop": f"AS{r.next_hop}" if r.next_hop != router.as_id else "Self (Direct)",
            "as_path": [f"AS{a}" for a in r.as_path] if r.as_path else [f"AS{router.as_id}"],
            "hops": len(r.as_path),
            "state": "ACTIVE (LPM)" if is_default else "INSTALLED",
            "origin_as": r.origin_as,
        })

    # Sort: default route first, then by prefix
    routes_list.sort(key=lambda item: (0 if item["prefix"] == "0.0.0.0/0" else 1, item["prefix"]))

    total_count = len(routes_list)
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    start_idx = (page - 1) * page_size
    paged_rows = routes_list[start_idx : start_idx + page_size]

    return {
        "as_id": as_id,
        "scale": scale,
        "is_optimized": ACTIVE_STATE["is_optimized"],
        "peer_count": len(router.neighbors),
        "table_size": len(table_dict),
        "total_routes": total_count,
        "page": page,
        "total_pages": total_pages,
        "page_size": page_size,
        "routes": paged_rows,
    }


class RunSimulationRequest(BaseModel):
    scale: int = 100


@app.post("/api/simulate/run")
def trigger_convergence_run(req: RunSimulationRequest):
    """Executes a full discrete-event simulation run for the requested scale."""
    start_time = time.perf_counter()
    engine, optimizer = get_or_create_engine(req.scale)

    # Trigger re-origination
    stats = engine.run_initial_convergence(max_rounds=50)
    duration = time.perf_counter() - start_time

    return {
        "status": "CONVERGED",
        "scale": req.scale,
        "rounds": stats.rounds,
        "execution_time_sec": duration,
        "total_messages": stats.total_messages,
        "update_messages": stats.update_messages,
        "withdrawal_messages": stats.withdrawal_messages,
        "avg_table_size": stats.avg_table_size,
        "reachability_pct": stats.reachability_ratio * 100.0,
        "avg_path_length": stats.avg_path_length,
        "messages_per_round": stats.messages_per_round,
    }


class LinkFailureRequest(BaseModel):
    as_u: int = 1
    as_v: int = 2


@app.post("/api/simulate/failure")
def trigger_link_failure(req: LinkFailureRequest):
    """Simulates dropping a peering link and measuring BGP reconvergence churn."""
    engine = ACTIVE_STATE["engine"]
    if not engine:
        engine, _ = get_or_create_engine(100)

    # Check if edge exists
    u, v = req.as_u, req.as_v
    if not engine.topology.graph.has_edge(u, v):
        # Pick first available edge connected to u
        neighbors = engine.topology.get_neighbors(u)
        if neighbors:
            v = neighbors[0]
        else:
            edges = list(engine.topology.graph.edges())
            u, v = edges[0]

    sim = NetworkEventSimulator(engine)
    result = sim.trigger_link_failure(u, v)
    ACTIVE_STATE["failed_link"] = (u, v)

    # Re-apply optimization if enabled
    if ACTIVE_STATE["is_optimized"] and ACTIVE_STATE["optimizer"]:
        ACTIVE_STATE["optimizer"].apply_optimization(ACTIVE_STATE["current_strategy"])

    post_reachability = engine.evaluate_reachability() * 100.0

    return {
        "event": "LINK_FAILURE",
        "failed_edge": f"AS{u} <-> AS{v}",
        "reconvergence_rounds": result.stats.rounds,
        "churn_messages": result.stats.total_messages,
        "execution_time_sec": result.execution_time_sec,
        "post_reachability_pct": post_reachability,
        "description": result.description,
    }


@app.post("/api/simulate/recovery")
def trigger_link_recovery():
    """Restores the failed peering link and propagates optimal alternate routes."""
    if not ACTIVE_STATE["failed_link"]:
        return {"status": "NO_FAILED_LINK", "message": "No active link failure to restore."}

    engine = ACTIVE_STATE["engine"]
    u, v = ACTIVE_STATE["failed_link"]

    sim = NetworkEventSimulator(engine)
    result = sim.trigger_link_recovery(u, v)
    ACTIVE_STATE["failed_link"] = None

    if ACTIVE_STATE["is_optimized"] and ACTIVE_STATE["optimizer"]:
        ACTIVE_STATE["optimizer"].apply_optimization(ACTIVE_STATE["current_strategy"])

    return {
        "event": "LINK_RECOVERY",
        "restored_edge": f"AS{u} <-> AS{v}",
        "reconvergence_rounds": result.stats.rounds,
        "total_messages": result.stats.total_messages,
        "execution_time_sec": result.execution_time_sec,
        "post_reachability_pct": engine.evaluate_reachability() * 100.0,
    }


class OptimizationRequest(BaseModel):
    strategy: str = "HYBRID"  # "HYBRID", "PREFIX_AGGREGATION", "DEFAULT_ROUTE", "PATH_COMPRESSION"
    enabled: bool = True


@app.post("/api/optimize")
def apply_table_optimization(req: OptimizationRequest):
    """Executes routing table optimization and verifies 100% reachability invariant."""
    ACTIVE_STATE["is_optimized"] = req.enabled
    engine = ACTIVE_STATE["engine"]
    if not engine:
        engine, _ = get_or_create_engine(100)

    strategy_map = {
        "HYBRID": OptimizationStrategy.HYBRID,
        "PREFIX_AGGREGATION": OptimizationStrategy.PREFIX_AGGREGATION,
        "DEFAULT_ROUTE": OptimizationStrategy.DEFAULT_ROUTE,
        "PATH_COMPRESSION": OptimizationStrategy.PATH_COMPRESSION,
    }
    strat = strategy_map.get(req.strategy.upper(), OptimizationStrategy.HYBRID)
    ACTIVE_STATE["current_strategy"] = strat

    optimizer = RoutingOptimizerSuite(engine)
    ACTIVE_STATE["optimizer"] = optimizer

    if req.enabled:
        comp_record = optimizer.apply_optimization(strat)
        return {
            "is_optimized": True,
            "strategy": strat.value,
            "baseline_table_size": comp_record.baseline_table_size,
            "optimized_table_size": comp_record.optimized_table_size,
            "table_reduction_pct": comp_record.table_size_reduction_pct,
            "memory_savings_pct": comp_record.memory_savings_pct,
            "reachability_preserved_pct": comp_record.optimized_reachability_pct,
        }
    else:
        sizes = [r.table_size for r in engine.routers.values()]
        import numpy as np
        return {
            "is_optimized": False,
            "strategy": "Unoptimized (Full BGP Loc-RIB)",
            "baseline_table_size": float(np.mean(sizes)),
            "optimized_table_size": float(np.mean(sizes)),
            "table_reduction_pct": 0.0,
            "memory_savings_pct": 0.0,
            "reachability_preserved_pct": engine.evaluate_reachability() * 100.0,
        }


class PacketTraceRequest(BaseModel):
    src_as: int = 1
    dest_prefix: str = "10.0.1.0/24"


@app.post("/api/trace")
def trace_packet_forwarding(req: PacketTraceRequest):
    """Simulates hop-by-hop packet forwarding using Longest-Prefix Matching."""
    engine = ACTIVE_STATE["engine"]
    optimizer = ACTIVE_STATE["optimizer"]
    if not engine or not optimizer:
        engine, optimizer = get_or_create_engine(100)

    # Find origin AS for prefix
    true_origin_as = None
    for r in engine.routers.values():
        if req.dest_prefix in r.originated_prefixes:
            true_origin_as = r.as_id
            break

    # If exact prefix not found, check supernet origin
    if true_origin_as is None:
        import ipaddress
        target_net = ipaddress.IPv4Network(req.dest_prefix, strict=False)
        for r in engine.routers.values():
            for p in r.originated_prefixes:
                if ipaddress.IPv4Network(p).supernet_of(target_net) or ipaddress.IPv4Network(p) == target_net:
                    true_origin_as = r.as_id
                    break
            if true_origin_as:
                break

    if true_origin_as is None:
        true_origin_as = 2  # default fallback

    hops = []
    current_as = req.src_as
    visited = set()
    delivered = False

    for step in range(25):
        visited.add(current_as)
        route = optimizer.longest_prefix_match(current_as, req.dest_prefix)
        if not route:
            hops.append({"as_id": current_as, "action": "DROPPED", "note": "No route to host"})
            break

        hops.append({
            "step": step + 1,
            "current_as": f"AS{current_as}",
            "matched_route": route.prefix,
            "next_hop": f"AS{route.next_hop}",
            "path_vector": [f"AS{a}" for a in route.as_path],
        })

        if route.next_hop == current_as or route.next_hop == true_origin_as:
            delivered = True
            break

        if route.next_hop in visited:
            hops.append({"as_id": route.next_hop, "action": "LOOP_DETECTED"})
            break

        current_as = route.next_hop

    return {
        "src_as": f"AS{req.src_as}",
        "dest_prefix": req.dest_prefix,
        "true_origin_as": f"AS{true_origin_as}",
        "delivered": delivered,
        "total_hops": len(hops),
        "trace_steps": hops,
    }


@app.get("/api/topology")
def get_topology_graph(scale: int = 25):
    """Returns nodes and edges for the live interactive topology visualization."""
    engine, optimizer = get_or_create_engine(scale)
    topo = engine.topology

    nodes = []
    for as_id in sorted(topo.nodes.keys()):
        node = topo.get_node(as_id)
        router = engine.routers.get(as_id)
        is_core = as_id <= 3 or (node and node.as_type == ASType.CORE)
        is_stub = node and node.as_type == ASType.STUB

        primary_prefix = f"10.0.{as_id}.0/24"
        if node and node.prefixes:
            primary_prefix = node.prefixes[0]
        elif router and router.originated_prefixes:
            primary_prefix = sorted(list(router.originated_prefixes))[0]

        nodes.append({
            "id": as_id,
            "label": f"AS-{as_id}",
            "tier": "Core" if is_core else ("Stub" if is_stub else "Transit"),
            "prefix": primary_prefix,
            "peer_count": len(router.neighbors) if router else (len(node.neighbors) if node else 0),
            "table_size": len(optimizer.optimized_tables.get(as_id, router.loc_rib if router else {})) if ACTIVE_STATE["is_optimized"] else (router.table_size if router else 0),
        })

    edges = []
    failed_edge = ACTIVE_STATE.get("failed_link")
    for u, v in topo.graph.edges():
        is_failed = False
        if failed_edge:
            fu, fv = failed_edge
            if (u == fu and v == fv) or (u == fv and v == fu):
                is_failed = True

        edges.append({
            "source": u,
            "target": v,
            "failed": is_failed,
        })

    return {
        "scale": scale,
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
        "failed_link": failed_edge,
    }


@app.get("/api/charts")
def get_chart_list():
    """Returns available analytical chart image URLs and metadata."""
    charts_dir = os.path.join(PROJECT_ROOT, "results", "charts")
    if not os.path.exists(charts_dir):
        return {"charts": []}

    chart_files = [
        {
            "id": "table-scaling",
            "title": "Routing Table Size vs Network Scale",
            "filename": "routing_table_size_scaling.png",
            "url": "/charts/routing_table_size_scaling.png",
            "caption": "Comparison of Baseline BGP growth vs. Hybrid Optimized compression.",
        },
        {
            "id": "convergence-scaling",
            "title": "Convergence Rounds & Latency",
            "filename": "convergence_scaling.png",
            "url": "/charts/convergence_scaling.png",
            "caption": "Discrete simulation rounds and execution latency up to 1,000 ASes.",
        },
        {
            "id": "message-overhead",
            "title": "Control Message Overhead",
            "filename": "message_overhead_scaling.png",
            "url": "/charts/message_overhead_scaling.png",
            "caption": "UPDATE vs WITHDRAWAL message overhead during network convergence.",
        },
        {
            "id": "memory-scaling",
            "title": "Router Memory Footprint (MB)",
            "filename": "memory_consumption_scaling.png",
            "url": "/charts/memory_consumption_scaling.png",
            "caption": "Total router memory consumed by BGP tables across all network routers.",
        },
        {
            "id": "strategy-comparison",
            "title": "Table Reduction by Strategy",
            "filename": "strategy_reduction_comparison.png",
            "url": "/charts/strategy_reduction_comparison.png",
            "caption": "Comparative reduction percentages delivered across optimization techniques.",
        },
    ]
    return {"charts": chart_files}


@app.get("/api/report")
def get_research_report():
    """Returns the markdown final report content."""
    report_file = os.path.join(PROJECT_ROOT, "docs", "final_report.md")
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()
        return {"report_markdown": content}
    return {"report_markdown": "# Report not found"}


@app.get("/api/prefixes")
def get_originated_prefixes(scale: int = Query(default=25, ge=10, le=1000)):
    """Returns all originated prefixes in the active engine for LPM trace dropdown."""
    engine, _ = get_or_create_engine(scale)
    prefixes = []
    for r in engine.routers.values():
        for p in sorted(r.originated_prefixes):
            prefixes.append({"prefix": p, "origin_as": r.as_id})
    prefixes.sort(key=lambda x: x["prefix"])
    return {"scale": scale, "prefixes": prefixes}


# Serve static charts
charts_path = os.path.join(PROJECT_ROOT, "results", "charts")
if os.path.exists(charts_path):
    app.mount("/charts", StaticFiles(directory=charts_path), name="charts")

# Serve dashboard application
dashboard_path = os.path.join(PROJECT_ROOT, "dashboard")
if os.path.exists(dashboard_path):
    app.mount("/", StaticFiles(directory=dashboard_path, html=True), name="dashboard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=8080, reload=False)
