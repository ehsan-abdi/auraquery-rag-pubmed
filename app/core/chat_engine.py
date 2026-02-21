import logging
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.utils.config import settings
from app.core.qa_chain import AuraQAChain

logger = logging.getLogger(__name__)

REFORMULATION_SYSTEM_PROMPT = """You are an expert query reformulator for a biomedical hybrid search engine.
Your sole purpose is to take a conversational user input and rewrite it into a standalone, highly specific search query.

CRITICAL RULES:
1. Look at the immediate Chat History to resolve any pronouns (e.g., "it", "they", "this treatment", "these papers", "their findings") or implicit context in the User's newest Input.
2. The output MUST be a standalone string that could be typed into Google Scholar without the listener needing to know the chat history.
3. DO NOT answer the user's question. ONLY output the rewritten query.
4. If the generic User Input does not require history to be understood (e.g., "What is HHT?"), just output the original input unchanged.

🔥 RULE 5 - MANDATORY PMID PRESERVATION 🔥:
If the user's follow-up question refers to specific papers, authors, or findings mentioned by the AI in the PREVIOUS TURN (e.g., "Can you summarize their main findings?", "Tell me more about the first paper"), you MUST extract ALL [PMID: XXXXXX] from the AI's historical answer and explicitly append them to your rewritten query in the format 'PMID: XXXXXX'.

Example 1:
History: User: "Does Bevacizumab help?" -> AI: "Yes, it reduces epistaxis."
New Input: "What are its side effects?"
Output: "What are the side effects of Bevacizumab in HHT patients?"

Example 2:
History: User: "Are there papers on loss-of-function?" -> AI: "Yes, Viteri-Noël discusses ENG mutations [PMID: 40648782] and Baysal discusses ACVRL1 [PMID: 31594285]."
New Input: "Can you summarize their findings?"
Output: "Can you summarize the findings of Viteri-Noël [PMID: 40648782] and Baysal [PMID: 31594285] regarding loss-of-function mutations?"
"""

class AuraChatEngine:
    """
    Wraps the Phase 3 RAG pipeline in a conversational memory layer.
    Intercepts the user query, uses an LLM to rewrite it based on chat history, 
    and then passes the standalone query to the retrieval engine.
    """
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.qa_chain = AuraQAChain()
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.0 # Strict determinism for reformulation
        )
        
        # Simulating basic in-memory history for local development.
        # In production (FastAPI), this will map to Session IDs using RunnableWithMessageHistory.
        self.chat_history: List[Any] = []
        
        self.reformulation_prompt = ChatPromptTemplate.from_messages([
            ("system", REFORMULATION_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Rewrite this input to be a standalone query: {input}")
        ])
        
    def _reformulate_query(self, user_input: str) -> str:
        """Uses the LLM to resolve pronouns and contextualize the user query."""
        if not self.chat_history:
            return user_input # No history to resolve against
            
        logger.info(f"Reformulating query based on history: '{user_input}'")
        chain = self.reformulation_prompt | self.llm
        
        response = chain.invoke({
            "history": self.chat_history,
            "input": user_input
        })
        
        rewritten_query = response.content.strip()
        logger.info(f"Rewritten Query: '{rewritten_query}'")
        return rewritten_query
        
    def chat(self, user_input: str) -> str:
        """
        The main interaction point for conversational RAG.
        1. Reformulate query
        2. Run RAG pipeline
        3. Save history
        4. Return answer
        """
        # 1. Reformulate
        standalone_query = self._reformulate_query(user_input)
        
        # 2. Add human message to history AFTER reformulation
        self.chat_history.append(HumanMessage(content=user_input))
        
        # 3. Execute the full Phase 3 QA Chain (Parse -> Retrieve -> Generation)
        # using the perfectly standalone query, so vector search doesn't break.
        answer = self.qa_chain.query(standalone_query)
        
        # 4. Save AI response to history
        self.chat_history.append(AIMessage(content=answer))
        
        # Trim history to prevent context bloat (keep last 6 interactions)
        if len(self.chat_history) > 12: 
            self.chat_history = self.chat_history[-12:]
            
        return answer
        
    def clear_history(self):
        """Wipes the current session memory."""
        self.chat_history = []
        logger.info("Chat history cleared.")
