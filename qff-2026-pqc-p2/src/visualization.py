"""
Visualization Module for Qiskit Fall Fest 2026.
Generates publication-grade figures:
1. Processor A (5-qubit linear) & Processor B (9-qubit heavy-hex) coupling topologies.
2. Architecture co-design benchmark comparisons (Depth, CX, SWAP, Fidelity).
3. Scanner performance & Cryptographic Bill of Materials (CBOM) distribution.
4. Ideal vs Noisy execution distributions on AerSimulator.
5. Quantum migration urgency timeline (Mosher's Law).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from src.processors import QuantumProcessor


def plot_processor_topology(
    processor: QuantumProcessor,
    save_path: Optional[str | Path] = None,
    figsize: tuple = (7, 5),
) -> plt.Figure:
    """Plots the hardware coupling topology graph for a given quantum processor."""
    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    G = processor.graph

    # Layout selection based on topology
    if processor.num_qubits == 5:
        # Linear chain horizontal layout
        pos = {i: (i * 2.0, 0.0) for i in range(5)}
    else:
        # Spring or planar layout with seed for reproducibility
        pos = nx.spring_layout(G, seed=42, k=1.2)

    # Node styling based on degree
    degrees = dict(G.degree())
    node_colors = [degrees[n] for n in G.nodes()]

    # Draw edges
    nx.draw_networkx_edges(
        G,
        pos,
        ax=ax,
        width=2.5,
        edge_color="#4B5563",
        style="solid",
        alpha=0.85,
    )

    # Draw nodes
    nodes = nx.draw_networkx_nodes(
        G,
        pos,
        ax=ax,
        node_size=850,
        node_color=node_colors,
        cmap=plt.cm.coolwarm,
        edgecolors="#1E293B",
        linewidths=2.0,
    )

    # Labels
    nx.draw_networkx_labels(
        G,
        pos,
        ax=ax,
        font_size=12,
        font_weight="bold",
        font_color="#FFFFFF",
        font_family="sans-serif",
    )

    # Colorbar for degree
    cbar = plt.colorbar(nodes, ax=ax, orientation="vertical", shrink=0.7, pad=0.04)
    cbar.set_label("Node Degree (Connectivity)", fontsize=10, weight="bold")

    ax.set_title(
        f"{processor.name} Topology ({processor.num_qubits} Qubits, {G.number_of_edges()} Edges)\n"
        f"Architecture: {processor.topology_type}",
        fontsize=12,
        fontweight="bold",
        pad=15,
    )
    ax.axis("off")
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
    return fig


def plot_architecture_comparison(
    comparison_data: List[Dict[str, Any]],
    save_path: Optional[str | Path] = None,
    figsize: tuple = (12, 6),
) -> plt.Figure:
    """Plots comparative bar charts of circuit depth, CX count, SWAP count, and fidelity."""
    df = pd.DataFrame(comparison_data)
    fig, axes = plt.subplots(1, 3, figsize=figsize, dpi=300)

    processors = df["processor_name"].tolist()
    colors = ["#2563EB", "#059669"]  # Blue for A, Emerald for B

    # 1. Depth & Total Gates
    x = np.arange(len(processors))
    width = 0.35
    axes[0].bar(x - width/2, df["transpiled_depth"], width, label="Transpiled Depth", color="#3B82F6")
    axes[0].bar(x + width/2, df["original_depth"], width, label="Original Depth", color="#93C5FD")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([p.replace("_", "\n") for p in processors], fontsize=10)
    axes[0].set_ylabel("Circuit Depth", fontsize=11, fontweight="bold")
    axes[0].set_title("Circuit Depth Expansion", fontsize=12, fontweight="bold")
    axes[0].legend(frameon=True)
    axes[0].grid(axis="y", linestyle="--", alpha=0.5)

    # 2. CX Count and SWAP Overhead
    axes[1].bar(x - width/2, df["transpiled_cx"], width, label="Transpiled CX", color="#EF4444")
    axes[1].bar(x + width/2, df["estimated_swaps"], width, label="Inserted SWAPs", color="#F59E0B")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([p.replace("_", "\n") for p in processors], fontsize=10)
    axes[1].set_ylabel("Gate Count", fontsize=11, fontweight="bold")
    axes[1].set_title("CX & SWAP Routing Overhead", fontsize=12, fontweight="bold")
    axes[1].legend(frameon=True)
    axes[1].grid(axis="y", linestyle="--", alpha=0.5)

    # 3. Estimated Analytical Fidelity
    fidelities = [f * 100 for f in df["estimated_analytical_fidelity"]]
    bars = axes[2].bar(x, fidelities, width=0.5, color=colors)
    axes[2].set_xticks(x)
    axes[2].set_xticklabels([p.replace("_", "\n") for p in processors], fontsize=10)
    axes[2].set_ylabel("Estimated Fidelity (%)", fontsize=11, fontweight="bold")
    axes[2].set_title("Noise Impact (Fidelity)", fontsize=12, fontweight="bold")
    axes[2].set_ylim(0, 105)
    axes[2].grid(axis="y", linestyle="--", alpha=0.5)
    for bar in bars:
        yval = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.1f}%", ha="center", va="bottom", fontweight="bold")

    plt.suptitle("Processor A (5Q Linear) vs Processor B (9Q Heavy-Hex) Co-Design Benchmark", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
    return fig


def plot_scanner_summary(
    summary_by_algo: Dict[str, int],
    summary_by_severity: Dict[str, int],
    save_path: Optional[str | Path] = None,
    figsize: tuple = (11, 5),
) -> plt.Figure:
    """Plots detected cryptographic inventory distributions by algorithm and severity."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, dpi=300)

    # Algorithm breakdown
    algos = list(summary_by_algo.keys())
    counts = list(summary_by_algo.values())
    y_pos = np.arange(len(algos))

    ax1.barh(y_pos, counts, color="#6366F1", edgecolor="#312E81")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(algos, fontsize=10)
    ax1.invert_yaxis()
    ax1.set_xlabel("Detected Occurrences", fontsize=11, fontweight="bold")
    ax1.set_title("Cryptographic Inventory by Algorithm", fontsize=12, fontweight="bold")
    ax1.grid(axis="x", linestyle="--", alpha=0.5)

    # Severity donut chart
    sev_labels = list(summary_by_severity.keys())
    sev_counts = list(summary_by_severity.values())
    sev_colors = {"CRITICAL": "#DC2626", "HIGH": "#F97316", "MEDIUM": "#FBBF24", "LOW": "#10B981"}
    colors = [sev_colors.get(s, "#9CA3AF") for s in sev_labels]

    wedges, texts, autotexts = ax2.pie(
        sev_counts,
        labels=sev_labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.45, edgecolor="w", linewidth=2),
    )
    for at in autotexts:
        at.set_color("white")
        at.set_weight("bold")
    ax2.set_title("Vulnerability Severity Breakdown", fontsize=12, fontweight="bold")

    plt.suptitle("Static Analysis Scanner (PS-P2) Cryptographic Inventory Findings", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
    return fig


def plot_noisy_vs_ideal_distributions(
    results_a: Dict[str, Any],
    results_b: Dict[str, Any],
    save_path: Optional[str | Path] = None,
    figsize: tuple = (12, 5),
) -> plt.Figure:
    """Plots comparative ideal vs noisy execution probability histograms for A and B."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, sharey=True, dpi=300)

    for ax, res, title in [(ax1, results_a, "Processor A (5Q Linear)"), (ax2, results_b, "Processor B (9Q Heavy-Hex)")]:
        counts_ideal = res["ideal_counts"]
        counts_noisy = res["noisy_counts"]
        shots = res["shots"]

        top_states = sorted(counts_ideal.keys(), key=lambda k: counts_ideal[k], reverse=True)[:6]
        x = np.arange(len(top_states))
        width = 0.35

        p_ideal = [counts_ideal.get(s, 0) / shots for s in top_states]
        p_noisy = [counts_noisy.get(s, 0) / shots for s in top_states]

        ax.bar(x - width/2, p_ideal, width, label="Ideal Aer", color="#2563EB", alpha=0.9)
        ax.bar(x + width/2, p_noisy, width, label="Noisy (Synthetic)", color="#EF4444", alpha=0.9)
        ax.set_xticks(x)
        ax.set_xticklabels([f"|{s}⟩" for s in top_states], rotation=30, fontsize=10)
        ax.set_xlabel("Basis States", fontsize=11, fontweight="bold")
        ax.set_title(f"{title}\nTVD = {res['total_variation_distance']:.3f} | Overlap = {res['bhattacharyya_fidelity']:.3f}", fontsize=11, fontweight="bold")
        ax.legend(frameon=True)
        ax.grid(axis="y", linestyle="--", alpha=0.5)

    ax1.set_ylabel("Measurement Probability", fontsize=11, fontweight="bold")
    plt.suptitle("Ideal vs Synthetic Noisy Circuit Execution on Shor Threat Circuit", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
    return fig


def plot_migration_urgency_matrix(
    save_path: Optional[str | Path] = None,
    figsize: tuple = (8, 5),
) -> plt.Figure:
    """Plots Mosher's Law migration urgency matrix illustrating the quantum risk window."""
    fig, ax = plt.subplots(figsize=figsize, dpi=300)

    # Categories
    categories = [
        "Diffie-Hellman / ECDH\n(Harvest Now Decrypt Later)",
        "RSA-2048 / RSA-4096\n(Long-term Records)",
        "ECDSA / DSA\n(Digital Signatures)",
        "Firmware Signing Keys\n(10+ Yr Shelf-Life)",
        "Ephemeral Session Keys\n(Short Shelf-Life)",
    ]

    shelf_life = [15, 12, 7, 20, 2]       # years data must remain secret (X)
    migration_time = [4, 5, 3, 6, 2]     # years required to transition (Y)
    y_pos = np.arange(len(categories))

    # Stacked bar: Migration Time (Y) + Shelf Life (X)
    ax.barh(y_pos, migration_time, color="#F59E0B", label="Migration Time (Y years)", edgecolor="#B45309")
    ax.barh(y_pos, shelf_life, left=migration_time, color="#EF4444", label="Data Shelf-Life (X years)", edgecolor="#B91C1C")

    # Cryptographically Relevant Quantum Computer (CRQC) threshold line: Z = 10 years
    ax.axvline(x=10, color="#1E293B", linestyle="--", linewidth=2.5, label="CRQC Arrival Horizon (Z = 10 yrs)")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("Time Horizon (Years)", fontsize=11, fontweight="bold")
    ax.set_title("Mosher's Law Quantum Risk Matrix: If X + Y > Z, You Are Already at Risk!", fontsize=12, fontweight="bold", pad=12)
    ax.legend(loc="lower right", frameon=True)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
    return fig
