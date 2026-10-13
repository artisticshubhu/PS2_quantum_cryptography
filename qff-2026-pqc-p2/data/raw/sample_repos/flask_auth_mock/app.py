"""
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
