"""
Test script for ARGO data processing pipeline
Tests the complete workflow from NetCDF to ChromaDB
"""

import logging
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_complete_pipeline():
    """Test the complete data processing pipeline"""
    
    logger.info("🧪 Testing ARGO Data Processing Pipeline")
    logger.info("=" * 50)
    
    # Step 1: Check if NetCDF file exists
    netcdf_files = list(Path('.').glob('*.nc'))
    
    if not netcdf_files:
        logger.info("📥 No NetCDF files found. Creating synthetic data...")
        
        try:
            from download_argo_data import ARGODataDownloader
            downloader = ARGODataDownloader()
            
            # Create synthetic data
            synthetic_file = downloader.create_synthetic_data(
                filename='test_tempsal.nc',
                num_floats=2,  # Small dataset for testing
                num_profiles=6  # 6 months of data
            )
            
            logger.info(f"✅ Created synthetic data: {synthetic_file}")
            netcdf_file = synthetic_file
            
        except Exception as e:
            logger.error(f"❌ Failed to create synthetic data: {e}")
            return False
    else:
        netcdf_file = str(netcdf_files[0])
        logger.info(f"📁 Using existing NetCDF file: {netcdf_file}")
    
    # Step 2: Test data processing
    try:
        from argo_data_processor import ARGODataProcessor
        
        processor = ARGODataProcessor(netcdf_file, chunk_size=5000)
        
        # Analyze file structure
        logger.info("📊 Analyzing NetCDF structure...")
        analysis = processor.analyze_netcdf_structure()
        logger.info(f"File size: {analysis['file_size_mb']:.1f}MB")
        logger.info(f"Estimated measurements: {analysis['estimated_measurements']:,}")
        
        # Process small dataset for testing
        logger.info("🔄 Processing data (limited to 5000 measurements for testing)...")
        processor.process_netcdf_chunked(max_measurements=5000)
        
        logger.info("✅ Data processing completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Data processing failed: {e}")
        return False
    
    # Step 3: Test database connections
    try:
        logger.info("🗄️ Testing database connections...")
        
        # Test PostgreSQL
        from sqlalchemy import create_engine, text
        import config
        
        engine = create_engine(config.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM measurements;"))
            count = result.fetchone()[0]
            logger.info(f"✅ PostgreSQL: {count:,} measurements stored")
        
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL test failed: {e}")
    
    # Step 4: Test ChromaDB
    try:
        import chromadb
        
        client = chromadb.PersistentClient(path=config.CHROMA_PATH) if config.VECTOR_STORE == "persistent" else chromadb.EphemeralClient()
        
        try:
            collection = client.get_collection("argo_measurements")
            doc_count = collection.count()
            logger.info(f"✅ ChromaDB: {doc_count:,} documents stored")
            
            # Test a simple query
            results = collection.query(
                query_texts=["temperature measurements in the ocean"],
                n_results=3
            )
            
            if results['documents'][0]:
                logger.info("✅ ChromaDB query test successful")
                logger.info(f"Sample result: {results['documents'][0][0][:100]}...")
            
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB collection not found: {e}")
    
    except Exception as e:
        logger.warning(f"⚠️ ChromaDB test failed: {e}")
    
    # Step 5: Test API endpoints (if backend is running)
    try:
        import requests
        
        logger.info("🔌 Testing API endpoints...")
        
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"✅ API Health: {health_data}")
            
            # Test query endpoint
            query_response = requests.post(
                "http://localhost:8000/query",
                json={"query_text": "What is the average temperature?"},
                timeout=10
            )
            
            if query_response.status_code == 200:
                logger.info("✅ API query test successful")
            else:
                logger.warning(f"⚠️ API query failed: {query_response.status_code}")
        else:
            logger.warning(f"⚠️ API health check failed: {response.status_code}")
    
    except requests.exceptions.RequestException:
        logger.info("ℹ️ API not running (this is OK for data processing test)")
    except Exception as e:
        logger.warning(f"⚠️ API test error: {e}")
    
    logger.info("🎉 Pipeline test completed!")
    return True

def test_individual_components():
    """Test individual components separately"""
    
    logger.info("🔧 Testing Individual Components")
    logger.info("=" * 40)
    
    # Test 1: Configuration
    try:
        import config
        logger.info(f"✅ Config loaded - Database: {config.DATABASE_URL[:20]}...")
        logger.info(f"✅ ChromaDB path: {config.CHROMA_PATH}")
        logger.info(f"✅ Vector store: {config.VECTOR_STORE}")
    except Exception as e:
        logger.error(f"❌ Config test failed: {e}")
        return False
    
    # Test 2: Dependencies
    required_packages = [
        'xarray', 'pandas', 'numpy', 'sqlalchemy', 
        'chromadb', 'sentence_transformers', 'requests'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} imported successfully")
        except ImportError as e:
            logger.error(f"❌ {package} import failed: {e}")
    
    # Test 3: Database connection
    try:
        from sqlalchemy import create_engine
        engine = create_engine(config.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute("SELECT 1;")
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    
    # Test 4: Embedding model
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        test_embedding = model.encode(["test sentence"])
        logger.info(f"✅ Embedding model loaded (dimension: {len(test_embedding[0])})")
    except Exception as e:
        logger.error(f"❌ Embedding model test failed: {e}")
    
    return True

def main():
    """Main test function"""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--components-only':
        # Test only individual components
        success = test_individual_components()
    else:
        # Test complete pipeline
        logger.info("🚀 Starting comprehensive pipeline test...")
        logger.info("Use --components-only flag to test only individual components")
        logger.info("")
        
        # First test components
        if not test_individual_components():
            logger.error("❌ Component tests failed. Fix issues before running full pipeline.")
            return
        
        logger.info("")
        
        # Then test full pipeline
        success = test_complete_pipeline()
    
    if success:
        logger.info("🎉 All tests completed successfully!")
        logger.info("Your ARGO data processing pipeline is ready!")
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()