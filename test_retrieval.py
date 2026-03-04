import asyncio
from app.core.qa_chain import AuraQAChain
import re

def main():
    chain = AuraQAChain()
    query = "What are the most prevalent mutations in HHT?"
    
    print(f"\\nTest: Generating answer for query: '{query}'")
    answer, _ = chain.query(query)
    
    # Extract PMIDs strictly from the new formatted citation blocks
    pmids = set(re.findall(r'\[PMID:\s*(\d+)\]', answer))
    
    print("\\n--- Final LLM Response ---")
    print(answer)
    print(f"\\n--- Citation Statistics ---")
    print(f"Unique Articles Cited: {len(pmids)}")
    print(f"Cited PMIDs: {list(pmids)}")

if __name__ == "__main__":
    main()
