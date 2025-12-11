import didkit
import json

class VCIssuer:
    def issue_zkp_vc(self, score: float, fingerprint: str):
        vc = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "type": ["VerifiableCredential", "AntiSIMCredential"],
            "issuer": "did:web:bleu.ecology",
            "credentialSubject": {
                "antisimScore": score,
                "fingerprint": fingerprint
            }
        }
        return didkit.issue_credential(json.dumps(vc), '{"proofPurpose":"assertionMethod"}', "key.jwk")
