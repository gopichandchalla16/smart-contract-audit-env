"""Root entry point for Docker — imports server app with correct paths"""
import sys
import os

# Ensure root is in path for models.py imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
