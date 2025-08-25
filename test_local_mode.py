#!/usr/bin/env python3
"""Test the full end-to-end article processing in LOCAL MODE"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_local_mode():
    """Test complete article processing using mock data"""
    
    print("🚀 Testing Media Monitoring Agent - LOCAL MODE")
    print("=" * 50)
    print("This test uses mock data instead of real web scraping and AI calls\n")
    
    # Step 1: Submit an article
    print("Step 1: Submitting article...")
    test_url = "https://example.com/test-article"  # Any URL will work in local mode
    
    submission_data = {
        "url": test_url,
        "submitter_name": "Test User"
    }
    
    try:
        print(f"   Making POST request to {BASE_URL}/api/articles/submit")
        response = requests.post(f"{BASE_URL}/api/articles/submit", json=submission_data, timeout=10)
        print(f"   Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Submission failed: {response.status_code}")
            print(f"   Response text: {response.text}")
            return False
            
        result = response.json()
        
        if not result.get('success'):
            print(f"❌ Submission failed: {result}")
            return False
            
        article_id = result.get('id')
        if not article_id:
            print(f"❌ No article ID in response: {result}")
            return False
            
        print(f"✅ Article submitted successfully with ID: {article_id}")
        print(f"   URL: {result.get('url', 'N/A')}")
        print(f"   Submitter: {result.get('submitted_by', 'N/A')}")
        print()
        
    except Exception as e:
        print(f"❌ Submission error: {e}")
        return False
    
    # Step 2: Process the article
    print("Step 2: Processing article (using mock data)...")
    print("This should be fast since we're using mock data...")
    
    try:
        process_url = f"{BASE_URL}/api/articles/process/{article_id}"
        print(f"   Making POST request to {process_url}")
        
        response = requests.post(process_url, timeout=30)
        print(f"   Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Processing failed: {response.status_code}")
            print(f"   Response text: {response.text}")
            return False
            
        result = response.json()
        print(f"   Processing response received")
        
        if not result.get('success'):
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            print(f"   Full error response: {json.dumps(result, indent=2)}")
            return False
            
        print(f"✅ Article processed successfully!")
        print(f"   Processing time: {result.get('processing_time_ms', 0):.0f}ms")
        print()
        
        # Display results
        print("📄 MOCK SCRAPED CONTENT:")
        scraped = result.get('scraped_content', {})
        print(f"   Title: {scraped.get('title', 'N/A')}")
        print(f"   Author: {scraped.get('author', 'N/A')}")
        print(f"   Word Count: {scraped.get('word_count', 0)}")
        content_preview = scraped.get('content', 'N/A')
        if len(content_preview) > 200:
            content_preview = content_preview[:200] + "..."
        print(f"   Content Preview: {content_preview}")
        print()
        
        print("🤖 MOCK AI SUMMARY:")
        summary = result.get('ai_summary', {})
        print(f"   Summary: {summary.get('summary', 'N/A')}")
        print(f"   Key Points: {summary.get('key_points', [])}")
        print(f"   Sentiment: {summary.get('sentiment', 'N/A')}")
        print(f"   Word Count: {summary.get('word_count', 0)}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    success = test_local_mode()
    
    if success:
        print("🎉 LOCAL MODE test completed successfully!")
        print("\nThe application can now:")
        print("  ✅ Submit articles")
        print("  ✅ Use mock web scraping (no internet required)")
        print("  ✅ Use mock AI summaries (no API calls)")
        print("  ✅ Complete full end-to-end processing")
        print("\nTo switch back to real mode, set LOCAL_MODE=false in .env")
    else:
        print("❌ LOCAL MODE test failed. Check the errors above.")

if __name__ == "__main__":
    main()