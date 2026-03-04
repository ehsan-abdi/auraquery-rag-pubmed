import asyncio
from app.core.query_parser import QueryParser

def main():
    parser = QueryParser()
    query = "how is the weather in London?"
    print(f"Testing query: '{query}'")
    
    parsed = parser.parse(query)
    print("\\n--- Parse Result ---")
    print(f"Clarification Required: {parsed.clarification_required}")
    print(f"Optimized Query: {parsed.optimized_query}")

if __name__ == "__main__":
    main()
