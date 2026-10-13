"""
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
