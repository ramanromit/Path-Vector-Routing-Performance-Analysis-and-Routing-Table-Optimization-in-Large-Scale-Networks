"""Visualization Engine for Path Vector Routing Analysis.

Generates publication-quality charts:
1. Routing Table Size vs Network Scale (Baseline vs Hybrid Optimized)
2. Convergence Rounds and Execution Time vs Network Scale
3. Control Message Overhead (UPDATE vs WITHDRAWAL)
4. Router Memory Footprint (MB) vs Network Scale
5. Link Failure Churn & Reconvergence
6. Percentage Improvement Breakdown across Strategies
"""

import os
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class ReportVisualizer:
    """Generates analytical charts and saves them as high-resolution images."""

    def __init__(self, output_dir: str = "results/charts"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Configure clean styling
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
        plt.rcParams["font.sans-serif"] = "DejaVu Sans"
        plt.rcParams["font.size"] = 10

    def plot_table_size_comparison(self, df_scale: pd.DataFrame, df_comp: pd.DataFrame) -> str:
        """Plots Routing Table Size vs Network Scale (Baseline vs Optimized)."""
        fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)

        # Merge scale and comparison
        hybrid = df_comp[df_comp["strategy"].str.contains("Hybrid", na=False)]
        merged = pd.merge(df_scale, hybrid, on="num_nodes", how="left")

        ax.plot(
            merged["num_nodes"],
            merged["avg_table_size"],
            marker="o",
            linewidth=2.5,
            color="#d9534f",
            label="Baseline (Unoptimized BGP)",
        )
        if "optimized_table_size" in merged:
            ax.plot(
                merged["num_nodes"],
                merged["optimized_table_size"],
                marker="s",
                linewidth=2.5,
                linestyle="--",
                color="#5cb85c",
                label="Optimized (CIDR + Default + Compression)",
            )

        ax.set_title("Routing Table Size vs Network Scale (Nodes)", fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Network Scale (Total Autonomous Systems / Nodes)", fontsize=11, labelpad=8)
        ax.set_ylabel("Average Routing Table Entries per Router", fontsize=11, labelpad=8)
        ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.6)

        filepath = os.path.join(self.output_dir, "routing_table_size_scaling.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300)
        plt.close(fig)
        return filepath

    def plot_convergence_scaling(self, df_scale: pd.DataFrame) -> str:
        """Plots Convergence Rounds and Wall-Clock Latency vs Network Scale."""
        fig, ax1 = plt.subplots(figsize=(9, 5.5), dpi=300)

        color1 = "#0275d8"
        color2 = "#f0ad4e"

        ax1.plot(
            df_scale["num_nodes"],
            df_scale["convergence_rounds"],
            marker="o",
            linewidth=2.2,
            color=color1,
            label="Convergence Rounds (Ticks)",
        )
        ax1.set_xlabel("Network Scale (Autonomous Systems)", fontsize=11, labelpad=8)
        ax1.set_ylabel("Convergence Rounds", color=color1, fontsize=11, labelpad=8)
        ax1.tick_params(axis="y", labelcolor=color1)
        ax1.grid(True, linestyle=":", alpha=0.6)

        # Second axis for wall clock time
        ax2 = ax1.twinx()
        ax2.plot(
            df_scale["num_nodes"],
            df_scale["convergence_time_sec"],
            marker="^",
            linewidth=2.2,
            linestyle="--",
            color=color2,
            label="Wall-Clock Time (s)",
        )
        ax2.set_ylabel("Simulation Execution Time (seconds)", color=color2, fontsize=11, labelpad=8)
        ax2.tick_params(axis="y", labelcolor=color2)
        ax2.grid(False)

        plt.title("Convergence Latency & Rounds vs Network Scale", fontsize=13, fontweight="bold", pad=12)

        filepath = os.path.join(self.output_dir, "convergence_scaling.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300)
        plt.close(fig)
        return filepath

    def plot_message_overhead(self, df_scale: pd.DataFrame) -> str:
        """Plots Control Message Overhead (UPDATEs vs WITHDRAWALs) vs Network Scale."""
        fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)

        x = np.arange(len(df_scale))
        width = 0.35

        ax.bar(
            x - width / 2,
            df_scale["update_messages"],
            width,
            label="UPDATE Messages",
            color="#337ab7",
        )
        ax.bar(
            x + width / 2,
            df_scale["withdrawal_messages"],
            width,
            label="WITHDRAWAL Messages",
            color="#e74c3c",
        )

        ax.set_title("Routing Control Message Volume by Network Scale", fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Network Scale (Total Nodes)", fontsize=11, labelpad=8)
        ax.set_ylabel("Total Messages Exchanged", fontsize=11, labelpad=8)
        ax.set_xticks(x)
        ax.set_xticklabels(df_scale["num_nodes"])
        ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc")
        ax.grid(True, linestyle=":", alpha=0.6, axis="y")

        filepath = os.path.join(self.output_dir, "message_overhead_scaling.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300)
        plt.close(fig)
        return filepath

    def plot_memory_comparison(self, df_scale: pd.DataFrame, df_comp: pd.DataFrame) -> str:
        """Plots Router Memory Footprint (MB) vs Network Scale."""
        fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)

        hybrid = df_comp[df_comp["strategy"].str.contains("Hybrid", na=False)]
        merged = pd.merge(df_scale, hybrid, on="num_nodes", how="left")

        ax.plot(
            merged["num_nodes"],
            merged["total_memory_mb"],
            marker="o",
            linewidth=2.5,
            color="#8e44ad",
            label="Baseline Memory (MB)",
        )
        if "optimized_memory_mb" in merged:
            ax.plot(
                merged["num_nodes"],
                merged["optimized_memory_mb"],
                marker="s",
                linewidth=2.5,
                linestyle="--",
                color="#27ae60",
                label="Optimized Memory (MB)",
            )

        ax.set_title("Total Router Memory Footprint vs Network Scale", fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Network Scale (Autonomous Systems)", fontsize=11, labelpad=8)
        ax.set_ylabel("Total Network Memory (Megabytes)", fontsize=11, labelpad=8)
        ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc")
        ax.grid(True, linestyle=":", alpha=0.6)

        filepath = os.path.join(self.output_dir, "memory_consumption_scaling.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300)
        plt.close(fig)
        return filepath

    def plot_strategy_reduction_bar(self, df_comp: pd.DataFrame) -> str:
        """Plots percentage table reduction across different optimization strategies."""
        fig, ax = plt.subplots(figsize=(9, 5.2), dpi=300)

        # Average percentage reduction per strategy across all scales
        strat_summary = df_comp.groupby("strategy")["table_size_reduction_pct"].mean().reset_index()

        colors = ["#3498db", "#e67e22", "#9b59b6", "#2ecc71"]
        bars = ax.bar(
            strat_summary["strategy"],
            strat_summary["table_size_reduction_pct"],
            color=colors[:len(strat_summary)],
            edgecolor="#333333",
            width=0.55,
        )

        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.1f}%",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        ax.set_title("Average Routing Table Size Reduction by Strategy (%)", fontsize=13, fontweight="bold", pad=12)
        ax.set_ylabel("Table Size Reduction (%)", fontsize=11, labelpad=8)
        ax.set_ylim(0, 100)
        ax.grid(True, linestyle=":", alpha=0.6, axis="y")
        plt.xticks(rotation=12, ha="right", fontsize=9.5)

        filepath = os.path.join(self.output_dir, "strategy_reduction_comparison.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300)
        plt.close(fig)
        return filepath

    def generate_all_plots(self, df_scale: pd.DataFrame, df_comp: pd.DataFrame) -> List[str]:
        """Generates the full visual analytical suite."""
        files = []
        files.append(self.plot_table_size_comparison(df_scale, df_comp))
        files.append(self.plot_convergence_scaling(df_scale))
        files.append(self.plot_message_overhead(df_scale))
        files.append(self.plot_memory_comparison(df_scale, df_comp))
        files.append(self.plot_strategy_reduction_bar(df_comp))
        return files
