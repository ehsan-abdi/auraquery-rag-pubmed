import logging
from typing import List, Dict, Any, Tuple
import datetime

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.db.vector_store import AuraVectorStore
from app.core.query_parser import QueryParser, ParsedQuery

logger = logging.getLogger(__name__)

class AuraRetriever:
    """
    Implements a High-Performance Two-Stage Hybrid Retrieval Pipeline.
    Stage 1: Index A (Abstracts) -> Selects Top unique PMIDs
    Stage 2: Index B (Body Text) -> Drills into specifically selected PMIDs
    Stage 3: Custom Reranking (Methodologies, Recency)
    Stage 4: Diversity Filtering (Max chunks per paper)
    """

    def __init__(self):
        self.vector_store = AuraVectorStore()
        self.query_parser = QueryParser()
        
        # Adjustable Hyperparameters
        self.abstract_top_n = 50
        self.chunk_top_k = 40
        self.max_chunks_per_article = 3
        self.target_return_size = 15

    def retrieve(self, raw_query: str) -> List[Document]:
        """The main orchestration pipeline."""
        logger.info(f"Starting retrieval pipeline for query: '{raw_query}'")
        
        # 1. Parse Query
        parsed_query = self.query_parser.parse(raw_query)
        
        # Print parsed query to terminal for inspection
        print("\n" + "-"*60)
        print("🔍 PARSED QUERY INSPECTION:")
        for k, v in parsed_query.model_dump().items():
            print(f"  {k}: {v}")
        print("-" * 60 + "\n")

        if parsed_query.clarification_required:
            logger.warning(f"Ambiguous query detected: {parsed_query.clarification_required}")
            # If the user asks an ambiguous question, we should ideally bounce this back up to the API.
            # For the retriever, we will return a fake Document containing the clarification message for the LLM.
            return [Document(
                page_content=f"System Alert: Do not answer the user's question. Instead, ask them this clarification: {parsed_query.clarification_required}",
                metadata={"type": "clarification"}
            )]
            
        search_term = parsed_query.optimized_query or raw_query
        
        # 2. Stage 1: Candidate Article Retrieval (Index A)
        candidate_pmids = self._stage_1_abstract_search(search_term, parsed_query)
        if not candidate_pmids:
            logger.warning("No candidate abstracts found. Aborting retrieval.")
            return []
            
        # 3. Stage 2: Chunk-Level Retrieval (Index B)
        raw_chunks = self._stage_2_chunk_search(search_term, candidate_pmids)
        if not raw_chunks:
            logger.warning("No body chunks found for candidate PMIDs.")
            return []
            
        # 4. Stage 3: Metadata-Aware Reranking
        reranked_chunks = self._stage_3_rerank(raw_chunks, parsed_query)
        
        # 5. Stage 4: Diversity Filtering
        final_chunks = self._stage_4_diversity_filter(reranked_chunks)
        
        logger.info(f"Retrieval complete. Yielding {len(final_chunks)} perfectly curated chunks.")
        return final_chunks

    def _build_chroma_filter(self, parsed_query: ParsedQuery) -> dict:
        """Translates the Pydantic MetadataFilters into a ChromaDB-compliant dict."""
        if not parsed_query.metadata_filters:
            return {}
            
        filters = {}
        meta = parsed_query.metadata_filters
        
        if meta.publication_year:
            # Note: in chunking we saved it as 'pub_year'
            filters["pub_year"] = meta.publication_year
        if meta.first_author_lastname:
            # Preserve exact casing from the LLM (e.g. for Álvarez-Hernández or MacDonald)
            filters["first_author_lastname"] = meta.first_author_lastname
        if meta.is_human is not None:
            filters["is_human"] = meta.is_human
        if meta.is_animal is not None:
            filters["is_animal"] = meta.is_animal
        
        # We can't easily filter list fields like mesh_major_terms in Chroma via direct match
        # if they were stringified, but we'll stick to scalars.
        return filters

    def _stage_1_abstract_search(self, search_term: str, parsed_query: ParsedQuery) -> List[str]:
        """Performs Dense Search on Index A (Abstracts) to derive candidate PMIDs."""
        logger.info(f"Executing Stage 1 Search on Index A. Term: '{search_term}'")
        
        # Build strict filters if extracted by the LLM
        stage_1_filter = self._build_chroma_filter(parsed_query)
        if stage_1_filter:
            logger.info(f"Applying strict Stage 1 ChromaDB metadata filter: {stage_1_filter}")
            
        kwargs = {"query": search_term, "k": self.abstract_top_n * 2}
        if stage_1_filter:
            if len(stage_1_filter) == 1:
                kwargs["filter"] = stage_1_filter
            else:
                kwargs["filter"] = {"$and": [{k: v} for k, v in stage_1_filter.items()]}
        
        try:
            results = self.vector_store.collection_a.similarity_search_with_relevance_scores(**kwargs)
        except Exception as e:
            logger.error(f"Stage 1 search failed with filter {stage_1_filter}: {e}")
            # Failsafe: drop the filter and try again if it was too restrictive / threw an error
            results = self.vector_store.collection_a.similarity_search_with_relevance_scores(
                query=search_term, k=self.abstract_top_n * 2
            )
        
        # Extract unique PMIDs
        unique_pmids = []
        for doc, score in results:
            pmid = doc.metadata.get("pmid")
            if pmid and pmid not in unique_pmids:
                unique_pmids.append(pmid)
                if len(unique_pmids) == self.abstract_top_n:
                    break
                    
        logger.info(f"Stage 1 complete. Isolated {len(unique_pmids)} candidate PMIDs.")
        return unique_pmids

    def _stage_2_chunk_search(self, search_term: str, candidate_pmids: List[str]) -> List[Tuple[Document, float]]:
        """Restricts deep body search strictly to the subset of candidate PMIDs."""
        logger.info("Executing Stage 2 Deep Search on Index B.")
        
        filter_dict = {
            "pmid": {"$in": candidate_pmids}
        }
        
        # Dense search over isolated chunks
        dense_results = self.vector_store.collection_b.similarity_search_with_relevance_scores(
            query=search_term,
            k=self.chunk_top_k,
            filter=filter_dict
        )
        
        # Optional: In-Memory BM25 RRF could be injected here for pure accuracy.
        # For now, we utilize the dense scores as the base.
        return dense_results

    def _stage_3_rerank(self, scored_docs: List[Tuple[Document, float]], parsed_query: ParsedQuery) -> List[Tuple[Document, float]]:
        """Applies algorithmic boosts to favor RCTs, robust methodologies, and recent papers."""
        logger.info("Executing Stage 3 Custom Reranking.")
        reranked = []
        
        current_year = datetime.datetime.now().year
        
        for doc, base_score in scored_docs:
            meta = doc.metadata
            final_score = base_score
            
            # --- PUBLICATION TYPE WEIGHTING ---
            pub_types = meta.get("publication_types", "") # Stored as a string representation of a list
            if "Meta-Analysis" in pub_types:
                final_score += 1.00
            elif "Systematic Review" in pub_types:
                final_score += 0.95
            elif "Guideline" in pub_types or "Practice Guideline" in pub_types:
                final_score += 0.90
            elif "Randomized Controlled Trial" in pub_types:
                final_score += 0.85
            elif "Clinical Trial" in pub_types:
                final_score += 0.75
            elif "Review" in pub_types:
                final_score += 0.55
            elif "Case Reports" in pub_types:
                final_score += 0.30
            else:
                final_score += 0.60 # Standard Journal Article fallback
                
            # --- SECTION WEIGHTING (Index B) ---
            h2 = meta.get("Header 2", "").lower()
            if "result" in h2:
                final_score += 1.5
            elif "conclusion" in h2:
                final_score += 1.5
            elif "method" in h2:
                final_score += 1.0
            elif "discussion" in h2:
                final_score += 0.5
            elif "introduction" in h2 or "background" in h2:
                final_score -= 0.5
                
            # --- RECENCY BOOST ---
            pub_year = meta.get("pub_year", meta.get("publication_year"))
            if pub_year and pub_year != "Unknown":
                try:
                    year_diff = current_year - int(pub_year)
                    if year_diff >= 0:
                        import math
                        # Reduced weight from 0.5 to 0.25 to prevent recent reviews overtaking older high-quality RCTs
                        recency_weight = 0.25 * math.exp(-year_diff / 8)
                        final_score += recency_weight
                except ValueError:
                    pass
                    
            # Inject the final calculated score for debugging / transparency
            doc.metadata["aura_rerank_score"] = final_score
            doc.metadata["aura_base_vector_score"] = base_score
            reranked.append((doc, final_score))
            
        # Sort aggressively by our new custom algorithmic score (Descending)
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked

    def _stage_4_diversity_filter(self, ranked_docs: List[Tuple[Document, float]]) -> List[Document]:
        """Enforces max_chunks per PMID to prevent review articles from dominating the LLM context."""
        logger.info("Executing Stage 4 Diversity Filtering.")
        final_list = []
        pmid_counts = {}
        
        for doc, score in ranked_docs:
            pmid = doc.metadata.get("pmid")
            
            # Initialize count
            if pmid not in pmid_counts:
                pmid_counts[pmid] = 0
                
            # Check maximum constraint
            if pmid_counts[pmid] >= self.max_chunks_per_article:
                continue # Skip to next document
                
            # Add to set
            final_list.append(doc)
            pmid_counts[pmid] += 1
            
            # Check terminal constraint
            if len(final_list) >= self.target_return_size:
                break
                
        return final_list
