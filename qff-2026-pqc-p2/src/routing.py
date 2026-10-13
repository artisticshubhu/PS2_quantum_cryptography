"""
Routing and Transpilation Module for Qiskit Fall Fest 2026.
Handles circuit compilation, layout mapping, routing methods (Sabre, Lookahead, Basic),
and basis gate decomposition for Processor A (5-qubit linear) and Processor B (9-qubit heavy-hex).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap, Layout

from src.processors import QuantumProcessor


def transpile_circuit_for_processor(
    circuit: QuantumCircuit,
    processor: QuantumProcessor,
    optimization_level: int = 1,
    routing_method: str = "sabre",
    layout_method: str = "sabre",
    seed: int = 42,
) -> QuantumCircuit:
    """
    Transpiles a logical quantum circuit onto the physical target processor architecture.
    Decomposes into basis gates: {rz, sx, x, cx}.
    Inserts SWAP gates to satisfy physical coupling constraints.
    """
    transpiled_qc = transpile(
        circuits=circuit,
        coupling_map=processor.coupling_map,
        basis_gates=processor.basis_gates,
        optimization_level=optimization_level,
        routing_method=routing_method,
        layout_method=layout_method,
        seed_transpiler=seed,
    )
    return transpiled_qc


def benchmark_routing_strategies(
    circuit: QuantumCircuit,
    processor: QuantumProcessor,
    routing_methods: Optional[List[str]] = None,
    optimization_levels: Optional[List[int]] = None,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Evaluates multiple routing methods and optimization levels across a target processor.
    Returns comparison records of depth, gate count, CX count, and SWAP overhead.
    """
    if routing_methods is None:
        routing_methods = ["sabre", "lookahead", "basic"]
    if optimization_levels is None:
        optimization_levels = [1, 2, 3]

    results = []
    original_depth = circuit.depth()
    original_cx = circuit.count_ops().get("cx", 0)

    for opt in optimization_levels:
        for r_method in routing_methods:
            try:
                transpiled = transpile_circuit_for_processor(
                    circuit=circuit,
                    processor=processor,
                    optimization_level=opt,
                    routing_method=r_method,
                    seed=seed,
                )
                ops = transpiled.count_ops()
                final_cx = ops.get("cx", 0)
                final_depth = transpiled.depth()
                total_gates = sum(ops.values())
                # SWAP overhead estimation: each SWAP decomposes to 3 CX gates
                swap_est = max(0, (final_cx - original_cx) // 3)

                results.append({
                    "processor": processor.name,
                    "num_qubits": processor.num_qubits,
                    "topology": processor.topology_type,
                    "optimization_level": opt,
                    "routing_method": r_method,
                    "original_depth": original_depth,
                    "transpiled_depth": final_depth,
                    "depth_expansion_ratio": final_depth / original_depth if original_depth > 0 else 1.0,
                    "original_cx": original_cx,
                    "transpiled_cx": final_cx,
                    "estimated_swaps": swap_est,
                    "total_gates": total_gates,
                    "gate_count_rz": ops.get("rz", 0),
                    "gate_count_sx": ops.get("sx", 0),
                    "gate_count_x": ops.get("x", 0),
                })
            except Exception as e:
                results.append({
                    "processor": processor.name,
                    "optimization_level": opt,
                    "routing_method": r_method,
                    "error": str(e),
                })

    return results
