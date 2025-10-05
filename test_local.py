"""
Local Testing Script
Quick test of backend and frontend locally before deployment
"""

import subprocess
import time
import requests
import logging
import sys
import os
from pathlib import Path
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalTester:
    """Helper for local testing"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        
    def check_dependencies(self):
        """Check if required packages are installed"""
        
        logger.info("🔍 Checking dependencies...")
        
        required_packages = [
            'fastapi', 'uvicorn', 'sqlalchemy', 'pandas', 
            'streamlit', 'plotly', 'requests'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                logger.error(f"❌ {package} - not installed")
        
        if missing_packages:
            logger.error(f"Missing packages: {missing_packages}")
            logger.info("Install with: pip install " + " ".join(missing_packages))
            return False
        
        logger.info("✅ All dependencies available")
        return True
    
    def check_configuration(self):
        """Check configuration files"""
        
        logger.info("⚙️ Checking configuration...")
        
        try:
            import config
            logger.info("✅ config.py loaded")
            
            # Test database URL format
            if hasattr(config, 'DATABASE_URL'):
                logger.info("✅ DATABASE_URL configured")
            else:
                logger.warning("⚠️ DATABASE_URL not found")
            
        except Exception as e:
            logger.error(f"❌ Configuration error: {e}")
            return False
        
        # Check if main_cloud.py exists
        if Path("main_cloud.py").exists():
            logger.info("✅ main_cloud.py found")
        else:
            logger.error("❌ main_cloud.py not found")
            return False
        
        # Check if streamlit app exists
        if Path("streamlit_app_hybrid.py").exists():
            logger.info("✅ streamlit_app_hybrid.py found")
        else:
            logger.error("❌ streamlit_app_hybrid.py not found")
            return False
        
        return True
    
    def setup_local_secrets(self):
        """Setup local Streamlit secrets"""
        
        logger.info("📝 Setting up local Streamlit secrets...")
        
        secrets_dir = Path(".streamlit")
        secrets_dir.mkdir(exist_ok=True)
        
        secrets_file = secrets_dir / "secrets.toml"
        
        secrets_content = '''# Local testing configuration
BACKEND_URL = "http://localhost:8000"

# For deployment, replace with your Railway URL
# BACKEND_URL = "https://your-railway-url.railway.app"
'''
        
        secrets_file.write_text(secrets_content)
        logger.info("✅ Local secrets.toml configured")
    
    def start_backend(self):
        """Start backend server"""
        
        logger.info("🚀 Starting backend server...")
        
        try:
            # Start backend in background
            self.backend_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "main_cloud:app", 
                "--reload", 
                "--host", "0.0.0.0", 
                "--port", "8000"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for backend to start
            logger.info("⏳ Waiting for backend to start...")
            time.sleep(5)
            
            # Test if backend is running
            for attempt in range(10):
                try:
                    response = requests.get("http://localhost:8000/health", timeout=2)
                    if response.status_code == 200:
                        logger.info("✅ Backend started successfully!")
                        logger.info(f"Backend running at: http://localhost:8000")
                        logger.info(f"API docs at: http://localhost:8000/docs")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(2)
                    logger.info(f"⏳ Attempt {attempt + 1}/10...")
            
            logger.error("❌ Backend failed to start")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error starting backend: {e}")
            return False
    
    def test_backend_endpoints(self):
        """Test backend endpoints"""
        
        logger.info("🧪 Testing backend endpoints...")
        
        endpoints = [
            ("/health", "Health check"),
            ("/", "Root endpoint"),
            ("/statistics", "Statistics"),
            ("/floats", "Floats data"),
            ("/sample-queries", "Sample queries")
        ]
        
        all_passed = True
        
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ {description} - OK")
                else:
                    logger.error(f"❌ {description} - HTTP {response.status_code}")
                    all_passed = False
            except Exception as e:
                logger.error(f"❌ {description} - Error: {e}")
                all_passed = False
        
        # Test query endpoint
        try:
            query_data = {"query_text": "What is the average temperature?"}
            response = requests.post("http://localhost:8000/query", json=query_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Query endpoint - OK")
                logger.info(f"   Sample response: {result.get('answer', '')[:100]}...")
            else:
                logger.error(f"❌ Query endpoint - HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            logger.error(f"❌ Query endpoint - Error: {e}")
            all_passed = False
        
        return all_passed
    
    def start_frontend_instructions(self):
        """Show instructions for starting frontend"""
        
        logger.info("🖥️ Frontend Setup Instructions")
        logger.info("=" * 40)
        logger.info("To start the frontend, open a NEW terminal window and run:")
        logger.info("")
        logger.info("   streamlit run streamlit_app_hybrid.py")
        logger.info("")
        logger.info("The frontend will open at: http://localhost:8501")
        logger.info("")
        logger.info("In the Streamlit app, check:")
        logger.info("✅ Sidebar shows 'Backend API Connected'")
        logger.info("✅ Overview tab displays statistics")
        logger.info("✅ Chat interface responds to queries")
        logger.info("✅ Map and profile tabs load data")
        logger.info("")
        logger.info("Press Ctrl+C in this terminal to stop the backend")
    
    def cleanup(self):
        """Clean up processes"""
        
        if self.backend_process:
            logger.info("🛑 Stopping backend server...")
            self.backend_process.terminate()
            self.backend_process.wait()
        
        if self.frontend_process:
            logger.info("🛑 Stopping frontend server...")
            self.frontend_process.terminate()
            self.frontend_process.wait()

def main():
    """Main testing function"""
    
    logger.info("🧪 ARGO Float Dashboard - Local Testing")
    logger.info("=" * 50)
    
    tester = LocalTester()
    
    try:
        # Step 1: Check dependencies
        if not tester.check_dependencies():
            logger.error("❌ Fix dependencies before continuing")
            return
        
        # Step 2: Check configuration
        if not tester.check_configuration():
            logger.error("❌ Fix configuration before continuing")
            return
        
        # Step 3: Setup local secrets
        tester.setup_local_secrets()
        
        # Step 4: Start backend
        if not tester.start_backend():
            logger.error("❌ Backend failed to start")
            return
        
        # Step 5: Test backend
        if not tester.test_backend_endpoints():
            logger.warning("⚠️ Some backend tests failed, but continuing...")
        
        # Step 6: Instructions for frontend
        tester.start_frontend_instructions()
        
        # Keep backend running
        logger.info("🔄 Backend is running. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down...")
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()