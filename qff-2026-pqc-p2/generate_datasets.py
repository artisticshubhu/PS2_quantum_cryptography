"""
Data generator for PS-P2: Populates data/raw/ and data/processed/ with
realistic open-source sample repositories (Flask mock, Requests TLS mock, PQC mock),
and ground-truth annotated benchmark corpus for precision/recall evaluation.
"""

from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# 1. Flask Auth Mock (Vulnerable Classical Crypto)
FLASK_AUTH_CODE = '''"""
Flask Authentication Service & Session Token Manager (Classical / Quantum-Vulnerable).
"""
import os
import hashlib
from flask import Flask, request, jsonify
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

app = Flask(__name__)

# Vulnerable: RSA 2048-bit key generation for JWT signing and session keys
SESSION_PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Vulnerable: Elliptic curve key using NIST P-256 (secp256r1)
DEVICE_AUTH_KEY = ec.generate_private_key(ec.SECP256R1())

@app.route("/api/login", methods=["POST"])
def login():
    username = request.json.get("username")
    password = request.json.get("password")
    
    # Vulnerable: Legacy MD5 password hash calculation
    password_hash = hashlib.md5(password.encode()).hexdigest()
    
    # Encrypt session token with RSA-OAEP
    public_key = SESSION_PRIVATE_KEY.public_key()
    ciphertext = public_key.encrypt(
        b"session_secret_token",
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        )
    )
    return jsonify({"status": "authenticated", "token_encrypted": ciphertext.hex()})

@app.route("/api/verify_signature", methods=["POST"])
def verify_signature():
    signature = request.json.get("signature")
    # Vulnerable: RSA PKCS1v15 legacy signature padding
    return jsonify({"verified": True})
'''

# 2. Requests TLS Mock (Vulnerable Key Exchange & Ciphers)
REQUESTS_TLS_CODE = '''"""
Requests / Urllib3 TLS Adapter with Diffie-Hellman and ECDHE configuration.
"""
import ssl
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.asymmetric import x25519

class CustomTLSAdapter:
    def __init__(self):
        # Vulnerable: Ephemeral Diffie-Hellman parameter generation
        self.dh_parameters = dh.generate_parameters(generator=2, key_size=2048)
        
        # Vulnerable: Classical X25519 Curve for ECDH Key Agreement
        self.private_key_x25519 = x25519.X25519PrivateKey.generate()
        self.peer_public_key = x25519.X25519PublicKey.from_public_bytes(b"0" * 32)
        
        # Vulnerable: Key exchange
        self.shared_key = self.private_key_x25519.exchange(self.peer_public_key)

    def configure_ciphers(self, context: ssl.SSLContext):
        # Vulnerable: Legacy quantum-vulnerable cipher list
        context.set_ciphers("ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384")
'''

# 3. Post-Quantum Migrated App (Safe reference)
PQC_MIGRATED_CODE = '''"""
Next-Generation Quantum-Safe Microservice.
Compliant with NIST FIPS 203 (ML-KEM) and NIST FIPS 204 (ML-DSA).
"""
import hashlib

# Quantum-Safe Key Encapsulation (NIST FIPS 203 ML-KEM-768)
class MLKEM768KeyManager:
    def __init__(self):
        self.standard = "NIST FIPS 203"
        self.algorithm = "ML-KEM-768"
        self.security_category = 3

    def encapsulate(self, public_key_bytes: bytes):
        # Module-lattice key encapsulation
        return b"shared_secret_256", b"ciphertext_1088_bytes"

# Quantum-Safe Digital Signature (NIST FIPS 204 ML-DSA-65)
class MLDSA65Signer:
    def __init__(self):
        self.standard = "NIST FIPS 204"
        self.algorithm = "ML-DSA-65"
        self.security_category = 3

    def sign(self, message: bytes):
        # Module-lattice digital signature
        return b"signature_3309_bytes"

# Quantum-Safe Hash: SHA-256 / SHA-3
def compute_secure_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
'''

# 4. Ground Truth Annotated Benchmark Corpus
CORPUS_CODE = '''"""
Cryptographic Benchmark Corpus with Known Ground-Truth Labels.
Used for rigorous Precision, Recall, and F1 evaluation of PS-P2 scanner.
"""
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, dsa, dh, ec, ed25519, x25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# [TP-1] RSA 2048 KeyGen (Vulnerable)
k_rsa = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# [TP-2] DSA KeyGen (Vulnerable)
k_dsa = dsa.generate_private_key(key_size=2048)

# [TP-3] DH Parameters (Vulnerable)
dh_p = dh.generate_parameters(generator=2, key_size=2048)

# [TP-4] EC Curve SECP256R1 (Vulnerable)
k_ec = ec.generate_private_key(ec.SECP256R1())

# [TP-5] EC Curve SECP384R1 (Vulnerable)
k_ec384 = ec.generate_private_key(ec.SECP384R1())

# [TP-6] Ed25519 KeyGen (Vulnerable)
k_ed = ed25519.Ed25519PrivateKey.generate()

# [TP-7] X25519 KeyGen (Vulnerable)
k_x = x25519.X25519PrivateKey.generate()

# [TP-8] MD5 Hash (Vulnerable / Deprecated)
h_md5 = hashlib.md5(b"test").hexdigest()

# [TP-9] SHA-1 Hash (Vulnerable / Deprecated)
h_sha1 = hashlib.sha1(b"test").hexdigest()

# [TP-10] AES-128 (Weak Symmetric under Grover)
c_aes128 = Cipher(algorithms.AES(b"0123456789abcdef"), modes.ECB())

# [TN-1] AES-256 (Quantum-Safe Symmetric)
c_aes256 = Cipher(algorithms.AES(b"0123456789abcdef0123456789abcdef"), modes.GCM(b"123456789012"))

# [TN-2] SHA-256 (Quantum-Safe Hash)
h_sha256 = hashlib.sha256(b"secure").hexdigest()

# [TN-3] SHA-3-256 (Quantum-Safe Hash)
h_sha3 = hashlib.sha3_256(b"secure").hexdigest()

# [TN-4] Classical math addition (Not crypto)
result = 42 + 100
'''

GROUND_TRUTH_LABELS = [
    {"line": 13, "label": "RSA KeyGen", "is_vuln": True, "type": "RSA"},
    {"line": 16, "label": "DSA KeyGen", "is_vuln": True, "type": "DSA"},
    {"line": 19, "label": "Diffie-Hellman Parameters", "is_vuln": True, "type": "DH"},
    {"line": 22, "label": "ECC Curve (ec.SECP256R1)", "is_vuln": True, "type": "ECC"},
    {"line": 25, "label": "ECC Curve (ec.SECP384R1)", "is_vuln": True, "type": "ECC"},
    {"line": 28, "label": "Ed25519", "is_vuln": True, "type": "ECC"},
    {"line": 31, "label": "X25519 (ECDH)", "is_vuln": True, "type": "ECC"},
    {"line": 34, "label": "MD5 Hash", "is_vuln": True, "type": "WEAK_HASH"},
    {"line": 37, "label": "SHA-1 Hash", "is_vuln": True, "type": "WEAK_HASH"},
    {"line": 40, "label": "AES-128", "is_vuln": True, "type": "WEAK_SYMMETRIC"},
]

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Write sample repos
    flask_dir = RAW_DIR / "sample_repos" / "flask_auth_mock"
    flask_dir.mkdir(parents=True, exist_ok=True)
    (flask_dir / "app.py").write_text(FLASK_AUTH_CODE, encoding="utf-8")

    requests_dir = RAW_DIR / "sample_repos" / "requests_tls_mock"
    requests_dir.mkdir(parents=True, exist_ok=True)
    (requests_dir / "tls_adapter.py").write_text(REQUESTS_TLS_CODE, encoding="utf-8")

    pqc_dir = RAW_DIR / "sample_repos" / "pqc_migrated_app"
    pqc_dir.mkdir(parents=True, exist_ok=True)
    (pqc_dir / "service.py").write_text(PQC_MIGRATED_CODE, encoding="utf-8")

    corpus_dir = RAW_DIR / "benchmark_corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    (corpus_dir / "crypto_cases.py").write_text(CORPUS_CODE, encoding="utf-8")

    # Write ground-truth labels
    labels_file = PROCESSED_DIR / "ground_truth_labels.json"
    with open(labels_file, "w", encoding="utf-8") as f:
        json.dump(GROUND_TRUTH_LABELS, f, indent=2)

    print("Successfully populated data/raw/ and data/processed/!")

if __name__ == "__main__":
    main()
