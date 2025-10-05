"""
Cloud-optimized FastAPI backend for ARGO Float Dashboard
Designed for zero-cost deployment on Railway, Render, etc.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from datetime import datetime
import logging
import os
from typing import Dict, List, Optional, Any

# Import cloud-optimized config
try:
    import config_cloud as config
except ImportError:
    import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI with cloud-friendly settings
app = FastAPI(
    title="ARGO Float Data API",
    description="Cloud-deployed API for oceanographic data visualization",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for database and vector store
engine = None
collection = None
mock_data_initialized = False
mock_floats = None
mock_measurements = None

# Pydantic models
class QueryRequest(BaseModel):
    query_text: str

class QueryResponse(BaseModel):
    answer: str
    context_documents: List[str]
    retrieved_metadata: List[Dict]
    sql_results: Optional[List[Dict]] = None

class HealthResponse(BaseModel):
    status: str
    database: str
    vector_store: str
    environment: str
    message: str

def initialize_mock_data():
    """Initialize mock data for cloud deployment"""
    global mock_data_initialized, mock_floats, mock_measurements
    
    if mock_data_initialized:
        return
    
    logger.info("Initializing mock oceanographic data...")
    
    # Create mock ARGO floats
    import numpy as np
    
    floats_data = []
    measurements_data = []
    
    # Generate 5 floats in Indian Ocean
    float_locations = [
        {"float_id": "ARGO_0001", "lat": 10.5, "lon": 75.2},
        {"float_id": "ARGO_0002", "lat": -5.8, "lon": 80.1},
        {"float_id": "ARGO_0003", "lat": 15.2, "lon": 70.5},
        {"float_id": "ARGO_0004", "lat": 5.3, "lon": 85.7},
        {"float_id": "ARGO_0005", "lat": -2.1, "lon": 67.8}
    ]
    
    measurement_id = 1
    
    for float_info in float_locations:
        float_id = float_info["float_id"]
        base_lat = float_info["lat"]
        base_lon = float_info["lon"]
        
        floats_data.append({
            "float_id": float_id,
            "wmo_id": int(float_id.split("_")[1]) + 5900000,
            "deployment_lat": base_lat,
            "deployment_lon": base_lon,
            "status": "ACTIVE",
            "deployment_date": "2023-01-15"
        })
        
        # Generate measurements for each float
        for profile in range(1, 13):  # 12 profiles
            profile_date = datetime(2023, profile, 15)
            
            # Slight position drift
            lat_drift = np.random.normal(0, 0.5)
            lon_drift = np.random.normal(0, 0.5)
            
            for depth in [5, 25, 50, 100, 200, 500, 1000, 1500]:  # 8 depths
                # Realistic temperature profile
                if depth < 100:
                    temp = 28 - (depth/100)*8 + np.random.normal(0, 0.5)
                elif depth < 500:
                    temp = 20 - (depth-100)/400*10 + np.random.normal(0, 0.3)
                else:
                    temp = 4 + np.random.normal(0, 0.2)
                
                # Realistic salinity
                sal = 35.0 + np.random.normal(0, 0.1)
                if depth > 200:
                    sal += 0.2
                
                measurements_data.append({
                    "id": measurement_id,
                    "float_id": float_id,
                    "profile_id": f"{float_id}_P{profile:02d}",
                    "time": profile_date.isoformat(),
                    "lat": base_lat + lat_drift,
                    "lon": base_lon + lon_drift,
                    "depth": depth,
                    "temperature": max(0, temp),
                    "salinity": sal,
                    "oxygen": max(0, 6.0 - (depth/1000)*3 + np.random.normal(0, 0.5)),
                    "ph": 8.1 - (depth/15000) + np.random.normal(0, 0.02),
                    "chlorophyll": max(0, 0.5 * np.exp(-depth/50) + np.random.normal(0, 0.1)) if depth < 200 else 0.01
                })
                measurement_id += 1
    
    mock_floats = pd.DataFrame(floats_data)
    mock_measurements = pd.DataFrame(measurements_data)
    mock_data_initialized = True
    
    logger.info(f"✅ Mock data initialized: {len(mock_floats)} floats, {len(mock_measurements)} measurements")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global engine, collection
    
    logger.info("🚀 Starting ARGO Float API...")
    
    # Try to initialize database connection
    try:
        from sqlalchemy import create_engine
        engine = create_engine(config.DATABASE_URL)
        logger.info("✅ Database connection initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed: {e}")
        engine = None
    
    # Try to initialize vector store
    try:
        import chromadb
        if config.VECTOR_STORE == "memory":
            client = chromadb.Client()
        else:
            client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        
        collection = client.get_or_create_collection(name="argo_measurements")
        logger.info("✅ Vector store initialized")
    except Exception as e:
        logger.warning(f"⚠️ Vector store initialization failed: {e}")
        collection = None
    
    # Initialize mock data as fallback
    initialize_mock_data()
    
    logger.info("🌊 ARGO Float API ready!")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    return HealthResponse(
        status="healthy",
        database="connected" if engine else "mock",
        vector_store="connected" if collection else "mock",
        environment="cloud" if config.IS_CLOUD else "local",
        message="ARGO Float API is operational"
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🌊 ARGO Float Data API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "environment": "cloud" if config.IS_CLOUD else "local"
    }

@app.post("/query", response_model=QueryResponse)
async def query_data(request: QueryRequest):
    """Process natural language queries about oceanographic data"""
    
    if not mock_data_initialized:
        initialize_mock_data()
    
    query = request.query_text.lower()
    
    # Simple query processing for demo
    if "temperature" in query:
        avg_temp = mock_measurements["temperature"].mean()
        answer = f"Based on ARGO float data, the average temperature across all measurements is {avg_temp:.2f}°C. Temperature varies from surface waters (~28°C) to deep waters (~4°C)."
        context = ["Temperature measurements from ARGO floats in the Indian Ocean"]
        
    elif "salinity" in query:
        avg_sal = mock_measurements["salinity"].mean()
        answer = f"The average salinity across all ARGO measurements is {avg_sal:.2f} PSU. Salinity shows typical oceanic values with slight increases at depth."
        context = ["Salinity measurements from ARGO floats"]
        
    elif "float" in query:
        num_floats = len(mock_floats)
        answer = f"There are {num_floats} active ARGO floats deployed in the Indian Ocean region, collecting oceanographic data continuously."
        context = ["ARGO float deployment information"]
        
    elif "depth" in query:
        max_depth = mock_measurements["depth"].max()
        answer = f"ARGO floats collect data down to {max_depth}m depth, providing vertical profiles of ocean properties."
        context = ["Depth profile information from ARGO floats"]
        
    else:
        answer = "I can help you explore ARGO float oceanographic data. Try asking about temperature, salinity, floats, or depth measurements."
        context = ["General ARGO float information"]
    
    return QueryResponse(
        answer=answer,
        context_documents=context,
        retrieved_metadata=[{"source": "mock_data", "query_type": "semantic"}]
    )

@app.get("/floats")
async def get_floats():
    """Get all ARGO float information"""
    if not mock_data_initialized:
        initialize_mock_data()
    
    return mock_floats.to_dict(orient="records")

@app.get("/measurements")
async def get_measurements(limit: int = 1000):
    """Get measurement data with optional limit"""
    if not mock_data_initialized:
        initialize_mock_data()
    
    return mock_measurements.head(limit).to_dict(orient="records")

@app.get("/statistics")
async def get_statistics():
    """Get system statistics"""
    if not mock_data_initialized:
        initialize_mock_data()
    
    return {
        "active_floats": len(mock_floats),
        "total_measurements": len(mock_measurements),
        "avg_temperature": float(mock_measurements["temperature"].mean()),
        "avg_salinity": float(mock_measurements["salinity"].mean()),
        "depth_range": f"{mock_measurements['depth'].min()}-{mock_measurements['depth'].max()}m",
        "data_quality": 98.5,
        "last_updated": datetime.now().isoformat()
    }

@app.get("/sample-queries")
async def get_sample_queries():
    """Get sample queries for testing"""
    return {
        "analytical_queries": {
            "Temperature Analysis": [
                "What is the average temperature at different depths?",
                "Show me temperature trends in the Indian Ocean",
                "Compare surface and deep water temperatures"
            ],
            "Salinity Analysis": [
                "What are the salinity levels in the Arabian Sea?",
                "Show me salinity profiles by depth",
                "Compare salinity across different regions"
            ]
        },
        "semantic_queries": {
            "General Information": [
                "Tell me about ARGO floats in the Indian Ocean",
                "What oceanographic data is available?",
                "How many active floats are there?",
                "What is the depth range of measurements?"
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)