import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.query_parser import QueryParser

def run_tests():
    parser = QueryParser()
    
    test_queries = [
        # 1. Broadly ambiguous acronym
        "What does APC do?",
        
        # 2. Straightforward intent with metadata
        "Show me recent human studies on ACVRL1 mutations from 2022.",
        
        # 3. Conversational / messy query (should strip out fluff and optimize BM25 density)
        "Hi there, I am wondering if you can tell me about the specific liver complications that happen when someone has hereditary hemorrhagic telangiectasia?"
    ]
    
    for i, test_query in enumerate(test_queries, 1):
        print(f"\n--- Test {i} ---")
        print(f"Raw Query: {test_query}")
        
        result = parser.parse(test_query)
        
        print("\nParsed Result:")
        # Dump the Pydantic model to a clean dictionary
        for k, v in result.model_dump().items():
            print(f"  {k}: {v}")
            
if __name__ == "__main__":
    run_tests()
