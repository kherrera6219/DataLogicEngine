import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app import app
from backend.truth_engine.api import get_truth_core_engine
from extensions import db
from models import User

def verify_workflow():
    with app.app_context():
        # Get a user (create if none exists for testing)
        user = User.query.first()
        if not user:
            print("Creating test user...")
            user = User(username="test_user", email="test@example.com")
            user.set_password("SecureAuth_2024#!")
            db.session.add(user)
            db.session.commit()
            
        engine = get_truth_core_engine()
        
        print("Creating high-stakes session...")
        session = engine.create_session(
            query="What is the impact of blockchain on healthcare billing compliance?",
            user_id=user.id
        )
        
        session_id = session['session_id']
        print(f"Session created: {session_id}")
        
        print("Processing session (this might take a few seconds)...")
        result = engine.process(session_id)
        
        print(f"Status: {result.get('status')}")
        print(f"Confidence: {result.get('confidence_score')}")
        
        steps = result.get('workflow_steps', [])
        print(f"Executed {len(steps)} steps.")
        
        for step in steps:
            s_name = step.get('step')
            s_status = step.get('status')
            s_ka = step.get('ka_id', 'None')
            print(f"  - {s_name} [{s_ka}]: {s_status}")
            
        if any(step.get('ka_id') for step in steps):
            print("SUCCESS: KA integration verified in workflow!")
        else:
            print("FAILURE: No KAs executed in workflow.")

if __name__ == "__main__":
    verify_workflow()
