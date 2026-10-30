# Path Vector Routing Performance Analysis and Routing Table Optimization in Large-Scale Networks

[![Tests](https://img.shields.io/badge/tests-13%20passed-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

> A comprehensive discrete-event simulation and optimization framework modeling BGP-style Path Vector routing across networks from tens to thousands of Autonomous Systems (ASes).

---

## 📌 Project Overview

This project addresses the two core scalability bottlenecks of Inter-domain Path Vector routing:
1. **Problem A — Performance at Scale**: How convergence latency, message overhead, memory consumption, and path stretch evolve as networks grow from 10 to 1,000+ nodes under steady-state and dynamic link failure conditions.
2. **Problem B — Routing Table Size**: How to radically shrink routing table entries and router memory overhead without breaking reachability (100.0% preserved destination delivery).

---

## 🏆 Key Experimental Finding (at Scale $N = 1000$ ASes)

> *"In a network of **1000 nodes**, basic path vector routing produced tables of **2100.0 entries** and required **7.6641 seconds** (4 rounds, generating 623,086 update/withdrawal messages) to reconverge after a link failure. After optimization using CIDR prefix aggregation, stub default route injection, and path compression, routing tables were smaller by **62.0%** (averaging 798.4 entries) and router memory footprint was reduced by **84.6%**, while **preserving 100.0% end-to-end reachability** across all destinations."*

---

## 🏗️ Architecture & Modules

```
CnProject/
├── docs/
│   ├── problem_statement.md          # Problem Statement
│   ├── action_plan.md                # Approved Project Plan
│   ├── work_done.md                  # Comprehensive Living Progress Log
│   └── final_report.md               # Empirical Research Report with Tables & Graphs
│
├── src/
│   ├── main.py                       # Main Experiment Orchestrator CLI
│   ├── topology/                     # AS Network Topologies (Transit-Stub, Scale-Free, CIDR Allocation)
│   ├── routing/                      # BGP Path Vector Engine (RIBs, Selection, Loop Inspection)
│   ├── events/                       # Perturbation Engine (Link Failure, Link Recovery, Node Join)
│   ├── optimizer/                    # Optimizers (CIDR Aggregation, Default Route, Compression)
│   ├── metrics/                      # Metric Aggregation & Dataset Export (CSV/JSON)
│   └── reports/                      # Matplotlib 300 DPI Visualizations & Report Compiler
│
├── tests/                            # Automated Pytest Suite (13 tests, 100% pass)
├── results/                          # Generated Data & High-Res Charts
│   ├── charts/                       # 5 High-Resolution PNG Plots
│   └── data/                         # CSV & JSON Metric Datasets
├── requirements.txt
└── README.md
```

---

## 🚀 Quickstart & Usage

### 1. Installation
Ensure Python 3.10+ is installed:
```bash
pip install -r requirements.txt
```

### 2. Run Test Suite
Execute the 13 automated unit tests:
```bash
python -m pytest
```

### 3. Run Benchmark Suite Across Network Scales
Run simulation from $N = 10$ to $N = 1000$ nodes:
```bash
python src/main.py --scales 10,25,50,100,250,500,1000
```

### 4. Launch Interactive Web Dashboard
Start the connected FastAPI backend and Obsidian Utility Console:
```bash
python -m uvicorn src.server:app --host 127.0.0.1 --port 8000
```
Open **`http://127.0.0.1:8000`** in your browser to interact with:
- Multi-scale BGP network selector ($N = 10 \to 1000$)
- Live Loc-RIB forwarding table with real-time prefix search and filtering
- Interactive Link Failure and Reconvergence churn simulations
- Live Hybrid Optimization toggles (CIDR supernet summarization, default routing, and path pruning)
- Longest-Prefix Match (LPM) hop-by-hop packet tracer
- 300 DPI analytical visualization viewer
- Research benchmark report reader


---

## 📊 Analytical Charts Generated

All charts are saved in `results/charts/`:
1. `routing_table_size_scaling.png`: Baseline vs Optimized Table Size
2. `convergence_scaling.png`: Convergence Latency & Simulation Rounds
3. `message_overhead_scaling.png`: UPDATE vs WITHDRAWAL Control Message Churn
4. `memory_consumption_scaling.png`: Total Router Memory Footprint (MB)
5. `strategy_reduction_comparison.png`: Table Reduction Gains across Optimization Strategies

---

## 📑 Detailed Documentation
- [Approved Action Plan](docs/action_plan.md)
- [Complete Work Done & Progress Log](docs/work_done.md)
- [Comprehensive Final Research Report](docs/final_report.md)
