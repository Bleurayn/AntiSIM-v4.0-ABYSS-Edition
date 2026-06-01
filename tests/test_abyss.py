import pytest
from antisim.core import AntiSIM

def test_generation():
    engine = AntiSIM()
    result = engine.generate_safe("What is 2+2?")
    
    assert result.response is not None
    assert result.hallucination_risk >= 0
    assert isinstance(result.prevention_events, list)

def test_hallucination_prevention():
    engine = AntiSIM()
    
    # Question likely to cause hallucination
    result = engine.generate_safe("What is the population of Mars?")
    
    # Should express uncertainty rather than hallucinate
    assert "unknown" in result.response.lower() or "not" in result.response.lower()
    assert result.hallucination_risk < 0.5

def test_verification():
    engine = AntiSIM()
    
    verification = engine.verify_response(
        "What color is the sky?",
        "The sky is blue during the day."
    )
    
    assert "verified_count" in verification
    assert "hallucination_count" in verification
