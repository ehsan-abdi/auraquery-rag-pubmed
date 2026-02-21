import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.retriever import AuraRetriever

def run_retrieval_test():
    retriever = AuraRetriever()
    
    # 1. Provide a complex clinical query
    query = "What is the efficacy of Bevacizumab in treating severe epistaxis in HHT patients?"
        
    print("\n" + "="*80)
    print("AURAQUERY RETRIEVAL ENGINE TEST")
    print("="*80)
    print(f"Executing deep hybrid retrieval for: '{query}'")
    print("-" * 80 + "\n")
    
    final_chunks = retriever.retrieve(query)
    
    for i, doc in enumerate(final_chunks, 1):
        meta = doc.metadata
        print(f"RANK: {i} | PMID: {meta.get('pmid')} | YEAR: {meta.get('publication_year')} | SEC: {meta.get('Header 2', 'N/A')}")
        print(f"RERANK SCORE: {meta.get('aura_rerank_score', 0):.4f} (Base Vector: {meta.get('aura_base_vector_score', 0):.4f})")
        print(f"PUB TYPES: {meta.get('publication_types', 'N/A')}")
        
        # Print a tiny clean snippet to verify content logic
        snippet = doc.page_content.replace('\n', ' ')
        print(f"SNIPPET: {snippet[:150]}...")
        print("-" * 80)

if __name__ == "__main__":
    run_retrieval_test()
