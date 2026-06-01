"""
Real prompt injection and jailbreak protection
"""

import re
from typing import Dict, List, Optional
import hashlib


class AntiSIMGuard:
    """Multi-layer prompt protection"""
    
    def __init__(self):
        self.patterns = self._compile_patterns()
        
    def verify_prompt(self, prompt: str, context: Optional[Dict] = None) -> Dict:
        """
        Verify prompt safety with multiple layers
        """
        # Layer 1: Pattern matching
        pattern_risk, matched_patterns = self._check_patterns(prompt)
        
        # Layer 2: Length and structure anomalies
        structural_risk = self._check_anomalies(prompt)
        
        # Layer 3: Context consistency (if context provided)
        context_risk = self._check_context(prompt, context) if context else 0.0
        
        total_risk = max(pattern_risk, structural_risk, context_risk)
        
        return {
            "is_safe": total_risk < 0.6,
            "risk_score": total_risk,
            "blocked_reason": self._get_reason(pattern_risk, structural_risk, context_risk),
            "matched_patterns": matched_patterns,
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()
        }
    
    def _compile_patterns(self) -> List[re.Pattern]:
        """Compile injection patterns"""
        return [
            re.compile(r"(?i)ignore (all|previous|above) instructions"),
            re.compile(r"(?i)you are (now|going to be) (dan|jailbreak)"),
            re.compile(r"(?i)system prompt:?"),
            re.compile(r"(?i)new (rule|instruction):"),
            re.compile(r"(?i)pretend (you are|to be)"),
            re.compile(r"(?i)no (restrictions|limits|boundaries)"),
            re.compile(r"(?i)jailbreak this (model|system)"),
            re.compile(r"(?i)bypass (safety|security|guard)"),
            re.compile(r"[^\x00-\x7F]{3,}"),  # Unusual Unicode sequences
        ]
    
    def _check_patterns(self, prompt: str) -> tuple:
        """Check for known malicious patterns"""
        matches = []
        for pattern in self.patterns:
            if pattern.search(prompt):
                matches.append(pattern.pattern)
        
        risk = min(0.3 * len(matches), 1.0)
        return risk, matches
    
    def _check_anomalies(self, prompt: str) -> float:
        """Check for structural anomalies"""
        risk = 0.0
        
        # Very long prompt
        if len(prompt) > 2000:
            risk += 0.3
        
        # Repetition
        if len(set(prompt.split())) < len(prompt.split()) * 0.3:
            risk += 0.2
        
        # Unusual character ratio
        non_alnum = sum(1 for c in prompt if not c.isalnum() and not c.isspace())
        if non_alnum / len(prompt) > 0.3:
            risk += 0.2
        
        return min(risk, 1.0)
    
    def _check_context(self, prompt: str, context: Dict) -> float:
        """Check consistency with expected context"""
        # Simplified - production would use embeddings
        risk = 0.0
        
        if "expected_topic" in context:
            if context["expected_topic"].lower() not in prompt.lower():
                risk += 0.4
        
        return min(risk, 1.0)
    
    def _get_reason(self, pattern_risk: float, structural_risk: float, context_risk: float) -> str:
        """Generate human-readable block reason"""
        if pattern_risk > 0.5:
            return "detected_injection_pattern"
        elif structural_risk > 0.5:
            return "structural_anomaly_detected"
        elif context_risk > 0.5:
            return "context_mismatch"
        else:
            return "passed_checks"
