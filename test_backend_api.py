"""
Test the intelligent backend API
"""

import requests
import json

def test_backend():
    backend_url = 'http://localhost:8000'
    
    test_queries = [
        'Hello, what can you tell me about the ocean data?',
        'What was the average temperature in 2010?',
        'How many measurements do we have?',
        'What is the highest temperature recorded?'
    ]
    
    print("🧪 Testing Intelligent Backend API")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: {query}")
        print("-" * 30)
        
        try:
            response = requests.post(f'{backend_url}/query', 
                                   json={'query_text': query}, 
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"Answer: {result.get('answer', 'No answer')}")
                
                if result.get('query_intent'):
                    print(f"Intent: {result['query_intent'].get('type', 'unknown')}")
                
                if result.get('sql_results'):
                    print(f"SQL Results: {len(result['sql_results'])} records")
                    if result['sql_results']:
                        print(f"Sample: {result['sql_results'][0]}")
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_backend()