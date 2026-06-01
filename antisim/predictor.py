"""
Token-level hallucination predictor
Trains on hallucination patterns to predict unsafe paths
"""

import numpy as np
from typing import List, Dict, Tuple
from sklearn.ensemble import RandomForestClassifier
import pickle
import hashlib


class TokenHallucinationPredictor:
    """
    Predicts if a token will lead to hallucination based on:
    1. Probability entropy
    2. Factual consistency
    3. Pattern matching
    4. Context contradiction
    """
    
    def __init__(self, model_path: str = None):
        if model_path:
            with open(model_path, 'rb') as f:
                self.classifier = pickle.load(f)
        else:
            # Initialize with reasonable defaults
            self.classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        
        self.trained = model_path is not None
        
    def predict_next_token_safety(self, 
                                   token_sequence: List[int],
                                   probability_distribution: np.ndarray,
                                   prompt: str) -> Dict[int, Dict]:
        """
        Predict hallucination risk for each possible next token
        
        Returns:
            Dict mapping token index to:
            - hallucination_risk_if_chosen: float 0-1
            - probability: original probability
            - features: extracted features for this token
        """
        predictions = {}
        
        for token_idx, prob in enumerate(probability_distribution):
            # Extract features for this token path
            features = self._extract_features(
                token_sequence + [token_idx],
                probability_distribution,
                prompt
            )
            
            # Predict risk if trained, else use heuristic
            if self.trained:
                risk = float(self.classifier.predict_proba([features])[0][1])
            else:
                risk = self._heuristic_risk(features)
            
            predictions[token_idx] = {
                "token_id": token_idx,
                "probability": float(prob),
                "hallucination_risk_if_chosen": risk,
                "features": features
            }
        
        return predictions
    
    def _extract_features(self, 
                          token_sequence: List[int],
                          probability_distribution: np.ndarray,
                          prompt: str) -> List[float]:
        """Extract features for hallucination prediction"""
        
        # Feature 1: Entropy of distribution
        entropy = -np.sum(probability_distribution * np.log(probability_distribution + 1e-8))
        max_entropy = np.log(len(probability_distribution))
        entropy_norm = entropy / max_entropy
        
        # Feature 2: Probability rank of this token
        sorted_probs = np.sort(probability_distribution)[::-1]
        rank = np.where(sorted_probs == probability_distribution[0])[0][0] if len(token_sequence) > 0 else 0
        rank_norm = rank / len(probability_distribution)
        
        # Feature 3: Token frequency (rare tokens = higher risk)
        # Simplified - use token id modulo 1000 as proxy for frequency
        token_freq = 1.0 - (token_sequence[-1] % 1000) / 1000 if token_sequence else 0.5
        
        # Feature 4: Sequence length
        seq_len_norm = min(len(token_sequence) / 100, 1.0)
        
        # Feature 5: Prompt complexity (simple heuristic)
        prompt_complexity = min(len(prompt.split()) / 50, 1.0)
        
        # Feature 6: Sudden probability drop from previous token
        prob_drop = 0.0  # Would need previous distribution
        
        # Feature 7: Contradiction indicator (if trained)
        contradiction = 0.0
        
        return [
            entropy_norm,
            rank_norm,
            token_freq,
            seq_len_norm,
            prompt_complexity,
            prob_drop,
            contradiction
        ]
    
    def _heuristic_risk(self, features: List[float]) -> float:
        """Fallback heuristic when model not trained"""
        # Simple weighted heuristic
        weights = [0.3, 0.2, 0.15, 0.1, 0.1, 0.1, 0.05]
        risk = sum(f * w for f, w in zip(features, weights))
        return min(max(risk, 0.0), 1.0)
    
    def train(self, training_data: List[Tuple[List[int], np.ndarray, str, bool]]):
        """
        Train predictor on labeled hallucination data
        
        Args:
            training_data: List of (token_sequence, probability_distribution, prompt, is_hallucination)
        """
        X = []
        y = []
        
        for seq, probs, prompt, is_hallucination in training_data:
            features = self._extract_features(seq, probs, prompt)
            X.append(features)
            y.append(is_hallucination)
        
        self.classifier.fit(X, y)
        self.trained = True
        
        # Save model
        with open("antisim_model.pkl", 'wb') as f:
            pickle.dump(self.classifier, f)
        
        return {"accuracy": self.classifier.score(X, y)}
