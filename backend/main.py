from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from rag_engine.rag_pipeline import (
    retrieve_candidates,
    augment_with_context,
    generate_response
)

app = FastAPI(title="HR Assistant Chatbot", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    query: str
    top_k: int = 3

# Output model for each candidate
class CandidateOut(BaseModel):
    id: int
    name: str
    skills: List[str]
    experience_years: int
    projects: List[str]
    availability: str
    match_score: float

# Final response model
class ChatResponse(BaseModel):
    answer: str
    candidates: List[CandidateOut]

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        candidates = retrieve_candidates(request.query, request.top_k)
        if not candidates:
            return ChatResponse(answer="No matching employees found.", candidates=[])
        
        context = augment_with_context(request.query, candidates)
        response = generate_response(context)

        return ChatResponse(answer=response, candidates=candidates)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Reuse your search endpoint as-is
@app.get("/employees/search", response_model=List[CandidateOut])
def search_employees(skill: str = Query(None), available: bool = True):
    from rag_engine.rag_pipeline import EMPLOYEES  # Optional: centralize access
    filtered = []
    for emp in EMPLOYEES:
        if skill and skill not in emp["skills"]:
            continue
        if available and emp["availability"].lower() != "available":
            continue
        emp["match_score"] = 0.0  # Default for filter results
        filtered.append(emp)
    return filtered
