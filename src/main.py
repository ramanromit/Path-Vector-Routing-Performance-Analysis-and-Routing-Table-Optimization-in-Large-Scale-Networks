"""Main Experiment Driver and Benchmarking Orchestrator.

Executes comprehensive performance analysis and routing table optimization experiments
across multiple network scales (10 to 1000+ nodes), matching the problem statement requirements.
"""

import argparse
import os
import sys
import time
from typing import List

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.topology.generator import ASType, generate_scale_free_topology
from src.topology.prefix_allocator import PrefixAllocator
from src.routing.engine import PathVectorEngine
from src.events.simulator import NetworkEventSimulator
from src.optimizer.engine import OptimizationStrategy, RoutingOptimizerSuite
from src.metrics.collector import (
    MetricsCollector,
    NetworkScaleMeasurement,
    OptimizationComparisonRecord,
)
from src.reports.visualizer import ReportVisualizer
from src.reports.report_generator import ResearchReportGenerator


# Configure UTF-8 encoding for Windows console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_experiment_pipeline(
    scales: List[int],
    seed: int = 42,
    output_dir: str = "results",
    report_path: str = "docs/final_report.md",
) -> None:
    """Executes the complete experimental benchmarking pipeline."""
    print("=" * 78)
    print("[*] PATH VECTOR ROUTING PERFORMANCE ANALYSIS & OPTIMIZATION BENCHMARK")
    print("=" * 78)
    print(f"Network Scales to evaluate: {scales}")
    print(f"Random seed: {seed}")
    print(f"Output directory: {output_dir}")
    print(f"Report target: {report_path}")
    print("-" * 78)

    collector = MetricsCollector()

    for idx, num_nodes in enumerate(scales, 1):
        print(f"\n[{idx}/{len(scales)}] [*] Evaluating Network Scale N = {num_nodes} Autonomous Systems...")

        # 1. Topology Generation
        topo_start = time.perf_counter()
        topo = generate_scale_free_topology(num_nodes=num_nodes, m_attachments=2, seed=seed)
        allocator = PrefixAllocator()
        allocator.allocate(topo, hierarchical=True)
        topo_time = time.perf_counter() - topo_start
        print(f"   [+] Topology generated: {topo.num_nodes} ASes, {topo.num_edges} links, {allocator.total_prefixes} prefixes ({topo_time:.3f}s)")

        # 2. Path Vector Routing Simulation (Initial Convergence)
        engine = PathVectorEngine(topo)
        sim_start = time.perf_counter()
        init_stats = engine.run_initial_convergence(max_rounds=500)
        sim_time = time.perf_counter() - sim_start

        print(f"   [+] Baseline convergence: {init_stats.rounds} rounds, {init_stats.total_messages} messages, {sim_time:.3f}s")
        print(f"   [+] Raw table size: {init_stats.avg_table_size:.1f} avg entries/router, Memory: {init_stats.total_memory_bytes / (1024*1024):.2f} MB")
        print(f"   [+] Reachability: {init_stats.reachability_ratio * 100:.1f}%, Avg Path: {init_stats.avg_path_length:.2f} hops")

        # 3. Dynamic Perturbation: Link Failure & Reconvergence Churn
        # Find a suitable transit link to fail
        edges = list(topo.graph.edges())
        # Pick an edge connected to a core/transit node if possible
        failed_edge = edges[0]
        for u, v in edges:
            if topo.nodes[u].as_type != ASType.STUB or topo.nodes[v].as_type != ASType.STUB:
                failed_edge = (u, v)
                break

        event_sim = NetworkEventSimulator(engine)
        fail_result = event_sim.trigger_link_failure(failed_edge[0], failed_edge[1])
        post_reachability = engine.evaluate_reachability() * 100.0

        print(f"   [+] Link failure (AS{failed_edge[0]} <-> AS{failed_edge[1]}): reconverged in {fail_result.stats.rounds} rounds, {fail_result.stats.total_messages} messages ({fail_result.execution_time_sec:.3f}s)")

        # Record baseline scale measurement
        scale_record = NetworkScaleMeasurement(
            num_nodes=num_nodes,
            num_edges=topo.num_edges,
            total_prefixes=allocator.total_prefixes,
            topology_type="ScaleFree_BA",
            convergence_rounds=init_stats.rounds,
            convergence_time_sec=sim_time,
            total_messages=init_stats.total_messages,
            update_messages=init_stats.update_messages,
            withdrawal_messages=init_stats.withdrawal_messages,
            avg_table_size=init_stats.avg_table_size,
            max_table_size=init_stats.max_table_size,
            total_table_entries=init_stats.total_table_entries,
            avg_memory_kb=(init_stats.total_memory_bytes / num_nodes) / 1024.0,
            total_memory_mb=init_stats.total_memory_bytes / (1024.0 * 1024.0),
            avg_path_length=init_stats.avg_path_length,
            reachability_pct=init_stats.reachability_ratio * 100.0,
            failure_rounds=fail_result.stats.rounds,
            failure_messages=fail_result.stats.total_messages,
            failure_reconvergence_sec=fail_result.execution_time_sec,
            post_failure_reachability_pct=post_reachability,
        )
        collector.record_scale_measurement(scale_record)

        # 4. Routing Table Optimization Strategies
        optimizer = RoutingOptimizerSuite(engine)

        strategies = [
            OptimizationStrategy.PREFIX_AGGREGATION,
            OptimizationStrategy.DEFAULT_ROUTE,
            OptimizationStrategy.PATH_COMPRESSION,
            OptimizationStrategy.HYBRID,
        ]

        for strat in strategies:
            comp_record = optimizer.apply_optimization(strat)
            collector.record_comparison(comp_record)
            if strat == OptimizationStrategy.HYBRID:
                print(f"   [+] Hybrid Optimization: Table size reduced by {comp_record.table_size_reduction_pct:.1f}% ({comp_record.optimized_table_size:.1f} entries), Memory saved: {comp_record.memory_savings_pct:.1f}%, Reachability: {comp_record.optimized_reachability_pct:.1f}%")

    # 5. Export Data
    print("\n" + "=" * 78)
    print("[*] EXPORTING METRICS & DATASETS...")
    data_dir = os.path.join(output_dir, "data")
    collector.export_csv(data_dir)
    collector.export_json(os.path.join(data_dir, "metrics.json"))
    print(f"   [+] CSV and JSON metrics saved to: {data_dir}")

    # 6. Generate Analytical Charts
    print("\n[*] GENERATING PUBLICATION-READY VISUALIZATIONS...")
    chart_dir = os.path.join(output_dir, "charts")
    visualizer = ReportVisualizer(output_dir=chart_dir)
    df_scale = collector.to_scale_dataframe()
    df_comp = collector.to_comparison_dataframe()
    generated_charts = visualizer.generate_all_plots(df_scale, df_comp)
    for c in generated_charts:
        print(f"   [+] Chart generated: {c}")

    # 7. Generate Final Comprehensive Markdown Report
    print("\n[*] COMPILING COMPREHENSIVE FINAL RESEARCH REPORT...")
    report_gen = ResearchReportGenerator(output_path=report_path)
    final_report_file = report_gen.generate_report(df_scale, df_comp, generated_charts)
    print(f"   [+] Final Report successfully written to: {final_report_file}")

    print("\n" + "=" * 78)
    print("[DONE] EXPERIMENT BENCHMARK COMPLETED SUCCESSFULLY!")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description="Path Vector Routing Analysis & Optimization Suite")
    parser.add_argument(
        "--scales",
        type=str,
        default="10,25,50,100,200,500,1000",
        help="Comma-separated list of network scale node counts (e.g. 10,25,50,100,200,500,1000)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory to save charts and data")
    parser.add_argument("--report-path", type=str, default="docs/final_report.md", help="Path for markdown report")

    args = parser.parse_args()
    scales = [int(s.strip()) for s in args.scales.split(",") if s.strip()]

    run_experiment_pipeline(
        scales=scales,
        seed=args.seed,
        output_dir=args.output_dir,
        report_path=args.report_path,
    )


if __name__ == "__main__":
    main()
