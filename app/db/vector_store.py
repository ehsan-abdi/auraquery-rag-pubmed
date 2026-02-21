import logging
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from app.utils.config import settings

logger = logging.getLogger(__name__)

class AuraVectorStore:
    """
    Decoupled database wrapper for ChromaDB.
    Handles embedding and retrieval directly from local collections,
    abstracting away database-specific logic from the rest of the application.
    """

    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        # Initialize the OpenAI Embeddings instance here
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            api_key=settings.OPENAI_API_KEY
        )
        
        self.persist_directory = str(settings.CHROMA_DB_DIR)
        
        # Initialize connection to both index collections
        self.collection_a = self._init_collection("index_a_abstracts")
        self.collection_b = self._init_collection("index_b_bodies")
        
        logger.info(f"AuraVectorStore initialized pointing to {self.persist_directory}")

    def _init_collection(self, collection_name: str) -> Chroma:
        """Initializes or connects to a specific Chroma collection."""
        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def add_abstracts(self, documents: List[Document]) -> List[str]:
        """Adds a batch of abstract documents to Index A."""
        if not documents:
            return []
        ids = self.collection_a.add_documents(documents)
        logger.info(f"Added {len(ids)} documents to Index A.")
        return ids

    def add_body_chunks(self, documents: List[Document]) -> List[str]:
        """Adds a batch of body chunks to Index B."""
        if not documents:
            return []
        ids = self.collection_b.add_documents(documents)
        logger.info(f"Added {len(ids)} documents to Index B.")
        return ids
    
    def fetch_abstracts_by_pmid(self, pmid: str) -> List[Document]:
        """Check if a PMID already exists in Index A to avoid duplicate embeddings via the 'where' filter."""
        # Chroma allows native fetching by metadata matching
        results = self.collection_a.get(where={"pmid": pmid})
        # Unpack the underlying records into LangChain Documents
        if not results or not results.get("ids"):
            return []
            
        docs = []
        for i in range(len(results["ids"])):
            doc = Document(
                page_content=results["documents"][i],
                metadata=results["metadatas"][i]
            )
            docs.append(doc)
        return docs
