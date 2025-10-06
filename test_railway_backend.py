#!/usr/bin/env python3
"""
Test Railway backend functionality including LLM and data queries
"""

import requests
import json
import time

RAILWAY_URL = "https://web-production-bbaf.up.railway.app"

def test_endpoint(endpoint, method="GET", data=None):
    """Test a specific endpoint"""
    url = f"{RAILWAY_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        
        print(f"✅ {method} {endpoint}: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict) and len(str(result)) > 200:
                # Truncate long responses
                print(f"   Response: {str(result)[:200]}...")
            else:
                print(f"   Response: {result}")
            return True, result
        else:
            print(f"   Error: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ {method} {endpoint}: {e}")
        return False, None

def main():
    """Test all backend functionality"""
    
    print("🧪 Testing Railway Backend Functionality")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n📋 Test 1: Health Check")
    success, health = test_endpoint("/health")
    
    if success:
        print(f"   Database: {health.get('database', 'unknown')}")
        print(f"   Vector Store: {health.get('vector_store', 'unknown')}")
        print(f"   Data Source: {health.get('data_source', 'unknown')}")
    
    # Test 2: Statistics
    print("\n📊 Test 2: Statistics")
    success, stats = test_endpoint("/statistics")
    
    if success:
        print(f"   Floats: {stats.get('active_floats', 0):,}")
        print(f"   Measurements: {stats.get('total_measurements', 0):,}")
        print(f"   Avg Temperature: {stats.get('avg_temperature', 0):.2f}°C")
    
    # Test 3: Simple Query (without LLM)
    print("\n🔍 Test 3: Simple Data Query")
    success, floats = test_endpoint("/floats")
    
    if success and isinstance(floats, list):
        print(f"   Retrieved {len(floats)} float records")
        if floats:
            print(f"   Sample float: {floats[0].get('float_id', 'unknown')}")
    
    # Test 4: LLM Query
    print("\n🤖 Test 4: LLM Query")
    query_data = {
        "query_text": "What is the average temperature in the dataset?"
    }
    success, query_result = test_endpoint("/query", method="POST", data=query_data)
    
    if success:
        answer = query_result.get('answer', '')
        print(f"   LLM Response: {answer[:150]}...")
        
        # Check if it's a real LLM response or fallback
        if "fallback" in answer.lower() or "error" in answer.lower():
            print("   ⚠️ Using fallback response - LLM may not be configured")
        else:
            print("   ✅ LLM responding correctly")
    
    # Test 5: Data Status
    print("\n📈 Test 5: Data Status")
    success, status = test_endpoint("/data-status")
    
    if success:
        print(f"   Database Connected: {status.get('database_connected', False)}")
        print(f"   Real Data Available: {status.get('real_data_available', False)}")
        print(f"   ChromaDB Connected: {status.get('chromadb_connected', False)}")
    
    print("\n" + "=" * 50)
    print("🎯 Backend Readiness Summary:")
    
    # Determine readiness
    if health and health.get('database') == 'connected' and health.get('data_source') != 'no_data':
        print("✅ Database: Ready")
    else:
        print("❌ Database: Not ready")
    
    if stats and stats.get('total_measurements', 0) > 100000:
        print("✅ Data: Ready (122K+ measurements)")
    else:
        print("❌ Data: Not ready")
    
    # Check LLM readiness based on query response
    if query_result and "fallback" not in query_result.get('answer', '').lower():
        print("✅ LLM: Ready")
    else:
        print("⚠️ LLM: Needs API key configuration")
    
    print("\n💡 Next Steps:")
    print("1. Add HUGGINGFACE_API_KEY to Railway environment variables")
    print("2. Optionally add ChromaDB for enhanced semantic search")
    print("3. Test frontend connection")

if __name__ == "__main__":
    main()