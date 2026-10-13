# Qiskit Fall Fest 2026 — Phase 1 Master Submission
## Track 5: Post-Quantum Cryptography (Quantum-Safe Systems)
### Problem Statement PS-P2: Cryptographic Inventory & Migration Scanner
**Unified Algorithm ↔ Architecture Co-Design: Mapping Classical Vulnerabilities to Physical Quantum Processors**

---

## 1. Project Overview & Challenge Statement

Modern public-key cryptography—predominantly **RSA**, **Diffie-Hellman (DH)**, and **Elliptic Curve Cryptography (ECC)**—protects digital trust, internet protocols, and confidential communication. However, these foundational primitives are universally vulnerable to polynomial-time cryptanalysis via **Shor's Algorithm** on fault-tolerant quantum computers.

This repository provides an end-to-end, reproducible solution for **PS-P2: Cryptographic Inventory & Migration Scanner** under the **Qiskit Fall Fest 2026 Phase 1 Master Challenge Kit**. Our solution bridges high-level software security with physical quantum hardware:
1. **Core Problem Solution (PS-P2)**: An industrial static analysis scanner combining Abstract Syntax Tree (AST) inspection and regex heuristics that detects quantum-vulnerable cryptography across codebases, generates a CycloneDX 1.6-compliant **Cryptography Bill of Materials (CBOM)**, and provides automated migration roadmaps to **NIST FIPS 203 (ML-KEM)**, **FIPS 204 (ML-DSA)**, and **FIPS 205 (SLH-DSA)**.
2. **Universal Co-Design Framework**: To address the hackathon's core objective (evaluating how physical connectivity, gate routing, and noise affect execution fidelity), we construct the exact **quantum cryptanalytic threat vector**—a scalable modular exponentiation and order-finding circuit—and benchmark its execution on **Processor A** (5-Qubit Linear Baseline) versus **Processor B** (9-Qubit Sparse Heavy-Hex Inspired Architecture) under the official synthetic noise model.

---

## 2. Authoritative Repository Structure

The repository strictly follows the official file structure mandated by the Hackathon & Competitions Cell:

```text
qff-2026-pqc-p2/
├── README.md                          # Problem statement selected, setup, methodology, key results
├── main.ipynb                         # End-to-end reproducible experiment notebook with full cell outputs
├── requirements.txt                   # Pinned software dependencies (qiskit, qiskit-aer, networkx, etc.)
├── report.md                          # Architectural analysis, trade-off interpretation, limitations
├── generate_latex_assets.py           # Script rendering official mathematical formulas
├── generate_datasets.py               # Script generating mock codebases and ground-truth corpus
├── run_benchmark.py                   # Automated end-to-end benchmark and plotting driver
├── build_notebook.py                  # Headless notebook build & pre-execution pipeline
├── data/
│   ├── raw/                           # Raw input data and open-source codebase targets
│   │   ├── benchmark_corpus/          # Annotated crypto testbed (crypto_cases.py)
│   │   └── sample_repos/              # Real-world target mock repositories
│   │       ├── flask_auth_mock/       # Flask authentication & JWT microservice
│   │       ├── requests_tls_mock/     # Requests/Urllib3 TLS adapter configuration
│   │       └── pqc_migrated_app/      # NIST FIPS 203/204 clean reference control
│   └── processed/
│       ├── ground_truth_labels.json   # Exact ground-truth classification labels
│       └── cbom_inventory.json        # Exported CycloneDX 1.6 CBOM records
├── processors/
│   ├── processor_A.json               # Participant-defined Processor A coupling map & config (5Q Linear)
│   └── processor_B.json               # Participant-defined Processor B coupling map & config (9Q Heavy-Hex)
├── src/
│   ├── __init__.py                    # Package initializer
│   ├── problem.py                     # AST/Pattern scanner engine & Shor order-finding threat circuit
│   ├── processors.py                  # QuantumProcessor class, topology graphs, and noise loaders
│   ├── routing.py                     # Transpilation, SabreRouting, and layout compilation routines
│   ├── metrics.py                     # Scanner evaluation, hardware overhead, and fidelity metrics
│   └── visualization.py               # Publication-grade topology, comparison, and histogram plotting
├── results/
│   ├── tables/                        # Exported CSV benchmark comparison tables
│   │   ├── scanner_benchmark.csv      # Precision, Recall, F1, and execution latency across targets
│   │   ├── cbom_inventory.csv         # Cryptographic inventory and migration guidance
│   │   ├── processor_comparison.csv   # Processor A vs B hardware and fidelity benchmark
│   │   └── routing_strategies.csv     # Multi-pass transpilation across routing algorithms
│   └── figures/                       # Publication-quality exported figures (300 DPI)
│       ├── topology_processor_a.png   # Processor A coupling graph visualization
│       ├── topology_processor_b.png   # Processor B coupling graph visualization
│       ├── circuit_depth_comparison.png# Transpiled depth, CX counts, SWAP overhead & fidelity
│       ├── scanner_summary.png        # Detected primitives and severity distribution
│       ├── noisy_vs_ideal_distributions.png # Ideal vs synthetic noisy Aer measurement distributions
│       └── migration_urgency_matrix.png# Mosher's Law quantum migration timeline
└── assets/
    └── qff_phase1_latex_images/       # High-resolution LaTeX equation renders
        ├── eq_qubit_state.png         # State vector normalization
        ├── eq_bell_state.png          # Bell state formulation
        ├── eq_graph.png               # Graph topology and degree formulation
        ├── eq_bell_fidelity.png       # Quantum state fidelity
        ├── eq_zz_expectation.png      # Expectation value calculation
        └── eq_standard_error.png      # Binomial standard error formulation
```

---

## 3. Environment Specification & Setup Instructions

### Prerequisites
- Python 3.10, 3.11, or 3.12 (CPython recommended)
- `pip` or `uv` package manager

### Installation (Clean Environment)
```bash
# Clone the repository
git clone https://github.com/<your-username>/qff-2026-pqc-p2.git
cd qff-2026-pqc-p2

# Create a virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

### Reproducing All Results (One-Click)
To re-run the entire scanner benchmark, quantum co-design compilation, noisy Aer simulations, table exports, and figure generation:
```bash
python run_benchmark.py
```

To re-execute the interactive Jupyter Notebook `main.ipynb`:
```bash
python build_notebook.py
```
Or launch JupyterLab / Notebook directly:
```bash
jupyter notebook main.ipynb
```

---

## 4. Methodology & Implementation Details

### 4.1 AST & Pattern Static Analysis Scanner (`src/problem.py`)
The scanner inspects codebases without executing them, preventing security risks from malicious code execution.
- **AST Visitor (`ASTCryptoVisitor`)**: Parses Python abstract syntax trees (`ast.parse`), inspects `Import` and `ImportFrom` nodes, and deeply analyzes `Call` nodes (e.g., `rsa.generate_private_key`, `ec.generate_private_key`, `dh.generate_parameters`, `padding.OAEP`, `hashlib.md5`).
- **Pattern Matcher (`PatternCryptoScanner`)**: Regular expression engine that catches PEM-encoded private keys (`-----BEGIN RSA PRIVATE KEY-----`), TLS cipher suites (`ECDHE-RSA-AES128-GCM-SHA256`), and configuration settings.
- **Standards Mapping Engine**: Automatically pairs detected items with NIST Post-Quantum Standards:
  - **RSA-OAEP / DH / ECDH** $\rightarrow$ **NIST FIPS 203 (ML-KEM-768)**
  - **RSA-PSS / DSA / ECDSA / Ed25519** $\rightarrow$ **NIST FIPS 204 (ML-DSA-65)**
  - **Root PKI / Conservative Signatures** $\rightarrow$ **NIST FIPS 205 (SLH-DSA)**
  - **Weak Hashes (MD5, SHA-1)** $\rightarrow$ **FIPS 180-4 / 202 (SHA-256 / SHA-3)**
  - **Weak Symmetric (AES-128)** $\rightarrow$ **FIPS 197 (AES-256-GCM)** (mitigating Grover's search)

### 4.2 Quantum Architecture Modeling (`src/processors.py`)
- **Processor A (Baseline Reference)**:
  - 5 physical qubits (Nodes 0 to 4), linear nearest-neighbor coupling: `[(0,1), (1,2), (2,3), (3,4)]`.
  - Architecture rationale: Represents 1D superconducting transmon chains. Simple fabrication with zero planar crossings, but constrained to graph diameter 4, requiring $\mathcal{O}(N)$ SWAP gates for non-adjacent interactions.
- **Processor B (Contemporary Reference)**:
  - 9 physical qubits (Nodes 0 to 8), heavy-hex inspired sparse planar graph (12 undirected edges):
    `[(0,1), (1,2), (1,6), (2,3), (2,6), (2,5), (3,4), (4,5), (5,6), (6,7), (6,8), (8,0)]`.
  - Architecture rationale: Heavy-hex design inspired by contemporary IBM quantum processors. Restricting degree minimizes spectator qubit frequency collisions and crosstalk, while central node 6 acts as a routing hub that provides 2D routing shortcuts.
- **Official Synthetic Noise Model**:
  - 1-qubit depolarizing error: $p = 0.001$ ($0.1\%$) on $\{rz, sx, x\}$
  - 2-qubit depolarizing error: $p = 0.005$ ($0.5\%$) on $cx$
  - Readout error: $p = 0.01$ ($1.0\%$) on measurement
  - Identical error rates are applied to both processors to isolate topological routing effects.

### 4.3 Quantum Threat Vector: Shor Order-Finding Circuit
To bridge the static scanner findings to physical quantum hardware, we model the foundational cryptanalytic threat breaking RSA and ECC:
- Canonical modular exponentiation and order-finding circuit: $U|y\rangle = |a y \pmod N\rangle$ with $a=7, N=15$ (analytical period $r=4$).
- Counting register (3 qubits) in superposition + 1 target qubit.
- Controlled phase rotations and Inverse Quantum Fourier Transform ($\text{QFT}^\dagger$).
- 4 logical qubits, transpiled onto Processor A (5q) and Processor B (9q) using SabreRouting and basis gates $\{rz, sx, x, cx\}$.

---

## 5. Quantitative Results & Key Findings

### 5.1 Static Analysis Scanner Performance Benchmark
Evaluated across our curated ground-truth corpus and mock open-source projects (`Flask` and `Requests`):

| Target Codebase | Files | LOC | TP | FP | FN | Precision | Recall | F1-Score | Scan Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Annotated Benchmark Corpus** | 1 | 50 | 10 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | **4.2 ms** |
| **Flask Auth Service (Mock)** | 1 | 46 | 7 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | **2.4 ms** |
| **Requests TLS Adapter (Mock)** | 1 | 22 | 6 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | **2.3 ms** |
| **PQC Clean Service (Control)** | 1 | 31 | 0 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | **0.8 ms** |

*Highlights*:
- Perfect **100% precision and recall** on all tested cryptographic primitives.
- **Zero false positives** on modernized NIST FIPS 203/204 code.
- Scanning throughput exceeds **10,000 lines of code per second**.

### 5.2 Processor A vs Processor B Co-Design Benchmark

| Architectural Metric | Logical Circuit | Processor A (5Q Linear) | Processor B (9Q Heavy-Hex) | Delta (Advantage of B) |
| :--- | :---: | :---: | :---: | :---: |
| **Qubit Count** | 4 | 5 | 9 | +4 spare qubits |
| **Graph Diameter** | — | 4 | 4 | Equal diameter |
| **Average Degree** | — | 1.60 | 2.67 | +66.9% connectivity |
| **Circuit Depth** | 12 | 52 | **45** | **-13.5% depth reduction** |
| **Depth Expansion** | 1.0x | 4.33x | **3.75x** | Less dilation |
| **CX Gate Count** | 4 | 31 | **22** | **-29.0% fewer 2Q gates** |
| **CX Overhead Ratio** | 1.0x | 7.75x | **5.50x** | Substantially reduced |
| **Inserted SWAP Gates** | 0 | 9 | **6** | **33.3% fewer SWAPs** |
| **Total Gate Count** | 17 | 72 | **63** | -12.5% gates |
| **Estimated Fidelity** | 100% | 79.17% | **82.82%** | **+3.65% higher fidelity** |
| **Total Variation Dist.**| 0.000 | 0.0364 | **0.0308** | **-15.4% lower drift** |
| **Bhattacharyya Overlap**| 1.0000 | 0.9988 | **0.9991** | Higher state overlap |
| **Peak State Preserved** | 100% | 91.07% | **93.19%** | **+2.12% higher peak** |

### 5.3 Key Architectural Insights
1. **Linear Bottleneck**: The 1D topology of Processor A requires linear SWAP chains whenever qubits at opposite ends of the chain must interact, causing CX count to balloon from 4 to 31 (a 7.75x overhead).
2. **Heavy-Hex Shortcut Efficiency**: Processor B's central node (Node 6) provides a low-hop bypass connecting non-adjacent regions. The compiler (SabreRouting) successfully routes entangling gates with only 6 SWAP operations, reducing circuit depth to 45 and CX gates to 22.
3. **Noise Attenuation**: Because 2-qubit CX gates have 5x higher error rates ($0.5\%$) than single-qubit gates ($0.1\%$), eliminating 9 CX gates directly preserves fidelity, giving Processor B an analytical fidelity of 82.82% vs 79.17% on Processor A.

---

## 6. Strategic Migration Roadmap (Mosher's Law)

The urgency of post-quantum migration is governed by **Mosher's Inequality**:
$$\text{If } X + Y > Z, \quad \text{an organization is ALREADY compromised!}$$
- $X$ = **Data Shelf-Life** (confidentiality duration: 10–25 years for medical, defense, and banking records).
- $Y$ = **Migration Timeline** (time to upgrade infrastructure and re-key systems: 3–7 years).
- $Z$ = **CRQC Horizon** (time until a Cryptographically Relevant Quantum Computer arrives: ~10 years).

Because $X + Y > Z$ holds for all critical infrastructure, **Harvest Now, Decrypt Later (HNDL)** attacks mean that classical Diffie-Hellman and RSA session exchanges captured today will be retroactively decrypted. Organizations must immediately adopt hybrid key encapsulation:
$$\text{Shared Secret} = \text{KDF}(\text{SS}_{\text{ECDH}} \,\|\, \text{SS}_{\text{ML-KEM-768}})$$

---

## 7. Phase 1 Closing Checklist

- [x] **Problem Statement Selected**: PS-P2 (Post-Quantum Cryptography - Cryptographic Inventory & Migration Scanner).
- [x] **Core Solution Implemented**: Full AST and pattern scanner engine with CBOM generation.
- [x] **Classical / Exact Ground Truth Verification**: Verified against annotated testbed with 100% precision/recall.
- [x] **Processor A (5Q) and Processor B (9Q) Defined**: Creative coupling maps and configurations in `processors/`.
- [x] **Transpilation & Routing Completed**: Compiled using SabreRouting at Optimization Level 1, seed 42.
- [x] **Quantitative Comparison Table Generated**: `results/tables/processor_comparison.csv` with depth, CX, SWAP, fidelity.
- [x] **Official Synthetic Noise Model Evaluated**: Simulating depolarizing and readout errors on AerSimulator (4096 shots).
- [x] **Authoritative File Structure Maintained**: Strict adherence to official Master Guide directory layout.
- [x] **Main Notebook Verified**: `main.ipynb` fully runnable and pre-populated with executed outputs.

---
*SRM University-AP | Qiskit Fall Fest 2026 | Hackathon & Competitions Cell*
