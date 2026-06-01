#!/usr/bin/env python3
"""
Generate cryptographic keys for production
"""

from cryptography.hazmat.primitives.asymmetric import ed25519
import os

def main():
    os.makedirs("keys", exist_ok=True)
    
    # Generate private key
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes_raw()
    
    with open("keys/issuer_private.key", "wb") as f:
        f.write(private_bytes)
    
    # Extract public key
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes_raw()
    
    with open("keys/issuer_public.key", "wb") as f:
        f.write(public_bytes)
    
    print("✅ Keys generated in ./keys/")
    print(f"   DID: did:key:{public_bytes.hex()}")
    print("\n🔒 Keep private key secure!")

if __name__ == "__main__":
    main()
