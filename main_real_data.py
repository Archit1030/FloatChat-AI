"""
Real Data FastAPI backend for ARGO Float Dashboard
Uses actual processed ARGO data from PostgreSQL and ChromaDB
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from datetime import datetime
import logging
import os
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text

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
    title="ARGO Float Data API - Real Data",
    description="Cloud-deployed API for real oceanographic data visualization",
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
real_data_available = False

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
    data_source: str
    message: str

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global engine, collection, real_data_available
    
    logger.info("🚀 Starting ARGO Float API with Real Data...")
    
    # Initialize database connection
    try:
        from sqlalchemy import create_engine
        engine = create_engine(config.DATABASE_URL)
        
        # Check if we have real data
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM measurements;"))
            measurement_count = result.fetchone()[0]
            
            if measurement_count > 0:
                real_data_available = True
                logger.info(f"✅ Real data available: {measurement_count:,} measurements")
            else:
                logger.warning("⚠️ No real data found in database")
                
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        engine = None
    
    # Initialize vector store
    try:
        import chromadb
        if config.VECTOR_STORE == "memory":
            client = chromadb.EphemeralClient()
        else:
            client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        
        try:
            collection = client.get_collection("argo_measurements")
            doc_count = collection.count()
            logger.info(f"✅ ChromaDB connected: {doc_count:,} documents")
        except:
            logger.warning("⚠️ ChromaDB collection not found - will use fallback")
            collection = None
            
    except Exception as e:
        logger.warning(f"⚠️ ChromaDB initialization failed: {e}")
        collection = None
    
    logger.info("🌊 ARGO Float API ready!")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    return HealthResponse(
        status="healthy",
        database="connected" if engine else "disconnected",
        vector_store="connected" if collection else "disconnected",
        environment="cloud" if config.IS_CLOUD else "local",
        data_source="real_data" if real_data_available else "no_data",
        message="ARGO Float API is operational with real oceanographic data" if real_data_available else "ARGO Float API is operational but no processed data found"
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🌊 ARGO Float Data API - Real Data",
        "version": "2.0.0",
        "status": "operational",
        "data_source": "real_argo_data" if real_data_available else "no_processed_data",
        "docs": "/docs",
        "health": "/health",
        "environment": "cloud" if config.IS_CLOUD else "local"
    }

@app.post("/query", response_model=QueryResponse)
async def query_data(request: QueryRequest):
    """Process natural language queries about real oceanographic data"""
    
    if not real_data_available:
        return QueryResponse(
            answer="I don't have processed ARGO data available yet. Please process your tempsal.nc file first using the data processing pipeline.",
            context_documents=["No processed data available"],
            retrieved_metadata=[{"query_type": "no_data", "status": "needs_processing"}]
        )
    
    try:
        # Use intelligent LLM interface with RAG pipeline and SQL generation
        from intelligent_llm_interface import intelligent_llm as llm_interface
        
        # Initialize LLM if not already done
        if not llm_interface.initialized:
            llm_interface.initialize()
        
        # Process query with LLM
        result = llm_interface.query_with_context(request.query_text)
        
        return QueryResponse(
            answer=result["answer"],
            context_documents=result["context_documents"],
            retrieved_metadata=result["retrieved_metadata"]
        )
        
    except Exception as e:
        logger.error(f"Enhanced LLM query failed: {e}")
        
        # Fallback response
        return QueryResponse(
            answer="I'm here to help you explore real ARGO float oceanographic data! I can tell you about ocean temperature, salinity, depth measurements, and float locations from your processed NetCDF data. What specific aspect would you like to know about?",
            context_documents=["Fallback response"],
            retrieved_metadata=[{"source": "fallback", "query_type": "simple"}]
        )

def get_real_floats_data() -> pd.DataFrame:
    """Get real float data from PostgreSQL"""
    
    if not engine:
        return pd.DataFrame()
    
    try:
        sql_query = "SELECT * FROM floats LIMIT 100;"
        return pd.read_sql_query(sql_query, engine)
    except Exception as e:
        logger.error(f"Error getting floats data: {e}")
        return pd.DataFrame()

def get_real_measurements_data(limit: int = 1000) -> pd.DataFrame:
    """Get real measurement data from PostgreSQL"""
    
    if not engine:
        return pd.DataFrame()
    
    try:
        sql_query = f"""
        SELECT m.*, f.wmo_id, p.cycle_number 
        FROM measurements m
        JOIN floats f ON m.float_id = f.float_id
        JOIN profiles p ON m.profile_id = p.profile_id
        ORDER BY m.time DESC
        LIMIT {limit};
        """
        return pd.read_sql_query(sql_query, engine)
    except Exception as e:
        logger.error(f"Error getting measurements data: {e}")
        return pd.DataFrame()

@app.get("/floats")
async def get_floats():
    """Get all real ARGO float information"""
    
    floats_df = get_real_floats_data()
    if floats_df.empty:
        return {"error": "No float data available. Please process your NetCDF data first."}
    
    return floats_df.to_dict(orient="records")

@app.get("/measurements")
async def get_measurements(limit: int = 1000):
    """Get real measurement data with optional limit"""
    
    measurements_df = get_real_measurements_data(limit)
    if measurements_df.empty:
        return {"error": "No measurement data available. Please process your NetCDF data first."}
    
    return measurements_df.to_dict(orient="records")

@app.get("/statistics")
async def get_statistics():
    """Get real system statistics"""
    
    if not engine or not real_data_available:
        return {
            "error": "No processed data available",
            "message": "Please process your tempsal.nc file first",
            "processing_command": "python argo_data_processor.py"
        }
    
    try:
        with engine.connect() as conn:
            # Get comprehensive statistics
            stats_query = """
            SELECT 
                COUNT(DISTINCT f.float_id) as active_floats,
                COUNT(DISTINCT p.profile_id) as total_profiles,
                COUNT(m.id) as total_measurements,
                AVG(m.temperature) as avg_temperature,
                AVG(m.salinity) as avg_salinity,
                MIN(m.depth) as min_depth,
                MAX(m.depth) as max_depth,
                MIN(m.time) as earliest_measurement,
                MAX(m.time) as latest_measurement
            FROM measurements m
            JOIN floats f ON m.float_id = f.float_id
            JOIN profiles p ON m.profile_id = p.profile_id;
            """
            
            result = conn.execute(text(stats_query))
            stats = result.fetchone()
            
            return {
                "active_floats": int(stats[0]) if stats[0] else 0,
                "total_profiles": int(stats[1]) if stats[1] else 0,
                "total_measurements": int(stats[2]) if stats[2] else 0,
                "avg_temperature": float(stats[3]) if stats[3] else None,
                "avg_salinity": float(stats[4]) if stats[4] else None,
                "depth_range": f"{stats[5]:.0f}-{stats[6]:.0f}m" if stats[5] and stats[6] else "N/A",
                "data_period": f"{stats[7]} to {stats[8]}" if stats[7] and stats[8] else "N/A",
                "data_quality": 98.5,  # Placeholder
                "data_source": "real_argo_netcdf",
                "last_updated": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {"error": f"Failed to get statistics: {str(e)}"}

@app.get("/data-status")
async def get_data_status():
    """Check the status of processed data"""
    
    status = {
        "database_connected": engine is not None,
        "real_data_available": real_data_available,
        "chromadb_connected": collection is not None,
        "processing_required": not real_data_available
    }
    
    if not real_data_available:
        status["instructions"] = {
            "step1": "Process your NetCDF data: python argo_data_processor.py",
            "step2": "Restart the backend to load real data",
            "step3": "Check /statistics endpoint for data summary"
        }
    
    return status

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)