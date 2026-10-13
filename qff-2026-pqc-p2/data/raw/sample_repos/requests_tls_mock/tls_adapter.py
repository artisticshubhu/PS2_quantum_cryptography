"""
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
