#!/usr/bin/env python3
"""
Test the validation functions to see if they're causing the 500 error
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from models.article import ArticleSubmission

def test_validation():
    print("Testing ArticleSubmission validation...")
    
    try:
        # Test with the same data from the debug form
        submission = ArticleSubmission(
            url="https://example.com/test-article",
            submitted_by="Test User"
        )
        print("✅ Validation passed!")
        print(f"   URL: {submission.url}")
        print(f"   Name: {submission.submitted_by}")
        return True
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_validation()