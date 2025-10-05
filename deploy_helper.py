"""
Deployment Helper Script
Assists with Railway deployment and configuration updates
"""

import os
import sys
import requests
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentHelper:
    """Helper for Railway deployment process"""
    
    def __init__(self):
        self.project_root = Path(".")
        
    def check_deployment_readiness(self):
        """Check if project is ready for deployment"""
        
        logger.info("🔍 Checking deployment readiness...")
        
        required_files = [
            "railway.json",
            "requirements-backend.txt", 
            "main_cloud.py",
            "config_cloud.py",
            "Procfile",
            "runtime.txt"
        ]
        
        missing_files = []
        for file in required_files:
            if not (self.project_root / file).exists():
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"❌ Missing required files: {missing_files}")
            return False
        
        logger.info("✅ All deployment files present")
        return True
    
    def update_backend_url(self, railway_url: str):
        """Update backend URL in configuration files"""
        
        logger.info(f"🔄 Updating backend URL to: {railway_url}")
        
        # Update GitHub Actions wake-backend.yml
        wake_backend_file = self.project_root / ".github/workflows/wake-backend.yml"
        if wake_backend_file.exists():
            content = wake_backend_file.read_text()
            updated_content = content.replace(
                'BACKEND_URL="https://your-app-name.railway.app"',
                f'BACKEND_URL="{railway_url}"'
            )
            wake_backend_file.write_text(updated_content)
            logger.info("✅ Updated wake-backend.yml")
        
        # Update Streamlit secrets
        secrets_file = self.project_root / ".streamlit/secrets.toml"
        if secrets_file.exists():
            content = secrets_file.read_text()
            updated_content = content.replace(
                'BACKEND_URL = "https://your-railway-url.railway.app"',
                f'BACKEND_URL = "{railway_url}"'
            )
            secrets_file.write_text(updated_content)
            logger.info("✅ Updated .streamlit/secrets.toml")
        
        # Update hybrid app
        hybrid_app_file = self.project_root / "streamlit_app_hybrid.py"
        if hybrid_app_file.exists():
            content = hybrid_app_file.read_text()
            updated_content = content.replace(
                'BACKEND_URL = "https://your-railway-url.railway.app"',
                f'BACKEND_URL = "{railway_url}"'
            )
            hybrid_app_file.write_text(updated_content)
            logger.info("✅ Updated streamlit_app_hybrid.py")
    
    def test_backend_connection(self, backend_url: str):
        """Test connection to deployed backend"""
        
        logger.info(f"🔌 Testing backend connection: {backend_url}")
        
        try:
            # Test health endpoint
            health_url = f"{backend_url}/health"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✅ Backend health check successful")
                logger.info(f"Status: {health_data.get('status')}")
                logger.info(f"Database: {health_data.get('database')}")
                logger.info(f"Vector Store: {health_data.get('vector_store')}")
                
                # Test other endpoints
                endpoints_to_test = [
                    "/",
                    "/floats", 
                    "/statistics",
                    "/sample-queries"
                ]
                
                for endpoint in endpoints_to_test:
                    try:
                        test_response = requests.get(f"{backend_url}{endpoint}", timeout=5)
                        if test_response.status_code == 200:
                            logger.info(f"✅ {endpoint} endpoint working")
                        else:
                            logger.warning(f"⚠️ {endpoint} returned {test_response.status_code}")
                    except Exception as e:
                        logger.warning(f"⚠️ {endpoint} test failed: {e}")
                
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def generate_environment_variables(self):
        """Generate environment variables for Railway"""
        
        logger.info("📋 Environment variables for Railway deployment:")
        logger.info("=" * 50)
        
        env_vars = {
            "HUGGINGFACE_API_KEY": "your_huggingface_token_here",
            "LLM_PROVIDER": "huggingface", 
            "VECTOR_STORE": "memory",
            "LLM_MODEL": "microsoft/DialoGPT-medium",
            "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
            "MAX_FLOATS": "500",
            "MAX_DOCUMENTS": "10000",
            "BATCH_SIZE": "5000"
        }
        
        for key, value in env_vars.items():
            logger.info(f"{key}={value}")
        
        logger.info("=" * 50)
        logger.info("💡 Copy these to your Railway project's environment variables")
        logger.info("🔑 Don't forget to get a real HuggingFace API key!")
    
    def show_deployment_status(self):
        """Show current deployment status"""
        
        logger.info("📊 Current Deployment Status")
        logger.info("=" * 40)
        
        # Check files
        files_status = {
            "railway.json": "✅" if (self.project_root / "railway.json").exists() else "❌",
            "main_cloud.py": "✅" if (self.project_root / "main_cloud.py").exists() else "❌", 
            "requirements-backend.txt": "✅" if (self.project_root / "requirements-backend.txt").exists() else "❌",
            ".streamlit/secrets.toml": "✅" if (self.project_root / ".streamlit/secrets.toml").exists() else "❌"
        }
        
        for file, status in files_status.items():
            logger.info(f"{status} {file}")
        
        # Check if URLs are updated
        secrets_file = self.project_root / ".streamlit/secrets.toml"
        if secrets_file.exists():
            content = secrets_file.read_text()
            if "your-railway-url" in content:
                logger.info("⚠️ Backend URL not updated in secrets.toml")
            else:
                logger.info("✅ Backend URL updated in secrets.toml")

def main():
    """Main deployment helper function"""
    
    helper = DeploymentHelper()
    
    if len(sys.argv) < 2:
        logger.info("🚀 ARGO Float Dashboard - Deployment Helper")
        logger.info("=" * 50)
        logger.info("Usage:")
        logger.info("  python deploy_helper.py check          - Check deployment readiness")
        logger.info("  python deploy_helper.py update-url <url> - Update backend URL")
        logger.info("  python deploy_helper.py test <url>     - Test backend connection")
        logger.info("  python deploy_helper.py env-vars       - Show environment variables")
        logger.info("  python deploy_helper.py status         - Show deployment status")
        logger.info("")
        logger.info("Example:")
        logger.info("  python deploy_helper.py update-url https://floatchat-ai-production.railway.app")
        return
    
    command = sys.argv[1]
    
    if command == "check":
        if helper.check_deployment_readiness():
            logger.info("🎉 Project is ready for Railway deployment!")
        else:
            logger.error("❌ Fix missing files before deploying")
    
    elif command == "update-url":
        if len(sys.argv) < 3:
            logger.error("❌ Please provide the Railway URL")
            logger.info("Example: python deploy_helper.py update-url https://your-app.railway.app")
            return
        
        railway_url = sys.argv[2]
        helper.update_backend_url(railway_url)
        logger.info("🎉 Backend URL updated! Don't forget to commit and push changes.")
    
    elif command == "test":
        if len(sys.argv) < 3:
            logger.error("❌ Please provide the backend URL to test")
            return
        
        backend_url = sys.argv[2]
        if helper.test_backend_connection(backend_url):
            logger.info("🎉 Backend is working correctly!")
        else:
            logger.error("❌ Backend connection failed")
    
    elif command == "env-vars":
        helper.generate_environment_variables()
    
    elif command == "status":
        helper.show_deployment_status()
    
    else:
        logger.error(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()