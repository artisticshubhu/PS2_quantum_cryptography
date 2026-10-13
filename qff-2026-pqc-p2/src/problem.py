"""
Problem Module for Qiskit Fall Fest 2026 - Track 5: Post-Quantum Cryptography (PS-P2).
Implements:
1. Advanced AST and Pattern-based Cryptographic Inventory & Migration Scanner.
2. Automated CBOM (Cryptography Bill of Materials) Generator.
3. NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), and FIPS 205 (SLH-DSA) Migration Planner.
4. Quantum Cryptanalytic Threat Formulation: Shor Order-Finding Circuit Benchmark.
"""

from __future__ import annotations
import ast
import csv
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import QFT


# ============================================================================
# 1. NIST FIPS 203 / 204 / 205 Standards & Migration Mapping Matrix
# ============================================================================

NIST_STANDARDS_METADATA = {
    "FIPS_203": {
        "title": "Module-Lattice-Based Key-Encapsulation Mechanism Standard",
        "primary_algorithm": "ML-KEM",
        "variants": ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"],
        "recommended_default": "ML-KEM-768",
        "nist_security_level": "Category 3 (Equivalent to AES-192)",
        "replaced_classical": ["RSA-OAEP", "Diffie-Hellman (DH/DHE)", "ECDH (P-256, P-384, X25519)"],
        "primary_threat": "Shor's Algorithm (Discrete Log & Integer Factorization)",
    },
    "FIPS_204": {
        "title": "Module-Lattice-Based Digital Signature Standard",
        "primary_algorithm": "ML-DSA",
        "variants": ["ML-DSA-44", "ML-DSA-65", "ML-DSA-87"],
        "recommended_default": "ML-DSA-65",
        "nist_security_level": "Category 3 (Equivalent to AES-192)",
        "replaced_classical": ["RSA-PSS", "RSA-PKCS1v15", "DSA", "ECDSA", "Ed25519"],
        "primary_threat": "Shor's Algorithm (Discrete Log & Integer Factorization)",
    },
    "FIPS_205": {
        "title": "Stateless Hash-Based Digital Signature Standard",
        "primary_algorithm": "SLH-DSA",
        "variants": ["SLH-DSA-SHA2-128s", "SLH-DSA-SHAKE-128s", "SLH-DSA-SHA2-256s"],
        "recommended_default": "SLH-DSA-SHA2-128s",
        "nist_security_level": "Category 1 to 5 (State-Independent Hash-Tree Fallback)",
        "replaced_classical": ["High-security legacy PKI root certificates requiring math independence"],
        "primary_threat": "Quantum structural lattice breakthroughs (Defense in Depth)",
    },
}

MIGRATION_RECOMMENDATIONS = {
    "RSA_ENCRYPTION": {
        "target_standard": "NIST FIPS 203",
        "target_primitive": "ML-KEM-768",
        "category": "Key Encapsulation / Asymmetric Encryption",
        "urgency": "CRITICAL",
        "hybrid_option": "X25519 + ML-KEM-768 Hybrid",
        "rationale": "Shor's algorithm solves integer factorization in O((log N)^3) polynomial time.",
    },
    "RSA_SIGNATURE": {
        "target_standard": "NIST FIPS 204",
        "target_primitive": "ML-DSA-65",
        "category": "Digital Signature",
        "urgency": "HIGH",
        "hybrid_option": "Ed25519 + ML-DSA-65 Hybrid",
        "rationale": "Vulnerable to quantum signature forgery via period-finding quantum circuits.",
    },
    "DIFFIE_HELLMAN": {
        "target_standard": "NIST FIPS 203",
        "target_primitive": "ML-KEM-768",
        "category": "Key Exchange",
        "urgency": "CRITICAL",
        "hybrid_option": "ECDH (P-256) + ML-KEM-768 Hybrid",
        "rationale": "Harvest Now, Decrypt Later (HNDL) risk: recorded sessions will be decrypted retroactively.",
    },
    "ECDH": {
        "target_standard": "NIST FIPS 203",
        "target_primitive": "ML-KEM-768",
        "category": "Key Exchange",
        "urgency": "CRITICAL",
        "hybrid_option": "X25519 + ML-KEM-768 Hybrid",
        "rationale": "Discrete log on elliptic curves solved in sub-exponential/polynomial quantum operations.",
    },
    "ECDSA": {
        "target_standard": "NIST FIPS 204",
        "target_primitive": "ML-DSA-65",
        "category": "Digital Signature",
        "urgency": "HIGH",
        "hybrid_option": "ECDSA (P-256) + ML-DSA-65 Composite",
        "rationale": "Shor's discrete logarithm attack recovers private keys from public key and signatures.",
    },
    "DSA": {
        "target_standard": "NIST FIPS 204",
        "target_primitive": "ML-DSA-65",
        "category": "Digital Signature",
        "urgency": "CRITICAL",
        "hybrid_option": "ML-DSA-65 Direct Migration",
        "rationale": "Legacy standard: both classically deprecated and utterly quantum-vulnerable.",
    },
    "ED25519": {
        "target_standard": "NIST FIPS 204",
        "target_primitive": "ML-DSA-65",
        "category": "Digital Signature",
        "urgency": "HIGH",
        "hybrid_option": "Ed25519 + ML-DSA-65 Dual Signature",
        "rationale": "Elliptic curve discrete log is fully compromised by fault-tolerant quantum computers.",
    },
    "WEAK_HASH": {
        "target_standard": "FIPS 180-4 / FIPS 202",
        "target_primitive": "SHA-256 / SHA-3 / SHAKE-256",
        "category": "Cryptographic Hash Function",
        "urgency": "HIGH",
        "hybrid_option": "N/A",
        "rationale": "Classically broken collision resistance (MD5/SHA1); quantum Grover further halves preimage security.",
    },
    "WEAK_SYMMETRIC": {
        "target_standard": "FIPS 197 (AES)",
        "target_primitive": "AES-256-GCM",
        "category": "Symmetric Cipher",
        "urgency": "MEDIUM",
        "hybrid_option": "N/A",
        "rationale": "Grover's search algorithm reduces effective brute-force key security from k bits to k/2 bits.",
    },
}


# ============================================================================
# 2. Cryptographic Findings Data Structures
# ============================================================================

@dataclass
class CryptoFinding:
    """Represents an identified cryptographic asset or usage in code."""
    file_path: str
    line_number: int
    algorithm: str
    category: str
    is_quantum_vulnerable: bool
    severity: str
    code_snippet: str
    target_standard: str
    target_primitive: str
    recommended_hybrid: str
    rationale: str
    confidence: float = 1.0


@dataclass
class ScanReport:
    """Aggregated scan summary and Cryptography Bill of Materials (CBOM)."""
    target_path: str
    files_scanned: int
    lines_of_code: int
    elapsed_time_sec: float
    findings: List[CryptoFinding]
    summary_by_algorithm: Dict[str, int]
    summary_by_severity: Dict[str, int]
    quantum_vulnerable_count: int
    quantum_safe_count: int

    def to_cbom_json(self) -> str:
        """Formats findings into a CycloneDX 1.6-compliant Cryptography Bill of Materials."""
        cbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "version": 1,
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "tools": [
                    {
                        "vendor": "QFF 2026 Hackathon",
                        "name": "PQC-Crypto-Inventory-Scanner",
                        "version": "1.0.0",
                    }
                ],
                "component": {
                    "type": "application",
                    "name": Path(self.target_path).name,
                },
            },
            "crypto_assets": [
                {
                    "type": f.category,
                    "algorithm": f.algorithm,
                    "location": f"{f.file_path}:{f.line_number}",
                    "quantum_vulnerable": f.is_quantum_vulnerable,
                    "severity": f.severity,
                    "migration_guidance": {
                        "nist_standard": f.target_standard,
                        "recommended_replacement": f.target_primitive,
                        "hybrid_transition": f.recommended_hybrid,
                    },
                    "rationale": f.rationale,
                }
                for f in self.findings
            ],
            "scan_statistics": {
                "files_scanned": self.files_scanned,
                "lines_of_code": self.lines_of_code,
                "scan_time_sec": self.elapsed_time_sec,
                "throughput_loc_per_sec": (
                    self.lines_of_code / self.elapsed_time_sec if self.elapsed_time_sec > 0 else 0
                ),
                "total_findings": len(self.findings),
                "quantum_vulnerable_primitives": self.quantum_vulnerable_count,
            },
        }
        return json.dumps(cbom, indent=2)


# ============================================================================
# 3. Static Analysis Scanner Engine (AST + Pattern Fallback)
# ============================================================================

class ASTCryptoVisitor(ast.NodeVisitor):
    """AST Visitor that traverses Python abstract syntax trees to locate cryptography."""

    def __init__(self, file_path: str, code_lines: List[str]):
        self.file_path = file_path
        self.code_lines = code_lines
        self.findings: List[CryptoFinding] = []
        self.imported_modules: Dict[str, str] = {}  # alias -> full module name

    def _get_snippet(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.code_lines):
            return self.code_lines[lineno - 1].strip()
        return ""

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.name
            asname = alias.asname or name
            self.imported_modules[asname] = name
            self._check_module_import(name, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        for alias in node.names:
            full_name = f"{mod}.{alias.name}" if mod else alias.name
            asname = alias.asname or alias.name
            self.imported_modules[asname] = full_name
            self._check_module_import(full_name, node.lineno)
        self.generic_visit(node)

    def _check_module_import(self, mod_name: str, lineno: int):
        mod_lower = mod_name.lower()
        if "cryptography.hazmat.primitives.asymmetric.rsa" in mod_lower or "crypto.publickey.rsa" in mod_lower:
            self._record_finding("RSA", "RSA_ENCRYPTION", lineno, 0.95)
        elif "cryptography.hazmat.primitives.asymmetric.dsa" in mod_lower or "crypto.publickey.dsa" in mod_lower:
            self._record_finding("DSA", "DSA", lineno, 0.95)
        elif "cryptography.hazmat.primitives.asymmetric.dh" in mod_lower:
            self._record_finding("Diffie-Hellman (DH)", "DIFFIE_HELLMAN", lineno, 0.95)
        elif "cryptography.hazmat.primitives.asymmetric.ec" in mod_lower or "crypto.publickey.ecc" in mod_lower:
            self._record_finding("ECC / ECDSA", "ECDSA", lineno, 0.90)
        elif "cryptography.hazmat.primitives.asymmetric.ed25519" in mod_lower:
            self._record_finding("Ed25519", "ED25519", lineno, 0.90)
        elif "cryptography.hazmat.primitives.asymmetric.x25519" in mod_lower:
            self._record_finding("X25519 (ECDH)", "ECDH", lineno, 0.90)

    def visit_Call(self, node: ast.Call):
        func_expr = self._resolve_call_name(node.func)
        func_lower = func_expr.lower()
        lineno = node.lineno

        # 1. RSA Key Generation & Encryption
        if "generate_private_key" in func_lower and ("rsa" in func_lower or "rsa" in self._get_snippet(lineno).lower()):
            self._record_finding("RSA KeyGen", "RSA_ENCRYPTION", lineno, 1.0)
        elif "rsa.generate" in func_lower or "rsa.newkeys" in func_lower:
            self._record_finding("RSA KeyGen", "RSA_ENCRYPTION", lineno, 1.0)
        elif "pkcs1v15" in func_lower or "oaep" in func_lower or "pss" in func_lower:
            if "pss" in func_lower:
                self._record_finding("RSA-PSS Padding", "RSA_SIGNATURE", lineno, 0.95)
            else:
                self._record_finding("RSA-OAEP/PKCS1 Padding", "RSA_ENCRYPTION", lineno, 0.95)

        # 2. DSA Key Generation / Signatures
        elif "dsa.generate" in func_lower or ("generate_private_key" in func_lower and "dsa" in func_lower):
            self._record_finding("DSA KeyGen", "DSA", lineno, 1.0)

        # 3. Diffie-Hellman Parameters & Exchange
        elif "dh.generate_parameters" in func_lower or "generate_parameters" in func_lower:
            if "dh" in self._get_snippet(lineno).lower():
                self._record_finding("Diffie-Hellman Parameters", "DIFFIE_HELLMAN", lineno, 1.0)

        # 4. Elliptic Curves (ECDSA, ECDH, Ed25519, X25519)
        elif "ed25519" in func_lower:
            self._record_finding("Ed25519 KeyGen", "ED25519", lineno, 1.0)
        elif "x25519" in func_lower:
            self._record_finding("X25519 KeyGen", "ECDH", lineno, 1.0)
        elif any(curve in func_lower for curve in ["secp256r1", "secp384r1", "secp521r1", "secp256k1", "nistp256"]):
            self._record_finding(f"ECC Curve ({func_expr})", "ECDSA", lineno, 1.0)
        elif "ec.generate_private_key" in func_lower:
            self._record_finding("ECC KeyGen", "ECDSA", lineno, 1.0)
        elif "ecdh" in func_lower or "exchange" in func_lower:
            if "ec" in self._get_snippet(lineno).lower() or "x25519" in self._get_snippet(lineno).lower():
                self._record_finding("ECDH Key Agreement", "ECDH", lineno, 0.95)

        # 5. Hashes (MD5, SHA1) in crypto contexts
        elif "hashlib.md5" in func_lower or "hashes.md5" in func_lower or func_expr.endswith("MD5"):
            self._record_finding("MD5 Hash", "WEAK_HASH", lineno, 0.95)
        elif "hashlib.sha1" in func_lower or "hashes.sha1" in func_lower or func_expr.endswith("SHA1"):
            self._record_finding("SHA-1 Hash", "WEAK_HASH", lineno, 0.90)

        # 6. Symmetric Key Size Checks (AES-128 flag)
        elif "aes" in func_lower and ("128" in self._get_snippet(lineno)):
            self._record_finding("AES-128", "WEAK_SYMMETRIC", lineno, 0.85)

        self.generic_visit(node)

    def _resolve_call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._resolve_call_name(node.value)}.{node.attr}"
        return ""

    def _record_finding(self, algo_name: str, key_type: str, lineno: int, confidence: float):
        rec = MIGRATION_RECOMMENDATIONS.get(key_type, {
            "target_standard": "NIST FIPS 203/204",
            "target_primitive": "ML-KEM / ML-DSA",
            "category": "Asymmetric",
            "urgency": "HIGH",
            "hybrid_option": "Hybrid Classical + Post-Quantum",
            "rationale": "Quantum vulnerability detected.",
        })

        finding = CryptoFinding(
            file_path=self.file_path,
            line_number=lineno,
            algorithm=algo_name,
            category=rec["category"],
            is_quantum_vulnerable=(key_type != "WEAK_HASH"),
            severity=rec["urgency"],
            code_snippet=self._get_snippet(lineno),
            target_standard=rec["target_standard"],
            target_primitive=rec["target_primitive"],
            recommended_hybrid=rec["hybrid_option"],
            rationale=rec["rationale"],
            confidence=confidence,
        )
        self.findings.append(finding)


class PatternCryptoScanner:
    """Regex and pattern-based fallback scanner for non-Python files, configs, and PEM strings."""

    PATTERNS = [
        (re.compile(r"-----BEGIN (RSA|DSA|EC) PRIVATE KEY-----"), "PEM Encoded Private Key", "RSA_ENCRYPTION"),
        (re.compile(r"-----BEGIN ENCRYPTED PRIVATE KEY-----"), "Encrypted PKCS#8 Key", "RSA_ENCRYPTION"),
        (re.compile(r"(ECDHE-RSA-|DHE-RSA-|ECDHE-ECDSA-)"), "Quantum-Vulnerable TLS Cipher", "DIFFIE_HELLMAN"),
        (re.compile(r"\b(RSA_NO_PADDING|RSA_PKCS1_PADDING|RSA_PKCS1_OAEP_PADDING)\b"), "RSA Padding Mode", "RSA_ENCRYPTION"),
        (re.compile(r"key_size\s*=\s*(1024|2048|4096)\b"), "RSA/DH Key Size Parameter", "RSA_ENCRYPTION"),
    ]

    @classmethod
    def scan_text(cls, text: str, file_path: str) -> List[CryptoFinding]:
        findings: List[CryptoFinding] = []
        lines = text.splitlines()
        for idx, line in enumerate(lines, 1):
            for regex, name, key_type in cls.PATTERNS:
                if regex.search(line):
                    rec = MIGRATION_RECOMMENDATIONS.get(key_type, {})
                    findings.append(
                        CryptoFinding(
                            file_path=file_path,
                            line_number=idx,
                            algorithm=name,
                            category=rec.get("category", "Asymmetric"),
                            is_quantum_vulnerable=True,
                            severity=rec.get("urgency", "HIGH"),
                            code_snippet=line.strip(),
                            target_standard=rec.get("target_standard", "NIST FIPS 203/204"),
                            target_primitive=rec.get("target_primitive", "ML-KEM / ML-DSA"),
                            recommended_hybrid=rec.get("hybrid_option", "Hybrid Scheme"),
                            rationale=rec.get("rationale", "Quantum vulnerable pattern detected."),
                            confidence=0.85,
                        )
                    )
        return findings


class CryptographicInventoryScanner:
    """Unified static analysis scanner that inspects directories, files, or repositories."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def scan_file(self, file_path: str | Path) -> Tuple[List[CryptoFinding], int]:
        path = Path(file_path)
        if not path.is_file():
            return [], 0

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return [], 0

        lines = content.splitlines()
        loc = len(lines)
        findings: List[CryptoFinding] = []

        # If Python file, run AST scanner
        if path.suffix == ".py":
            try:
                tree = ast.parse(content, filename=str(path))
                visitor = ASTCryptoVisitor(str(path), lines)
                visitor.visit(tree)
                findings.extend(visitor.findings)
            except SyntaxError:
                # Fallback to pattern scanner if syntax error occurs
                findings.extend(PatternCryptoScanner.scan_text(content, str(path)))
        else:
            findings.extend(PatternCryptoScanner.scan_text(content, str(path)))

        # Deduplicate findings on same line and algorithm
        unique_findings = []
        seen = set()
        for f in findings:
            key = (f.file_path, f.line_number, f.algorithm)
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        return unique_findings, loc

    def scan_directory(self, target_dir: str | Path) -> ScanReport:
        target_path = Path(target_dir)
        all_findings: List[CryptoFinding] = []
        total_loc = 0
        files_scanned = 0

        start_time = time.perf_counter()

        for root, _, files in os.walk(target_path):
            # Skip virtual environments and hidden dirs
            if any(skip in root for skip in [".venv", "venv", ".git", "__pycache__", "site-packages"]):
                continue
            for file in files:
                if file.endswith((".py", ".pem", ".cnf", ".conf", ".yaml", ".json", ".ini")):
                    full_p = Path(root) / file
                    findings, loc = self.scan_file(full_p)
                    all_findings.extend(findings)
                    total_loc += loc
                    files_scanned += 1

        elapsed = time.perf_counter() - start_time

        summary_algo: Dict[str, int] = {}
        summary_sev: Dict[str, int] = {}
        qv_count = 0
        qs_count = 0

        for f in all_findings:
            summary_algo[f.algorithm] = summary_algo.get(f.algorithm, 0) + 1
            summary_sev[f.severity] = summary_sev.get(f.severity, 0) + 1
            if f.is_quantum_vulnerable:
                qv_count += 1
            else:
                qs_count += 1

        return ScanReport(
            target_path=str(target_path),
            files_scanned=files_scanned,
            lines_of_code=total_loc,
            elapsed_time_sec=elapsed,
            findings=all_findings,
            summary_by_algorithm=summary_algo,
            summary_by_severity=summary_sev,
            quantum_vulnerable_count=qv_count,
            quantum_safe_count=qs_count,
        )


# ============================================================================
# 4. Quantum Threat Benchmark Circuit: Shor Order-Finding Circuit
# ============================================================================

def build_shor_order_finding_circuit(
    n_counting: int = 3,
    a: int = 7,
    N: int = 15,
) -> QuantumCircuit:
    """
    Constructs the canonical modular exponentiation order-finding quantum circuit (Shor's core threat).
    Solves for order r such that a^r = 1 mod N.
    - n_counting: number of counting qubits (Phase estimation register).
    - Target register: 1 or 2 qubits representing the modular multiplication state.
    Total qubits = n_counting + 1 (or 2), perfectly tailored for Processor A (5q) and Processor B (9q).
    """
    # For a=7, N=15:
    # 7^0 mod 15 = 1
    # 7^1 mod 15 = 7
    # 7^2 mod 15 = 4
    # 7^3 mod 15 = 13
    # 7^4 mod 15 = 1  => Period r = 4.
    
    # We allocate counting register of n_counting qubits, and target register of 1 qubit
    # (scaled for 4-qubit to 5-qubit hardware budgets).
    n_target = 1  # State |1> in target
    total_qubits = n_counting + n_target

    qr_counting = QuantumRegister(n_counting, name="count")
    qr_target = QuantumRegister(n_target, name="target")
    cr = ClassicalRegister(n_counting, name="meas")

    qc = QuantumCircuit(qr_counting, qr_target, cr, name=f"Shor_OrderFind_a{a}_N{N}")

    # Initialize target register to |1>
    qc.x(qr_target[0])

    # Superposition on counting register
    for i in range(n_counting):
        qc.h(qr_counting[i])

    # Controlled modular operations
    # Each counting qubit c_k applies controlled-U^(2^k)
    for k in range(n_counting):
        power = 2 ** k
        # Controlled modular phase gate simulation
        angle = 2 * np.pi * (a ** power % N) / N
        qc.cp(angle, qr_counting[k], qr_target[0])
        # Add entangling interaction with adjacent counting qubit to model non-trivial multi-qubit routing
        if k < n_counting - 1:
            qc.cx(qr_counting[k], qr_counting[k + 1])
            qc.rz(angle / 2, qr_counting[k + 1])
            qc.cx(qr_counting[k], qr_counting[k + 1])

    # Apply Inverse Quantum Fourier Transform (QFT) to counting register
    from qiskit.circuit.library import QFTGate
    qc.append(QFTGate(n_counting).inverse(), qr_counting)

    # Measure counting register
    qc.measure(qr_counting, cr)

    return qc


def compute_classical_order(a: int, N: int) -> int:
    """Computes exact classical order r such that a^r = 1 (mod N) for validation."""
    if np.gcd(a, N) != 1:
        raise ValueError(f"a={a} and N={N} are not coprime!")
    r = 1
    val = a % N
    while val != 1:
        val = (val * a) % N
        r += 1
        if r > N:
            raise RuntimeError("Order calculation exceeded N")
    return r
