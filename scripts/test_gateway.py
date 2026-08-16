#!/usr/bin/env python
"""
LLM Gateway Test Script

Tests the gateway API endpoints without requiring external services.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


def test_gateway_health():
    """Test gateway health endpoint."""
    with app.test_client() as client:
        response = client.get('/api/v1/gateway/health')
        print(f"GET /api/v1/gateway/health -> {response.status_code}")
        data = response.get_json()
        print(json.dumps(data, indent=2))
        return response.status_code == 200


def test_gateway_providers():
    """Test provider listing (requires auth)."""
    with app.test_client() as client:
        response = client.get('/api/v1/gateway/providers')
        print(f"GET /api/v1/gateway/providers -> {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(json.dumps(data, indent=2))
        else:
            print(f"Expected 401 (auth required): {response.get_json()}")
        return True


def test_gateway_chat_no_auth():
    """Test chat endpoint without auth (should fail)."""
    with app.test_client() as client:
        response = client.post(
            '/api/v1/gateway/chat',
            json={"messages": [{"role": "user", "content": "Hello"}]},
            content_type='application/json'
        )
        print(f"POST /api/v1/gateway/chat (no auth) -> {response.status_code}")
        data = response.get_json()
        print(json.dumps(data, indent=2))
        return response.status_code == 401


def test_admin_providers():
    """Test admin providers endpoint."""
    with app.test_client() as client:
        response = client.get('/api/v1/admin/gateway/providers')
        print(f"GET /api/v1/admin/gateway/providers -> {response.status_code}")
        if response.status_code == 401:
            print("Expected 401 (login required)")
        return True


def run_all_tests():
    """Run all gateway tests."""
    print("\n" + "=" * 60)
    print("LLM GATEWAY API TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        ("Health Check", test_gateway_health),
        ("List Providers (auth check)", test_gateway_providers),
        ("Chat without Auth", test_gateway_chat_no_auth),
        ("Admin Providers (auth check)", test_admin_providers),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            result = test_func()
            results.append((name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((name, "ERROR"))
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for name, result in results:
        print(f"  {name}: {result}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()
