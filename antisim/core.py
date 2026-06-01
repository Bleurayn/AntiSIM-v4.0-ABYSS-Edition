"""
AntiSIM v4.0 Core Engine - Pre-output hallucination prevention
"""

import json
import hashlib
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

from .guard import AntiSIMGuard
from .predictor import TokenHallucinationPredictor
from .watermark import RobustWatermark
from .vc_issuer import VCIssuer


@dataclass
class GenerationResult:
    """Result of safe generation"""
    response: str
    hallucination_risk: float
    prevention_events: List[Dict]
    token_path: List[str]
    cryptographic_attestation: Optional[str]


class AntiSIM:
    """
    Pre-output hallucination prevention engine.
    Predicts and blocks hallucination paths before generation.
    """
    
    def __init__(self, config_path: str = "antisim/config.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        
        # Load model (use smaller model for demo, configurable for production)
        model_name = self.config.get("model_name", "gpt2")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.model.eval()
        
        # Initialize components
        self.guard = AntiSIMGuard()
        self.predictor = TokenHallucinationPredictor()
        self.watermark = RobustWatermark()
        self.issuer = VCIssuer()
        
        # Configuration
        self.risk_threshold = self.config.get("risk_threshold", 0.3)
        self.max_tokens = self.config.get("max_tokens", 200)
        self.temperature = self.config.get("temperature", 0.7)
        
    def generate_safe(self, prompt: str, context: Optional[Dict] = None) -> GenerationResult:
        """
        Generate text with pre-output hallucination prevention
        """
        # Stage 1: Guard against injection
        safety = self.guard.verify_prompt(prompt, context)
        if not safety["is_safe"]:
            return GenerationResult(
                response=f"Blocked: {safety['blocked_reason']}",
                hallucination_risk=1.0,
                prevention_events=[{"type": "blocked", "reason": safety["blocked_reason"]}],
                token_path=[],
                cryptographic_attestation=None
            )
        
        # Stage 2: Token-by-token generation with prevention
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        generated_ids = []
        prevention_events = []
        hallucination_risks = []
        
        for step in range(self.max_tokens):
            # Get next token probabilities
            with torch.no_grad():
                outputs = self.model(input_ids)
                logits = outputs.logits[0, -1, :]
                probs = torch.softmax(logits / self.temperature, dim=-1).numpy()
            
            # Predict hallucination risk for each possible token
            token_risks = self.predictor.predict_next_token_safety(
                token_sequence=generated_ids,
                probability_distribution=probs,
                prompt=prompt
            )
            
            # Find safe tokens (hallucination risk below threshold)
            safe_tokens = [
                (idx, data) for idx, data in token_risks.items()
                if data["hallucination_risk_if_chosen"] < self.risk_threshold
            ]
            
            if not safe_tokens:
                # No safe path - abort generation
                prevention_events.append({
                    "step": step,
                    "type": "abort",
                    "reason": "all_tokens_unsafe",
                    "token_risks": token_risks
                })
                break
            
            # Choose safest token with reasonable probability
            best_token_idx, best_token_data = max(
                safe_tokens,
                key=lambda x: x[1]["probability"] * (1 - x[1]["hallucination_risk_if_chosen"])
            )
            
            # Record prevention if we avoided a hallucination
            if best_token_data["hallucination_risk_if_chosen"] > 0.2:
                prevention_events.append({
                    "step": step,
                    "type": "prevention",
                    "chosen_token": self.tokenizer.decode([best_token_idx]),
                    "avoided_risk": best_token_data["hallucination_risk_if_chosen"],
                    "alternatives": [
                        {"token": self.tokenizer.decode([idx]), "risk": data["hallucination_risk_if_chosen"]}
                        for idx, data in list(token_risks.items())[:5]
                    ]
                })
            
            # Append token
            generated_ids.append(best_token_idx)
            hallucination_risks.append(best_token_data["hallucination_risk_if_chosen"])
            
            # Check for EOS
            if best_token_idx == self.tokenizer.eos_token_id:
                break
            
            # Update input for next iteration
            input_ids = torch.cat([input_ids, torch.tensor([[best_token_idx]])], dim=1)
        
        # Decode response
        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        # Stage 3: Post-generation verification
        final_risk = np.mean(hallucination_risks) if hallucination_risks else 0.0
        
        # Stage 4: Cryptographic attestation
        attestation = self.issuer.issue_attestation(
            prompt=prompt,
            response=response,
            risk_score=final_risk,
            prevention_events=prevention_events
        )
        
        return GenerationResult(
            response=response,
            hallucination_risk=final_risk,
            prevention_events=prevention_events,
            token_path=[self.tokenizer.decode([idx]) for idx in generated_ids],
            cryptographic_attestation=attestation
        )
    
    def verify_response(self, prompt: str, response: str) -> Dict:
        """
        Verify existing response for hallucinations (post-hoc)
        """
        # Extract claims
        claims = self._extract_claims(response)
        
        # Verify each claim
        verified = []
        hallucinations = []
        
        for claim in claims:
            # Check against model's own probability
            verification = self._verify_claim(claim, prompt)
            
            if verification["is_consistent"]:
                verified.append(claim)
            else:
                hallucinations.append({
                    "claim": claim,
                    "confidence": verification["confidence"],
                    "contradiction": verification["contradiction"]
                })
        
        return {
            "total_claims": len(claims),
            "verified_count": len(verified),
            "hallucination_count": len(hallucinations),
            "hallucination_rate": len(hallucinations) / len(claims) if claims else 0,
            "hallucinations": hallucinations,
            "cryptographic_proof": self.issuer.issue_verification(verified, hallucinations)
        }
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text"""
        # Simple sentence splitting - use NLP library in production
        sentences = text.split('.')
        return [s.strip() for s in sentences if len(s.strip()) > 10 and '?' not in s]
    
    def _verify_claim(self, claim: str, context: str) -> Dict:
        """Verify a claim against model's knowledge"""
        # This is simplified - production uses RAG with trusted sources
        prompt = f"Context: {context}\nClaim: {claim}\nIs this claim true? Answer yes or no:"
        
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model.generate(input_ids, max_new_tokens=5)
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        is_true = "yes" in response.lower() and "no" not in response.lower()
        
        return {
            "is_consistent": is_true,
            "confidence": 0.8 if is_true else 0.3,
            "contradiction": not is_true
        }
