#!/usr/bin/env python3
"""
Test the manual articles API endpoint
"""

import requests
import json

def test_manual_articles_api():
    """Test the manual articles processing API"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Manual Articles API...")
    
    # Test 1: Get manual articles
    print("\n1. Testing GET /api/manual-articles/")
    try:
        response = requests.get(f"{base_url}/api/manual-articles/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            articles = response.json()
            print(f"   Found {len(articles)} manual articles")
            for article in articles:
                print(f"   - ID {article['id']}: {article['url'][:50]}... (has_content: {article['has_content']})")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Test process-batch endpoint
    print("\n2. Testing POST /api/manual-articles/process-batch")
    try:
        test_payload = {
            "articles": [
                {"id": 1, "content": "Test content for article 1"},
                {"id": 2, "content": "Test content for article 2"}
            ],
            "recipient_email": "test@example.com"
        }
        
        response = requests.post(
            f"{base_url}/api/manual-articles/process-batch",
            headers={"Content-Type": "application/json"},
            json=test_payload
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 202:
            result = response.json()
            print(f"   ✅ Success! Job ID: {result.get('job_id')}")
            print(f"   Processed IDs: {result.get('processed_ids')}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Health check
    print("\n3. Testing health endpoint")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health = response.json()
            print(f"   Overall status: {health.get('status')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_manual_articles_api()
