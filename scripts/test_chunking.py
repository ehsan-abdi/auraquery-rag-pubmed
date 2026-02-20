import json
import logging
import os
from pprint import pprint
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.chunker import AuraChunker

def test_chunking():
    json_path = "data/raw/hht/20501893.json"
    
    with open(json_path, "r", encoding="utf-8") as f:
        article_data = json.load(f)

    chunker = AuraChunker(max_chunk_size=1000, chunk_overlap=200)
    
    print(f"Testing chunking on {json_path}")
    docs = chunker.process_article(article_data)
    
    index_a_chunks = docs.get("index_a", [])
    index_b_chunks = docs.get("index_b", [])
    
    print(f"\n--- INDEX A (Abstract) ---")
    print(f"Total chunks: {len(index_a_chunks)}")
    for i, chunk in enumerate(index_a_chunks):
        print(f" Chunk {i+1} Length: {len(chunk.page_content)}")
        print(f" Chunk {i+1} Metadata: {chunk.metadata}")
        
    print(f"\n--- INDEX B (Body) ---")
    print(f"Total chunks: {len(index_b_chunks)}")
    for i, chunk in enumerate(index_b_chunks[:3]):
        print(f" Chunk {i+1} Length: {len(chunk.page_content)}")
        print(f" Chunk {i+1} Metadata: {chunk.metadata}")
        print(f" Chunk {i+1} Content snippet: {chunk.page_content[:150]}...")
        
    print(f"...\n(showing first 3 of {len(index_b_chunks)} Index B chunks)")
    
    # Check max size violations
    max_size_violations = [c for c in index_b_chunks if len(c.page_content) > 1000]
    print(f"\nMax size violated chunks (>1000 chars): {len(max_size_violations)}")
    
    # Save the output to a JSON file for inspection
    output_path = "data/raw/hht/20501893_chunked_test.json"
    
    output_data = {
        "index_a": [{"page_content": c.page_content, "metadata": c.metadata} for c in index_a_chunks],
        "index_b": [{"page_content": c.page_content, "metadata": c.metadata} for c in index_b_chunks]
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)
        
    print(f"\nSaved full chunked output to {output_path}")

if __name__ == "__main__":
    test_chunking()
