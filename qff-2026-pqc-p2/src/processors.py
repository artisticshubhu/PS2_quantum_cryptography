"""
Processors Module for Qiskit Fall Fest 2026.
Defines Processor A (5-qubit linear baseline) and Processor B (9-qubit heavy-hex contemporary),
constructs topology graphs, coupling maps, basis gates, and calibrated synthetic noise models.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
from qiskit.transpiler import CouplingMap, Target
from qiskit.circuit.library import CXGate, RZGate, SXGate, XGate
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error


class QuantumProcessor:
    """Represents a quantum processor architecture with topology and noise model."""

    def __init__(self, config: Dict[str, Any], config_path: Optional[Path] = None):
        self.config = config
        self.config_path = config_path
        self.name: str = config["name"]
        self.num_qubits: int = int(config["num_qubits"])
        self.qubit_nodes: List[int] = list(config.get("qubit_nodes", list(range(self.num_qubits))))
        self.topology_type: str = config.get("topology_type", "Custom")
        self.undirected_edges: List[List[int]] = config["undirected_edges"]
        self.coupling_map_raw: List[List[int]] = config["coupling_map"]
        self.basis_gates: List[str] = list(config.get("basis_gates", ["rz", "sx", "x", "cx"]))
        self.noise_params: Dict[str, float] = config.get(
            "noise_model",
            {"gate_error_1q": 0.001, "gate_error_2q": 0.005, "readout_error": 0.01},
        )
        self.description: str = config.get("architectural_justification", "")

        # Build NetworkX graph
        self.graph = nx.Graph()
        self.graph.add_nodes_from(self.qubit_nodes)
        self.graph.add_edges_from([tuple(e) for e in self.undirected_edges])

        # Build Qiskit CouplingMap
        self.coupling_map = CouplingMap(self.coupling_map_raw)

        # Build Noise Model & AerSimulator
        self.noise_model = self._build_noise_model()
        self.simulator = AerSimulator(noise_model=self.noise_model)

    def _build_noise_model(self) -> NoiseModel:
        """Constructs the official synthetic depolarizing and readout noise model."""
        noise_model = NoiseModel()
        p1 = self.noise_params.get("gate_error_1q", 0.001)
        p2 = self.noise_params.get("gate_error_2q", 0.005)
        p_ro = self.noise_params.get("readout_error", 0.01)

        # 1-qubit depolarizing error for basis single qubit gates
        if p1 > 0:
            error_1q = depolarizing_error(p1, 1)
            noise_model.add_all_qubit_quantum_error(error_1q, ["rz", "sx", "x"])

        # 2-qubit depolarizing error for CX gates along each physical edge
        if p2 > 0:
            error_2q = depolarizing_error(p2, 2)
            # Add to all directed pairs in coupling map
            for edge in self.coupling_map_raw:
                noise_model.add_quantum_error(error_2q, "cx", [edge[0], edge[1]])

        # 1-qubit Readout error on measurement for all qubits
        if p_ro > 0:
            ro_matrix = [[1.0 - p_ro, p_ro], [p_ro, 1.0 - p_ro]]
            readout_err = ReadoutError(ro_matrix)
            noise_model.add_all_qubit_readout_error(readout_err)

        return noise_model

    def get_graph_metrics(self) -> Dict[str, Any]:
        """Calculates topological graph metrics for co-design analysis."""
        degrees = [d for _, d in self.graph.degree()]
        is_connected = nx.is_connected(self.graph)
        diameter = nx.diameter(self.graph) if is_connected else float("inf")
        avg_spl = (
            nx.average_shortest_path_length(self.graph) if is_connected else float("inf")
        )

        return {
            "name": self.name,
            "num_qubits": self.num_qubits,
            "num_edges": self.graph.number_of_edges(),
            "avg_degree": sum(degrees) / len(degrees) if degrees else 0.0,
            "max_degree": max(degrees) if degrees else 0,
            "diameter": diameter,
            "avg_shortest_path_length": avg_spl,
            "edge_to_node_ratio": self.graph.number_of_edges() / self.num_qubits,
            "is_connected": is_connected,
        }

    def __repr__(self) -> str:
        return f"<QuantumProcessor: {self.name} ({self.num_qubits} qubits, {self.topology_type})>"


def load_processor_from_file(json_path: str | Path) -> QuantumProcessor:
    """Loads a QuantumProcessor from a JSON configuration file."""
    path = Path(json_path)
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return QuantumProcessor(config, config_path=path)


def get_processor_a(base_dir: Optional[Path] = None) -> QuantumProcessor:
    """Convenience function to load Processor A."""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    path = base_dir / "processors" / "processor_A.json"
    return load_processor_from_file(path)


def get_processor_b(base_dir: Optional[Path] = None) -> QuantumProcessor:
    """Convenience function to load Processor B."""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    path = base_dir / "processors" / "processor_B.json"
    return load_processor_from_file(path)


def get_all_processors(base_dir: Optional[Path] = None) -> Dict[str, QuantumProcessor]:
    """Returns a dictionary containing both Processor A and Processor B."""
    return {
        "Processor_A": get_processor_a(base_dir),
        "Processor_B": get_processor_b(base_dir),
    }
