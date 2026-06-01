"""
FastAPI server for AntiSIM service
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn

from antisim.core import AntiSIM

app = FastAPI(title="AntiSIM v4.0 ABYSS", version="4.0.0")

# Initialize engine
engine = AntiSIM()

class GenerateRequest(BaseModel):
    prompt: str
    context: Optional[Dict] = None
    verify_only: bool = False

class GenerateResponse(BaseModel):
    response: str
    hallucination_risk: float
    prevention_events: list
    attestation: Optional[str]

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "4.0.0"}

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate text with hallucination prevention"""
    result = engine.generate_safe(request.prompt, request.context)
    
    return GenerateResponse(
        response=result.response,
        hallucination_risk=result.hallucination_risk,
        prevention_events=result.prevention_events,
        attestation=result.cryptographic_attestation
    )

@app.post("/verify")
async def verify(prompt: str, response: str):
    """Verify existing response for hallucinations"""
    result = engine.verify_response(prompt, response)
    return result

def main():
    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
