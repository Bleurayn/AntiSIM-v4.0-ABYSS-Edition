#!/usr/bin/env python3
"""
Demo of AntiSIM hallucination prevention
"""

from antisim.core import AntiSIM

def main():
    print("🚀 AntiSIM v4.0 ABYSS Demo\n")
    
    engine = AntiSIM()
    
    # Test cases
    test_cases = [
        "What is the capital of France?",
        "What is the population of Mars?",
        "Explain quantum computing in simple terms",
        "Who won the World Cup in 2024?"  # Future event - should show uncertainty
    ]
    
    for prompt in test_cases:
        print(f"\n📝 Prompt: {prompt}")
        print("-" * 50)
        
        result = engine.generate_safe(prompt)
        
        print(f"✅ Response: {result.response}")
        print(f"⚠️  Hallucination risk: {result.hallucination_risk:.2%}")
        
        if result.prevention_events:
            print(f"🛡️  Prevented {len(result.prevention_events)} potential hallucinations")
        
        print("-" * 50)

if __name__ == "__main__":
    main()
