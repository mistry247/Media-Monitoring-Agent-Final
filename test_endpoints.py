#!/usr/bin/env python3
"""Quick test script for the Media Monitoring Agent endpoints"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test 3: Health check endpoint"""
    print("=== Testing Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"Overall Status: {health_data['status']}")
            print("Service Health:")
            for service, details in health_data['checks'].items():
                print(f"  - {service}: {details['status']}")
        print("✅ Health check passed\n")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        return False

def test_main_page():
    """Test 2: Main application page"""
    print("=== Testing Main Application ===")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            content = response.text
            if "Media Monitoring Agent" in content:
                print("✅ Main page loaded successfully")
                print(f"Page size: {len(content)} characters")
            else:
                print("⚠️ Main page loaded but content unexpected")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Main page failed: {e}\n")
        return False

def test_article_submission():
    """Test 4: Article submission functionality"""
    print("=== Testing Article Submission ===")
    try:
        # Test with a simple, reliable URL
        test_data = {
            "url": "https://httpbin.org/html",  # Simple test page
            "submitter_name": "Test User"
        }
        
        print(f"Submitting test article: {test_data['url']}")
        response = requests.post(
            f"{BASE_URL}/api/articles/submit",
            json=test_data,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Article submitted successfully")
            print(f"Article ID: {result.get('id', 'N/A')}")
            print(f"Status: {result.get('status', 'N/A')}")
        else:
            print(f"❌ Article submission failed")
            print(f"Response: {response.text}")
        
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Article submission failed: {e}\n")
        return False

def main():
    print("🚀 Testing Media Monitoring Agent\n")
    
    results = []
    
    # Run tests in order
    results.append(("Health Check", test_health()))
    results.append(("Main Application", test_main_page()))
    results.append(("Article Submission", test_article_submission()))
    
    # Summary
    print("=== Test Summary ===")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The application is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()