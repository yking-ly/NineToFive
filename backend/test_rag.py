import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

try:
    from rag_service import RAGService
    
    print("Initializing RAG Service...")
    rag = RAGService()
    
    query = "What is the punishment for mob lynching?"
    print(f"\nQuery: {query}")
    
    context = rag.query_statutes(query)
    print(f"Retrieved: {len(context['bns'])} BNS docs, {len(context['ipc'])} IPC docs, {len(context['mapping'])} Mapping docs")
    
    answer = rag.generate_answer(query, context)
    print("\n--- Generated Answer ---\n")
    print(answer)
    print("\n------------------------")
    
except Exception as e:
    print(f"Test Failed: {e}")
