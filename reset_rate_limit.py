#!/usr/bin/env python3
"""
Script to reset rate limiting for testing purposes
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils.security import rate_limiter

def reset_rate_limits():
    """Clear all rate limit data"""
    rate_limiter._requests.clear()
    print("✅ Rate limits have been reset")
    print("All clients can now make requests again")

if __name__ == "__main__":
    reset_rate_limits()