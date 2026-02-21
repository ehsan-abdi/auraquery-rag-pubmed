import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as chat_router

# Configure root logger for the API
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = FastAPI(
    title="AuraQuery API",
    description="Backend RAG Retrieval Engine for the AuraQuery Frontend",
    version="1.0.0"
)

# Standard permissive CORS configuration for local development integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Expand this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the endpoint definitions
app.include_router(chat_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # Use standard host/port for local angular development
    uvicorn.run(app, host="0.0.0.0", port=8000)
