import logging
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from pydantic import BaseModel, Field

from app.utils.config import settings
from app.core.retriever import AuraRetriever

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# System Prompt
# -----------------------------------------------------------------------
QA_SYSTEM_PROMPT = """You are AuraQuery, an expert biomedical AI assistant designed to answer highly complex medical questions using ONLY the provided verified literature.

You must answer the user's question accurately, directly, and comprehensively based explicitly on the Context Provided below.

CRITICAL RULES:
1. NO HALLUCINATION: If the context does not contain the answer, state clearly: "I cannot find sufficient evidence in the parsed literature to answer this question." Do not attempt to guess or use outside knowledge.
2. CITATIONS REQUIRED: Every distinct medical claim, statistic, or observation MUST be cited in-line using the exact metadata provided in each chunk's header.
   - You MUST include the PMID in every citation.
   - Use Harvard style format WITH the PMID: (First Author Last Name, Year) [PMID: XXXXXX] or just [PMID: XXXXXX] if author/year data is missing.
   - Example: "Bevacizumab drastically reduces epistaxis severity (Smith, 2022) [PMID: 123456]."
3. COMPREHENSIVE SYNTHESIS: You will be provided with multiple text chunks from diverse articles. You MUST synthesize information from MULTIPLE sources to provide a well-rounded and comprehensive answer. Do not just summarize the first article you see.
4. TONE: Professional, clinical, and objective. Avoid conversational filler (e.g., "Sure, I can help with that").

CONTEXT PROVIDED:
{context}
"""

class AuraQAChain:
    """
    Orchestrates the final LLM response.
    Takes a Raw Query, runs it through the Retriever, formats the retrieved chunks into a context block,
    and passes it to the LLM to generate a cited response.
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.retriever = AuraRetriever()
        
        # We use a standard generation model here, not structured output.
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1 # Very low temperature for factual RAG
        )
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", QA_SYSTEM_PROMPT),
            ("human", "{question}")
        ])

    def query(self, raw_query: str) -> str:
        """Executes the full RAG pipeline and returns the Markdown answer."""
        logger.info(f"Executing End-to-End RAG for query: {raw_query}")
        
        # 1. Retrieve the best Chunks
        docs = self.retriever.retrieve(raw_query)
        
        if not docs:
            return "No relevant literature could be found to answer this query."
            
        # 2. Check if the Retriever bounced back a Clarification Request
        if docs[0].metadata.get("type") == "clarification":
            return docs[0].page_content.replace("System Alert: Do not answer the user's question. Instead, ask them this clarification: ", "")
            
        # 3. Format the Context block
        formatted_context = self._format_docs(docs)
        logger.info(f"Context compiled. Sending {len(docs)} chunks to LLM payload.")
        
        # 4. Generate Answer
        chain = self.prompt_template | self.llm
        response = chain.invoke({
            "context": formatted_context,
            "question": raw_query
        })
        
        return response.content

    def _format_docs(self, docs: List[Document]) -> str:
        """Helper to inject cleanly formatted texts and metadata into the LLM prompt."""
        formatted_strings = []
        for i, doc in enumerate(docs, 1):
            meta = doc.metadata
            pmid = meta.get("pmid", "Unknown")
            year = meta.get("pub_year", meta.get("publication_year"))
            author = meta.get("first_author_lastname")
            
            # Smart citation assembly
            if author and year and author != "Unknown" and year != "Unknown":
                citation_header = f"[{i}] ({author}, {year}) [PMID: {pmid}]"
            elif author and author != "Unknown":
                citation_header = f"[{i}] ({author}) [PMID: {pmid}]"
            elif year and year != "Unknown":
                citation_header = f"[{i}] ({year}) [PMID: {pmid}]"
            else:
                 citation_header = f"[{i}] [PMID: {pmid}]"
            
            content = doc.page_content.strip()
            formatted_strings.append(f"{citation_header}\nCONTENT: {content}\n")
            
        return "\n".join(formatted_strings)
