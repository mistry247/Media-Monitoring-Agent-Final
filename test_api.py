#!/usr/bin/env python3
"""
Simple script to test API endpoints
"""
import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("Testing API endpoints...")
    
    # Test 1: Get pending articles
    try:
        response = requests.get(f"{base_url}/api/articles/pending")
        print(f"✅ GET /api/articles/pending: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data)} pending articles")
    except Exception as e:
        print(f"❌ GET /api/articles/pending failed: {e}")
    
    # Test 2: Submit article
    try:
        payload = {
            "url": "https://example.com/test-article",
            "submitted_by": "Test User"
        }
        response = requests.post(
            f"{base_url}/api/articles/submit",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ POST /api/articles/submit: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ POST /api/articles/submit failed: {e}")
    
    # Test 3: Health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ GET /health: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ GET /health failed: {e}")

if __name__ == "__main__":
    test_api()