"""
FastAPI service for RAG retrieval.
Exposes endpoints for Kleiber to query the vector store.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.retriever import ContextRetriever

app = FastAPI(
    title="Toscanini RAG API",
    description="Retrieval API for augmenting context generation with documentation",
    version="1.0.0"
)

# Enable CORS for Kleiber to call this service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize retriever (loads embedding model on startup)
retriever = None


@app.on_event("startup")
async def startup_event():
    """Load the embedding model on startup."""
    global retriever
    print("Loading RAG retriever...")
    retriever = ContextRetriever()
    print("RAG retriever ready")


class RetrieveRequest(BaseModel):
    """Request for generic retrieval."""
    query: str
    source_types: Optional[List[str]] = None
    top_k: int = 5


class RetrieveForContextRequest(BaseModel):
    """Request for context-aware retrieval (optimized for Kleiber)."""
    user_input: str


class ChunkResponse(BaseModel):
    """Individual chunk in response."""
    content: str
    title: str
    source_url: str
    source_type: str
    section: str
    similarity: float


class RetrieveResponse(BaseModel):
    """Response for generic retrieval."""
    chunks: List[dict]


class RetrieveForContextResponse(BaseModel):
    """Response for context-aware retrieval."""
    formatted_context: str
    raw: dict


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "retriever_loaded": retriever is not None}


@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(request: RetrieveRequest):
    """
    Generic retrieval endpoint.

    Query the vector store with a text query and optional filters.
    """
    if retriever is None:
        raise HTTPException(status_code=503, detail="Retriever not initialized")

    try:
        results = retriever.retrieve(
            query=request.query,
            source_types=request.source_types,
            top_k=request.top_k
        )
        return {"chunks": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retrieve-for-context", response_model=RetrieveForContextResponse)
async def retrieve_for_context(request: RetrieveForContextRequest):
    """
    Context-aware retrieval endpoint (optimized for Kleiber).

    Takes user input (combined answers from Kleiber's 18 questions)
    and returns categorized documentation chunks ready for prompt injection.
    """
    if retriever is None:
        raise HTTPException(status_code=503, detail="Retriever not initialized")

    try:
        # Retrieve categorized results
        results = retriever.retrieve_for_context_generation(request.user_input)

        # Format for prompt injection
        formatted = retriever.format_for_prompt(results)

        return {
            "formatted_context": formatted,
            "raw": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
