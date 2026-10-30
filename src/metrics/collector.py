"""Metrics Collector for Path Vector Routing Performance Analysis.

Collects, aggregates, and stores empirical measurements across network scales and events:
- Routing table size (average, max, total)
- Convergence latency (simulation rounds and CPU execution time)
- Message overhead (UPDATE vs WITHDRAWAL counts)
- Memory consumption (bytes per router and network total)
- Average path length (AS hops)
- Reachability verification (ensuring 100% reachability invariant)
"""

from dataclasses import asdict, dataclass, field
import json
import os
from typing import Dict, List, Optional
import pandas as pd


@dataclass
class NetworkScaleMeasurement:
    """Measurement record for a single network scale experiment."""
    num_nodes: int
    num_edges: int
    total_prefixes: int
    topology_type: str
    convergence_rounds: int
    convergence_time_sec: float
    total_messages: int
    update_messages: int
    withdrawal_messages: int
    avg_table_size: float
    max_table_size: int
    total_table_entries: int
    avg_memory_kb: float
    total_memory_mb: float
    avg_path_length: float
    reachability_pct: float

    # Post-failure event metrics
    failure_rounds: int = 0
    failure_messages: int = 0
    failure_reconvergence_sec: float = 0.0
    post_failure_reachability_pct: float = 0.0


@dataclass
class OptimizationComparisonRecord:
    """Pairwise comparison of baseline vs optimized routing performance."""
    num_nodes: int
    strategy: str

    # Baseline (Unoptimized)
    baseline_table_size: float
    baseline_memory_mb: float
    baseline_convergence_rounds: int
    baseline_total_messages: int
    baseline_reachability_pct: float
    baseline_path_length: float

    # Optimized
    optimized_table_size: float
    optimized_memory_mb: float
    optimized_convergence_rounds: int
    optimized_total_messages: int
    optimized_reachability_pct: float
    optimized_path_length: float

    # Percentage Improvements
    table_size_reduction_pct: float = 0.0
    memory_savings_pct: float = 0.0
    message_reduction_pct: float = 0.0


class MetricsCollector:
    """Stores experiment results and provides structured data export."""

    def __init__(self):
        self.scale_measurements: List[NetworkScaleMeasurement] = []
        self.comparison_records: List[OptimizationComparisonRecord] = []

    def record_scale_measurement(self, measurement: NetworkScaleMeasurement) -> None:
        self.scale_measurements.append(measurement)

    def record_comparison(self, record: OptimizationComparisonRecord) -> None:
        # Calculate percentage gains
        if record.baseline_table_size > 0:
            record.table_size_reduction_pct = (
                (record.baseline_table_size - record.optimized_table_size)
                / record.baseline_table_size
            ) * 100.0

        if record.baseline_memory_mb > 0:
            record.memory_savings_pct = (
                (record.baseline_memory_mb - record.optimized_memory_mb)
                / record.baseline_memory_mb
            ) * 100.0

        if record.baseline_total_messages > 0:
            record.message_reduction_pct = (
                (record.baseline_total_messages - record.optimized_total_messages)
                / record.baseline_total_messages
            ) * 100.0

        self.comparison_records.append(record)

    def to_scale_dataframe(self) -> pd.DataFrame:
        """Converts scale measurements to a pandas DataFrame."""
        return pd.DataFrame([asdict(m) for m in self.scale_measurements])

    def to_comparison_dataframe(self) -> pd.DataFrame:
        """Converts comparison records to a pandas DataFrame."""
        return pd.DataFrame([asdict(c) for c in self.comparison_records])

    def export_json(self, filepath: str) -> None:
        """Exports all recorded data to a JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data = {
            "scale_measurements": [asdict(m) for m in self.scale_measurements],
            "comparison_records": [asdict(c) for c in self.comparison_records],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def export_csv(self, directory: str) -> None:
        """Exports data to CSV files."""
        os.makedirs(directory, exist_ok=True)
        df_scale = self.to_scale_dataframe()
        if not df_scale.empty:
            df_scale.to_csv(os.path.join(directory, "scale_measurements.csv"), index=False)

        df_comp = self.to_comparison_dataframe()
        if not df_comp.empty:
            df_comp.to_csv(os.path.join(directory, "optimization_comparisons.csv"), index=False)
