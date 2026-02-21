from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.core.chat_engine import AuraChatEngine

router = APIRouter()
logger = logging.getLogger(__name__)

# Single instance for basic API serving. In production, consider dependency injection.
chat_engine = AuraChatEngine()

class QueryRequest(BaseModel):
    query: str
    session_id: str

class QueryResponse(BaseModel):
    answer: str

@router.post("/chat", response_model=QueryResponse)
def compute_chat_response(request: QueryRequest):
    """
    Core RAG Endpoint. Interacts with the ChatEngine to retrieve context
    and generate a formatted markdown response, complete with citations.
    """
    logger.info(f"API Request - Session: {request.session_id} | Query: {request.query}")
    try:
        # ChatEngine handles isolated session histories internally
        answer = chat_engine.chat(request.query, session_id=request.session_id)
        return QueryResponse(answer=answer)
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error processing query.")

@router.get("/health")
def health_check():
    """Simple health ping."""
    return {"status": "AuraQuery API is locked and loaded."}
