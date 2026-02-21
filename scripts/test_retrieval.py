import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.vector_store import AuraVectorStore

def test_retrieval():
    print("\nInitializing Vector Store...")
    vector_store = AuraVectorStore()
    
    query = "What are the common genetic mutations associated with Hereditary Hemorrhagic Telangiectasia?"
    print(f"\nSearching for: '{query}'")
    print("-" * 50)
    
    # Test Index A (Abstracts)
    print("\n--- Top 3 Results from INDEX A (Abstracts) ---")
    results_a = vector_store.collection_a.similarity_search_with_score(query, k=3)
    for i, (doc, score) in enumerate(results_a):
        print(f"\nResult {i+1} (Distance: {score:.4f}):")
        print(f"PMID: {doc.metadata.get('pmid')}")
        print(f"Title: {doc.metadata.get('title')}")
        print(f"Content Snippet: {doc.page_content[:200]}...")
        
    # Test Index B (Body Text)
    print("\n--- Top 3 Results from INDEX B (Body Text chunks) ---")
    results_b = vector_store.collection_b.similarity_search_with_score(query, k=3)
    for i, (doc, score) in enumerate(results_b):
        print(f"\nResult {i+1} (Distance: {score:.4f}):")
        print(f"PMID: {doc.metadata.get('pmid')}")
        print(f"Section: {doc.metadata.get('Header 2', 'N/A')} > {doc.metadata.get('Header 3', 'N/A')}")
        print(f"Content Snippet: {doc.page_content[:200]}...")

if __name__ == "__main__":
    test_retrieval()
