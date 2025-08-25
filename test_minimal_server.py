#!/usr/bin/env python3
"""
Minimal FastAPI server to test if the issue is in imports
"""
from fastapi import FastAPI

app = FastAPI()

@app.post("/test-minimal")
async def test_minimal(request_data: dict):
    """Ultra minimal endpoint with zero dependencies"""
    return {
        "success": True,
        "message": "Minimal server working",
        "received": request_data
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting minimal server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)