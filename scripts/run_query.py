import argparse
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.qa_chain import AuraQAChain

def main():
    parser = argparse.ArgumentParser(description="AuraQuery RAG Command Line Interface")
    parser.add_argument(
        "query", 
        type=str, 
        help="The medical question you want to ask AuraQuery."
    )
    
    args = parser.parse_args()
    user_query = args.query
    
    print("\n" + "="*80)
    print("🧠 AuraQuery AI - Processing Query...")
    print("="*80)
    print(f"QUESTION: {user_query}")
    print("-" * 80)
    
    qa_chain = AuraQAChain()
    
    try:
        # Run the full RAG pipeline (Parse -> Retrieve -> Format -> Generate)
        answer = qa_chain.query(user_query)
        
        print("\n🤖 ANSWER:\n")
        print(answer)
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to generate answer. Details: {e}")
        
if __name__ == "__main__":
    main()
