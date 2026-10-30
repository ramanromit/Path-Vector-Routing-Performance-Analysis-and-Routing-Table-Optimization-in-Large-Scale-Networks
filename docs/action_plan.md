# 📋 Action Plan: Path Vector Routing Performance Analysis & Routing Table Optimization

> **Project**: Path Vector Routing Performance Analysis and Routing Table Optimization in Large-Scale Networks  
> **Subject**: Computer Networks  
> **Status**: Approved & In Progress  
> **Date**: 2026-10-26

---

## 1. Project Understanding Summary

The project has **two linked goals**:

| Goal | Description |
|------|-------------|
| **A — Performance Analysis** | Simulate path vector routing (BGP-style) and measure how convergence time, message overhead, memory/CPU, and path length scale as the network grows from tens to thousands of nodes. |
| **B — Routing Table Optimization** | Apply optimization techniques (prefix aggregation, route summarization, path compression, default routes) to reduce routing table size **without breaking reachability**, then compare before vs. after metrics with graphs and tables. |

---

## 2. Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Language** | Python 3.10+ (Python 3.13 detected) | Fast graph manipulation, rich network analysis libraries, excellent profiling & plotting |
| **Graph Library** | NetworkX 3.5 | Industry-standard graph models (Barabási–Albert scale-free networks, Erdős–Rényi, Watts–Strogatz) |
| **Data & Metrics** | NumPy, Pandas | Fast aggregation of simulation metrics across nodes and time steps |
| **Visualization** | Matplotlib 3.10, Plotly | High-resolution publication-quality comparison charts and interactive topological visualizations |
| **Testing** | pytest | Robust unit & integration testing (reachability, loop prevention, route optimization invariants) |
| **Documentation** | Markdown (`docs/work_done.md`) | Continuous logging of work done, architectural decisions, and benchmark metrics |

---

## 3. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Main Simulator Orchestrator                          │
│                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  Topology        │  │  Path Vector     │  │  Metrics             │  │
│  │  Generator       │──│  Routing Engine  │──│  Collector           │  │
│  │  (Scale-Free BA, │  │  (RIB, Selection,│  │  (Convergence, Size,│  │
│  │   Prefix Alloc)  │  │   Loop Det, Incr)│  │   Messages, Memory)  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘  │
│           │                     │                       │              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  Event           │  │  Routing Table   │  │  Report & Chart      │  │
│  │  Simulator       │  │  Optimizer       │  │  Generator           │  │
│  │  (Link Fail/Rec, │  │  (Aggregation,   │  │  (Before vs After    │  │
│  │   Node Join/Drop)│  │   Compression,   │  │   Graphs & Markdown) │  │
│  │                  │  │   Default Route) │  │                      │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Detailed Module Breakdown

### Module 1: Topology Generator (`src/topology/`)
- **Synthetic Scale-Free Topology**: Barabási–Albert preferential attachment model (mimics real-world Internet AS-level topology with core transit tier-1 ASes and multi/single-homed stub ASes).
- **Erdős–Rényi Random Model**: For comparative topology benchmarking.
- **Hierarchical AS Relationships**: Core provider, transit, customer/stub classification.
- **Prefix Allocator**: Allocates contiguous and non-contiguous IPv4 prefix ranges (e.g., `/24`, `/23`, `/22`) per autonomous system to enable CIDR prefix aggregation testing.

### Module 2: Path Vector Routing Engine (`src/routing/`)
- Simplified BGP-like protocol implementation:
  - **RIB Structure**: Adj-RIB-In, Loc-RIB, and Adj-RIB-Out.
  - **Message Types**: `UPDATE` (prefix advertisement with AS-path and next-hop), `WITHDRAWAL` (unreachable prefix withdrawal), `KEEPALIVE`.
  - **Loop Prevention**: Path inspection (`if own_as in as_path -> discard`).
  - **Route Selection Decision Process**:
    1. Highest local preference (if configured)
    2. Shortest AS-Path length
    3. Deterministic tie-breaker (lowest router/AS ID)
  - **Discrete Event Queue**: Deterministic event-driven simulation loop.

### Module 3: Event Simulator (`src/events/`)
- Dynamic topology and network state modifications:
  - **Link Failure**: Drop an edge between two ASes, trigger path invalidation & withdrawal cascade.
  - **Link Recovery**: Re-establish edge and propagate alternate best paths.
  - **Node Join / Addition**: Introduce new AS with prefix and trigger propagation.
  - **Node Departure / Failure**: Drop an AS completely and re-converge.

### Module 4: Metrics Collector (`src/metrics/`)
- Precision measurement of the 6 key evaluation criteria:
  - **Routing Table Size**: Mean, median, max, and total entries across all routers.
  - **Convergence Time**: Number of simulation rounds/ticks until all queues empty and tables stabilize.
  - **Update Message Overhead**: Total volume of UPDATE and WITHDRAW messages generated.
  - **Memory Footprint**: Estimated in-memory bytes per router based on RIB entries and AS-path sequences.
  - **Average Path Length**: Mean AS-hop distance for all valid pairs.
  - **Reachability Invariant**: Matrix validation ensuring 100% reachability to all connected components.

### Module 5: Routing Table Optimizer (`src/optimizer/`)
Three concrete optimization algorithms:
1. **CIDR Prefix Aggregation**: Merges adjacent prefix blocks (e.g. `192.168.0.0/24` + `192.168.1.0/24` -> `192.168.0.0/23`) sharing identical next-hop and AS-path attributes.
2. **AS-Path Compression & Stub Path Pruning**: Compresses redundant path vectors for single-homed and transit chains where next-hop forwarding is invariant.
3. **Default Route Injection for Stub Networks**: Replaces large upstream routing tables in stub/leaf ASes with a default route (`0.0.0.0/0`) directed to the upstream provider while retaining local customer routes.

### Module 6: Report & Visualizer (`src/reports/`)
- High-resolution Matplotlib/Seaborn plots comparing:
  - Routing Table Size (Raw vs. Optimized) across scales
  - Convergence Rounds under Link Failure (Raw vs. Optimized)
  - Message Volume during Convergence
  - Average Path Length & Stretch
  - Memory Savings % vs. Scale
- Generates comprehensive markdown report with tables, graphs, and concrete numerical conclusions.

---

## 5. Development Phases

- **Phase 1: Foundation & Data Structures**
- **Phase 2: Core Path Vector Routing Engine & Discrete Simulation**
- **Phase 3: Network Events & Metrics Engine**
- **Phase 4: Routing Table Optimization Suite**
- **Phase 5: Benchmark Experiments, Visualizations & Comprehensive Report**
