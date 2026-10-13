"""
Metrics Module for Qiskit Fall Fest 2026.
Computes:
1. Static analysis scanner metrics (Precision, Recall, F1-Score, Throughput).
2. Hardware compilation metrics (Depth, CX Count, SWAP Overhead, Qubit Active Footprint).
3. Quantum execution fidelity metrics (Analytical Fidelity, Total Variation Distance, Bhattacharyya Fidelity).
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from src.processors import QuantumProcessor


# ============================================================================
# 1. Scanner Performance Metrics
# ============================================================================

def compute_scanner_metrics(
    tp: int,
    fp: int,
    fn: int,
    tn: int = 0,
    elapsed_time_sec: float = 0.0,
    loc: int = 0,
) -> Dict[str, float]:
    """Computes precision, recall, F1-score, accuracy, and scanning throughput."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    total_samples = tp + fp + fn + tn
    accuracy = (tp + tn) / total_samples if total_samples > 0 else 1.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 1.0
    throughput = loc / elapsed_time_sec if elapsed_time_sec > 0 else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "accuracy": accuracy,
        "specificity": specificity,
        "elapsed_time_sec": elapsed_time_sec,
        "lines_of_code": loc,
        "throughput_loc_per_sec": throughput,
    }


# ============================================================================
# 2. Quantum Circuit & Hardware Architecture Metrics
# ============================================================================

def compute_circuit_hardware_metrics(
    original_circuit: QuantumCircuit,
    transpiled_circuit: QuantumCircuit,
    processor: QuantumProcessor,
) -> Dict[str, Any]:
    """Calculates gate counts, depth expansion, SWAP overhead, and analytical fidelity."""
    orig_ops = original_circuit.count_ops()
    trans_ops = transpiled_circuit.count_ops()

    orig_depth = original_circuit.depth()
    trans_depth = transpiled_circuit.depth()

    orig_cx = orig_ops.get("cx", 0)
    trans_cx = trans_ops.get("cx", 0)

    # In Qiskit decomposition into {rz, sx, x, cx}, each inserted SWAP gate is synthesized as 3 CX gates
    estimated_swaps = max(0, (trans_cx - orig_cx) // 3)

    count_1q = sum(trans_ops.get(g, 0) for g in ["rz", "sx", "x"])
    count_2q = trans_cx
    total_gates = sum(trans_ops.values())

    p1 = processor.noise_params.get("gate_error_1q", 0.001)
    p2 = processor.noise_params.get("gate_error_2q", 0.005)
    pro = processor.noise_params.get("readout_error", 0.01)

    # Find active physical qubits in transpiled circuit
    active_qubits = len(set(q._index for inst in transpiled_circuit.data for q in inst.qubits))
    if active_qubits == 0:
        active_qubits = transpiled_circuit.num_qubits

    # Estimated circuit fidelity under depolarizing & readout noise
    est_fidelity = ((1.0 - p1) ** count_1q) * ((1.0 - p2) ** count_2q) * ((1.0 - pro) ** active_qubits)

    return {
        "processor_name": processor.name,
        "processor_qubits": processor.num_qubits,
        "topology": processor.topology_type,
        "original_qubits": original_circuit.num_qubits,
        "active_physical_qubits": active_qubits,
        "original_depth": orig_depth,
        "transpiled_depth": trans_depth,
        "depth_expansion": trans_depth / orig_depth if orig_depth > 0 else 1.0,
        "original_total_gates": sum(orig_ops.values()),
        "transpiled_total_gates": total_gates,
        "original_cx": orig_cx,
        "transpiled_cx": trans_cx,
        "cx_overhead_ratio": trans_cx / orig_cx if orig_cx > 0 else 1.0,
        "estimated_swaps": estimated_swaps,
        "single_qubit_gates": count_1q,
        "two_qubit_gates": count_2q,
        "estimated_analytical_fidelity": est_fidelity,
        "hardware_footprint_volume": trans_depth * active_qubits,
    }


# ============================================================================
# 3. Execution Simulation & Distribution Comparison Metrics
# ============================================================================

def execute_and_compare_simulation(
    transpiled_circuit: QuantumCircuit,
    processor: QuantumProcessor,
    shots: int = 4096,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Executes circuit on both Ideal AerSimulator and Noisy AerSimulator with official noise model.
    Computes Total Variation Distance (TVD), Bhattacharyya overlap, and peak state preservation.
    """
    ideal_sim = AerSimulator()
    noisy_sim = processor.simulator

    # Run Ideal simulation
    job_ideal = ideal_sim.run(transpiled_circuit, shots=shots, seed_simulator=seed)
    counts_ideal = job_ideal.result().get_counts()

    # Run Noisy simulation
    job_noisy = noisy_sim.run(transpiled_circuit, shots=shots, seed_simulator=seed)
    counts_noisy = job_noisy.result().get_counts()

    # Normalize to probability distributions
    all_keys = set(counts_ideal.keys()).union(set(counts_noisy.keys()))
    prob_ideal = {k: counts_ideal.get(k, 0) / shots for k in all_keys}
    prob_noisy = {k: counts_noisy.get(k, 0) / shots for k in all_keys}

    # Total Variation Distance: TVD = 0.5 * sum(|P - Q|)
    tvd = 0.5 * sum(abs(prob_ideal[k] - prob_noisy[k]) for k in all_keys)

    # Classical Bhattacharyya Fidelity: sum(sqrt(P * Q))
    fidelity_bhattacharyya = sum(math.sqrt(prob_ideal[k] * prob_noisy[k]) for k in all_keys)

    # Peak state preservation (the most frequent ideal state)
    peak_state = max(prob_ideal.items(), key=lambda x: x[1])[0]
    peak_prob_ideal = prob_ideal[peak_state]
    peak_prob_noisy = prob_noisy.get(peak_state, 0.0)
    peak_preservation_ratio = peak_prob_noisy / peak_prob_ideal if peak_prob_ideal > 0 else 0.0

    # Standard error for peak state
    std_error_peak = math.sqrt(peak_prob_noisy * (1.0 - peak_prob_noisy) / shots)

    return {
        "shots": shots,
        "ideal_counts": counts_ideal,
        "noisy_counts": counts_noisy,
        "total_variation_distance": tvd,
        "bhattacharyya_fidelity": fidelity_bhattacharyya,
        "peak_state": peak_state,
        "peak_prob_ideal": peak_prob_ideal,
        "peak_prob_noisy": peak_prob_noisy,
        "peak_preservation_ratio": peak_preservation_ratio,
        "peak_standard_error": std_error_peak,
    }
