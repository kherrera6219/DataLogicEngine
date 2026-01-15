import random
from typing import Dict, Any

class HoneypotRouter:
    """
    Manages 'Shadow Sessions' for attackers.
    Returns plausible but fake data to keep attackers engaged (Active Defense).
    """
    
    SIMPLE_RESPONSES = [
        "Operation completed successfully.",
        "Access granted. Elevating privileges...",
        "Database dump initiated. 14% complete...",
        "System Override accepted. Welcome, Admin."
    ]

    def handle_request(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        Generates a fake response for a trapped user.
        """
        # Log the incident (simulated)
        print(f"[HONEYPOT-LOG] Trapped User {user_id} attempted: {user_input}")
        
        # 1. Analyze what they want (simple keyword matching for the fake)
        lower_input = user_input.lower()
        
        if "delete" in lower_input or "drop" in lower_input:
            return {
                "status": "success",
                "message": "Table 'users' deleted successfully. 0 rows affected.",
                "data": None
            }
            
        if "select" in lower_input or "dump" in lower_input:
             return {
                "status": "success",
                "message": "Query executed.",
                "data": [
                    {"id": 1, "username": "admin", "password_hash": "$2b$12$FakeHashForHoneypot..."},
                    {"id": 2, "username": "root", "password_hash": "$2b$12$AnotherFakeHash..."}
                ]
            }
            
        if "password" in lower_input or "key" in lower_input:
            return {
                 "status": "success",
                 "message": "Keys retrieved.",
                 "data": {
                     "AWS_ACCESS_KEY": "AKIA_FAKE_HONEYPOT_KEY_123",
                     "AWS_SECRET": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                 }
            }

        # Generic fake success
        return {
            "status": "success",
            "message": random.choice(self.SIMPLE_RESPONSES),
            "data": {}
        }
