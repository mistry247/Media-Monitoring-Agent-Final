#!/usr/bin/env python3
"""
Test script for API error handling
"""
import asyncio
import json
from fastapi.testclient import TestClient
from main import app

def test_api_error_handling():
    """Test API endpoints with error handling"""
    client = TestClient(app)
    
    print("Testing API error handling...")
    
    # Test 1: Health check endpoint
    print("\n1. Testing health check endpoint...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Overall status: {data['status']}")
        print(f"   Checks: {data['summary']['total_checks']}")
    
    # Test 2: Simple health check
    print("\n2. Testing simple health check...")
    response = client.get("/health/simple")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: {data['status']}")
    
    # Test 3: Version endpoint
    print("\n3. Testing version endpoint...")
    response = client.get("/version")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Name: {data['name']}")
        print(f"   Version: {data['version']}")
    
    # Test 4: Article submission with valid data
    print("\n4. Testing article submission (valid)...")
    article_data = {
        "url": "https://example.com/test-article",
        "submitted_by": "Test User"
    }
    response = client.post("/api/articles/submit", json=article_data)
    print(f"   Status: {response.status_code}")
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"   Success: {data.get('success', False)}")
        print(f"   Message: {data.get('message', 'No message')}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 5: Article submission with duplicate URL
    print("\n5. Testing article submission (duplicate)...")
    response = client.post("/api/articles/submit", json=article_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 409:
        print("   ✓ Correctly handled duplicate URL")
    else:
        print(f"   Response: {response.text}")
    
    # Test 6: Article submission with invalid data
    print("\n6. Testing article submission (invalid)...")
    invalid_data = {
        "url": "",  # Empty URL
        "submitted_by": ""  # Empty name
    }
    response = client.post("/api/articles/submit", json=invalid_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 422:
        print("   ✓ Correctly handled validation error")
    else:
        print(f"   Response: {response.text}")
    
    # Test 7: Get pending articles
    print("\n7. Testing get pending articles...")
    response = client.get("/api/articles/pending")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Articles count: {data.get('count', 0)}")
    
    # Test 8: Get non-existent article
    print("\n8. Testing get non-existent article...")
    response = client.get("/api/articles/pending/99999")
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print("   ✓ Correctly handled not found error")
    else:
        print(f"   Response: {response.text}")
    
    # Test 9: Check duplicate URL
    print("\n9. Testing duplicate URL check...")
    check_data = {"url": "https://example.com/test-article"}
    response = client.post("/api/articles/check-duplicate", json=check_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Is duplicate: {data.get('is_duplicate', False)}")
        print(f"   Location: {data.get('location', 'none')}")
    
    # Test 10: Media report generation
    print("\n10. Testing media report generation...")
    report_data = {"pasted_content": "Test content for media report"}
    response = client.post("/api/reports/media", json=report_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 202:
        data = response.json()
        print(f"   Success: {data.get('success', False)}")
        print(f"   Report ID: {data.get('report_id', 'None')}")
        
        # Test report status
        if data.get('report_id'):
            print("\n11. Testing report status check...")
            status_response = client.get(f"/api/reports/status/{data['report_id']}")
            print(f"   Status: {status_response.status_code}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   Report status: {status_data.get('status', 'unknown')}")
    
    print("\n✓ API error handling tests completed!")

if __name__ == "__main__":
    test_api_error_handling()