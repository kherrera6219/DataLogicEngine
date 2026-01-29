import asyncio
import uuid
import sys
import os

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models import ChatSession, ChatMessage
from backend.llm_gateway.gateway import get_gateway

# Instead of importing from models.py which might trigger re-definition, 
# we'll use the already-loaded models from SQLAlchemy registry if they exist
def get_user_model():
    from models import User
    return User

async def verify_chat_persistence():
    print("🚀 Starting E2E Chat Persistence Verification...")
    
    with app.app_context():
        # 1. Create a dummy user if not exists
        User = get_user_model()
        user = User.query.filter_by(username="test_user").first()
        if not user:
            user = User(username="test_user", email="test@example.com")
            user.set_password("TestPassword123!")
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created test user: {user.id}")
        
        # 2. Simulate a chat session
        session_id = str(uuid.uuid4())
        gateway = get_gateway()
        
        print(f"💬 Simulating chat turn for session: {session_id}")
        
        # Directly call gateway process with session_id
        from backend.llm_gateway.gateway import GatewayRequest
        
        request = GatewayRequest(
            messages=[{"role": "user", "content": "What is the capital of UKG logic?"}],
            user_id=user.id,
            session_id=session_id,
            run_ukg_pipeline=True
        )
        
        response = await gateway.process(request)
        print(f"🤖 Assistant response received: {response.content[:50]}...")
        
        # 3. Verify SQL Persistence
        session = ChatSession.query.get(uuid.UUID(session_id))
        if not session:
            print("❌ FAIL: ChatSession not found in DB")
            return
        
        messages = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.created_at).all()
        if len(messages) < 2:
            print(f"❌ FAIL: Expected 2 messages, found {len(messages)}")
            return
        
        print(f"✅ Verified {len(messages)} messages persisted in SQL")
        for m in messages:
            print(f"   [{m.role}]: {m.content[:30]}...")
            
        # 4. Verify RAG search works
        try:
            from backend.services.rag_service import get_rag_service
            rag = get_rag_service()
            results = rag.search_chat_history(session_id, "UKG logic")
            if results and len(results) > 0:
                print(f"✅ Verified RAG semantic search found {len(results)} matches")
            else:
                print("⚠️ WARNING: RAG search returned 0 results (might need index sync)")
        except Exception as e:
            print(f"❌ RAG Verification Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_chat_persistence())
