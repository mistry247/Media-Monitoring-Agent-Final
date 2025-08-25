#!/usr/bin/env python3
"""Test the full end-to-end article processing"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_full_process():
    """Test complete article processing from submission to summary"""
    
    print("🚀 Testing Full Article Processing Pipeline\n")
    
    # Step 1: Submit an article
    print("Step 1: Submitting article...")
    test_url = "https://www.bbc.com/news"  # Use a reliable news site
    
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
        print(f"   Full response: {json.dumps(result, indent=2)}")
        
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
        print(f"   Status: {result.get('status', 'N/A')}")
        print()
        
    except Exception as e:
        print(f"❌ Submission error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False
    
    # Step 2: Process the article
    print("Step 2: Processing article (scraping + AI summary)...")
    print("This may take 10-30 seconds...")
    
    try:
        process_url = f"{BASE_URL}/api/articles/process/{article_id}"
        print(f"   Making POST request to {process_url}")
        
        response = requests.post(process_url, timeout=60)
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
        print("📄 SCRAPED CONTENT:")
        scraped = result.get('scraped_content', {})
        print(f"   Title: {scraped.get('title', 'N/A')}")
        print(f"   Author: {scraped.get('author', 'N/A')}")
        print(f"   Word Count: {scraped.get('word_count', 0)}")
        content_preview = scraped.get('content', 'N/A')
        if len(content_preview) > 200:
            content_preview = content_preview[:200] + "..."
        print(f"   Content Preview: {content_preview}")
        print()
        
        print("🤖 AI SUMMARY:")
        summary = result.get('ai_summary', {})
        print(f"   Summary: {summary.get('summary', 'N/A')}")
        print(f"   Key Points: {summary.get('key_points', [])}")
        print(f"   Sentiment: {summary.get('sentiment', 'N/A')}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    print("Testing Media Monitoring Agent - Full Pipeline")
    print("=" * 50)
    
    success = test_full_process()
    
    if success:
        print("🎉 Full end-to-end test completed successfully!")
        print("The application can now:")
        print("  ✅ Submit articles")
        print("  ✅ Scrape article content")
        print("  ✅ Generate AI summaries")
    else:
        print("❌ End-to-end test failed. Check the errors above.")

if __name__ == "__main__":
    main()