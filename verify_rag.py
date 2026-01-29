
import os
import sys

# Mock env var if not present (simulate what checking the file does)
# But here we expect the shell to pass it. simpler logging.

print(f"DEBUG: Initial OPENAI_API_KEY in env: {os.environ.get('OPENAI_API_KEY', 'Not Set')[:10]}...")

try:
    from backend.services.rag_service import RAGService
    
    print("Initializing RAG Service...")
    rag = RAGService()
    
    print("Testing _default_embedding...")
    # This should trigger the dynamic env check
    embedding = rag._default_embedding("This is a test sentence for embedding generation.")
    
    if embedding and len(embedding) == 1536:
        print("SUCCESS: Embedding generated with length 1536")
        sys.exit(0)
    else:
        print(f"FAILURE: Embedding generated but unexpected length: {len(embedding) if embedding else 'None'}")
        sys.exit(1)

except Exception as e:
    print(f"CRITICAL FAILURE: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
