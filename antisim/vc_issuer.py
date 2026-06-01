"""
Verifiable Credential Issuer with real signatures
"""

import json
import time
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
import base64
from typing import Dict, Optional


class VCIssuer:
    """Issue and verify credentials with Ed25519 signatures"""
    
    def __init__(self, private_key_path: Optional[str] = None):
        if private_key_path:
            with open(private_key_path, 'rb') as f:
                self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(f.read())
        else:
            # Generate key pair for demo
            self.private_key = ed25519.Ed25519PrivateKey.generate()
        
        self.public_key = self.private_key.public_key()
        self.did = "did:key:" + base64.b64encode(self.public_key.public_bytes_raw()).decode()
    
    def issue_attestation(self, prompt: str, response: str, risk_score: float, prevention_events: List) -> str:
        """Issue signed attestation for generation"""
        
        credential = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "type": ["VerifiableCredential", "AntiSIMAttestation"],
            "issuer": self.did,
            "issuanceDate": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "credentialSubject": {
                "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
                "response_hash": hashlib.sha256(response.encode()).hexdigest(),
                "risk_score": risk_score,
                "prevention_count": len(prevention_events)
            }
        }
        
        # Sign the credential
        credential_json = json.dumps(credential, sort_keys=True)
        signature = self.private_key.sign(credential_json.encode())
        
        credential["proof"] = {
            "type": "Ed25519Signature2020",
            "signature": base64.b64encode(signature).decode(),
            "verificationMethod": self.did
        }
        
        return json.dumps(credential)
    
    def verify_attestation(self, attestation_json: str) -> Dict:
        """Verify attestation signature"""
        attestation = json.loads(attestation_json)
        
        # Extract proof
        proof = attestation.pop("proof")
        signature = base64.b64decode(proof["signature"])
        
        # Verify
        attestation_json = json.dumps(attestation, sort_keys=True)
        
        try:
            # Reconstruct public key from DID
            public_key_bytes = base64.b64decode(proof["verificationMethod"].replace("did:key:", ""))
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(signature, attestation_json.encode())
            return {"valid": True, "attestation": attestation}
        except:
            return {"valid": False, "reason": "invalid_signature"}
    
    def issue_verification(self, verified_claims: List, hallucinations: List) -> str:
        """Issue verification of claim checking"""
        verification = {
            "verified_count": len(verified_claims),
            "hallucination_count": len(hallucinations),
            "timestamp": time.time()
        }
        
        verification_json = json.dumps(verification, sort_keys=True)
        signature = self.private_key.sign(verification_json.encode())
        
        return base64.b64encode(signature).decode()
