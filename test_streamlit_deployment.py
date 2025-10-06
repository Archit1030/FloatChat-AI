#!/usr/bin/env python3
"""
Test Streamlit deployment and backend connectivity
"""

import requests
import time

# Your URLs
RAILWAY_BACKEND = "https://web-production-bbaf.up.railway.app"
STREAMLIT_APP = "https://flowchat-ai.streamlit.app"  # Update with your actual URL

def test_backend():
    """Test Railway backend"""
    print("🧪 Testing Railway Backend...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{RAILWAY_BACKEND}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Backend Health: {health['status']}")
            print(f"   Database: {health['database']}")
            print(f"   Data Source: {health['data_source']}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_streamlit_app():
    """Test Streamlit app accessibility"""
    print("\n🌐 Testing Streamlit App...")
    
    try:
        response = requests.get(STREAMLIT_APP, timeout=15)
        if response.status_code == 200:
            print("✅ Streamlit app is accessible")
            return True
        else:
            print(f"❌ Streamlit app returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Streamlit app connection failed: {e}")
        return False

def main():
    """Run deployment tests"""
    print("🚀 Testing Complete Deployment")
    print("=" * 50)
    
    backend_ok = test_backend()
    streamlit_ok = test_streamlit_app()
    
    print("\n" + "=" * 50)
    print("📊 Deployment Status:")
    
    if backend_ok:
        print("✅ Railway Backend: Ready")
    else:
        print("❌ Railway Backend: Issues detected")
    
    if streamlit_ok:
        print("✅ Streamlit Frontend: Accessible")
    else:
        print("❌ Streamlit Frontend: Issues detected")
    
    if backend_ok and streamlit_ok:
        print("\n🎉 Complete system is deployed and working!")
        print(f"🔗 Your app: {STREAMLIT_APP}")
        print(f"🔗 Your API: {RAILWAY_BACKEND}")
    else:
        print("\n⚠️ Some components need attention")
    
    print("\n💡 Next steps:")
    print("1. Visit your Streamlit app")
    print("2. Test the chat interface")
    print("3. Verify data visualization")
    print("4. Check backend connectivity in sidebar")

if __name__ == "__main__":
    main()