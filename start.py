#!/usr/bin/env python3
"""
Railway startup script for ARGO Float API
Handles PORT environment variable properly
"""

import os
import uvicorn
from main_real_data import app

def main():
    # Get port from environment variable, default to 8000
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting ARGO Float API on port {port}...")
    
    # Start uvicorn server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()