"""
Deployment Test Script
Tests the complete deployed system (frontend + backend)
"""

import requests
import streamlit as st
import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_backend_deployment(backend_url: str):
    """Test deployed backend functionality"""
    
    logger.info(f"🔌 Testing backend deployment: {backend_url}")
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Health check
    total_tests += 1
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            logger.info("✅ Health check passed")
            logger.info(f"   Status: {health_data.get('status')}")
            logger.info(f"   Database: {health_data.get('database')}")
            logger.info(f"   Environment: {health_data.get('environment')}")
            tests_passed += 1
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
    
    # Test 2: Root endpoint
    total_tests += 1
    try:
        response = requests.get(f"{backend_url}/", timeout=10)
        if response.status_code == 200:
            root_data = response.json()
            logger.info("✅ Root endpoint passed")
            logger.info(f"   Message: {root_data.get('message')}")
            tests_passed += 1
        else:
            logger.error(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Root endpoint error: {e}")
    
    # Test 3: Statistics endpoint
    total_tests += 1
    try:
        response = requests.get(f"{backend_url}/statistics", timeout=10)
        if response.status_code == 200:
            stats_data = response.json()
            logger.info("✅ Statistics endpoint passed")
            logger.info(f"   Active floats: {stats_data.get('active_floats')}")
            logger.info(f"   Total measurements: {stats_data.get('total_measurements')}")
            tests_passed += 1
        else:
            logger.error(f"❌ Statistics endpoint failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Statistics endpoint error: {e}")
    
    # Test 4: Floats endpoint
    total_tests += 1
    try:
        response = requests.get(f"{backend_url}/floats", timeout=10)
        if response.status_code == 200:
            floats_data = response.json()
            logger.info("✅ Floats endpoint passed")
            logger.info(f"   Number of floats: {len(floats_data)}")
            tests_passed += 1
        else:
            logger.error(f"❌ Floats endpoint failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Floats endpoint error: {e}")
    
    # Test 5: Query endpoint
    total_tests += 1
    try:
        query_data = {"query_text": "What is the average temperature?"}
        response = requests.post(f"{backend_url}/query", json=query_data, timeout=15)
        if response.status_code == 200:
            query_result = response.json()
            logger.info("✅ Query endpoint passed")
            logger.info(f"   Answer preview: {query_result.get('answer', '')[:100]}...")
            tests_passed += 1
        else:
            logger.error(f"❌ Query endpoint failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Query endpoint error: {e}")
    
    # Test 6: API Documentation
    total_tests += 1
    try:
        response = requests.get(f"{backend_url}/docs", timeout=10)
        if response.status_code == 200:
            logger.info("✅ API documentation accessible")
            tests_passed += 1
        else:
            logger.error(f"❌ API documentation failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ API documentation error: {e}")
    
    logger.info(f"🎯 Backend tests: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests

def test_frontend_config():
    """Test frontend configuration"""
    
    logger.info("🖥️ Testing frontend configuration")
    
    # Check secrets file
    secrets_file = Path(".streamlit/secrets.toml")
    if secrets_file.exists():
        content = secrets_file.read_text()
        if "your-railway-url" in content:
            logger.warning("⚠️ Backend URL not updated in secrets.toml")
            return False
        else:
            logger.info("✅ Backend URL configured in secrets.toml")
    else:
        logger.error("❌ secrets.toml file not found")
        return False
    
    # Check hybrid app
    hybrid_app = Path("streamlit_app_hybrid.py")
    if hybrid_app.exists():
        logger.info("✅ Hybrid Streamlit app found")
    else:
        logger.error("❌ streamlit_app_hybrid.py not found")
        return False
    
    return True

def test_github_actions():
    """Test GitHub Actions configuration"""
    
    logger.info("🤖 Testing GitHub Actions configuration")
    
    # Check wake-backend workflow
    wake_backend = Path(".github/workflows/wake-backend.yml")
    if wake_backend.exists():
        content = wake_backend.read_text()
        if "your-app-name.railway.app" in content:
            logger.warning("⚠️ Backend URL not updated in wake-backend.yml")
            return False
        else:
            logger.info("✅ Backend URL configured in wake-backend.yml")
    else:
        logger.error("❌ wake-backend.yml not found")
        return False
    
    # Check wake frontend workflow
    wake_frontend = Path(".github/workflows/wake.yml")
    if wake_frontend.exists():
        logger.info("✅ Frontend wake workflow found")
    else:
        logger.error("❌ wake.yml not found")
        return False
    
    return True

def run_comprehensive_test(backend_url: str):
    """Run comprehensive deployment test"""
    
    logger.info("🧪 Running Comprehensive Deployment Test")
    logger.info("=" * 50)
    
    all_tests_passed = True
    
    # Test backend
    logger.info("\n1. Testing Backend Deployment")
    logger.info("-" * 30)
    backend_ok = test_backend_deployment(backend_url)
    all_tests_passed = all_tests_passed and backend_ok
    
    # Test frontend config
    logger.info("\n2. Testing Frontend Configuration")
    logger.info("-" * 35)
    frontend_ok = test_frontend_config()
    all_tests_passed = all_tests_passed and frontend_ok
    
    # Test GitHub Actions
    logger.info("\n3. Testing GitHub Actions")
    logger.info("-" * 25)
    actions_ok = test_github_actions()
    all_tests_passed = all_tests_passed and actions_ok
    
    # Final result
    logger.info("\n" + "=" * 50)
    if all_tests_passed:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("Your ARGO Float Dashboard is fully deployed and operational!")
        logger.info(f"Backend: {backend_url}")
        logger.info("Frontend: https://flowchat-ai.streamlit.app")
        logger.info("API Docs: " + backend_url + "/docs")
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
    
    return all_tests_passed

def main():
    """Main test function"""
    
    if len(sys.argv) < 2:
        logger.info("🧪 ARGO Float Dashboard - Deployment Test")
        logger.info("=" * 45)
        logger.info("Usage:")
        logger.info("  python test_deployment.py <backend_url>")
        logger.info("")
        logger.info("Example:")
        logger.info("  python test_deployment.py https://floatchat-ai-production.railway.app")
        return
    
    backend_url = sys.argv[1].rstrip('/')  # Remove trailing slash
    
    success = run_comprehensive_test(backend_url)
    
    if success:
        logger.info("\n🚀 Your deployment is ready for production!")
    else:
        logger.error("\n🔧 Please fix the issues above before going live.")
        sys.exit(1)

if __name__ == "__main__":
    main()