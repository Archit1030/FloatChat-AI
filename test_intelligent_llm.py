"""
Test script for the intelligent LLM interface
Tests the RAG pipeline and SQL generation capabilities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intelligent_llm_interface import intelligent_llm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_intelligent_llm():
    """Test the intelligent LLM interface directly"""
    
    print("🧠 Testing Intelligent LLM Interface")
    print("=" * 50)
    
    # Initialize the interface
    print("🔄 Initializing intelligent LLM...")
    intelligent_llm.initialize()
    
    if not intelligent_llm.initialized:
        print("❌ Failed to initialize intelligent LLM")
        return
    
    print("✅ Intelligent LLM initialized successfully!")
    print()
    
    # Test queries
    test_queries = [
        "What was the temperature in 2011?",
        "Average temperature in 2010",
        "What is the highest temperature recorded?",
        "How many measurements do we have?",
        "Show me salinity data from January 2010",
        "Temperature trend over time"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"🧪 Test {i}: {query}")
        print("-" * 30)
        
        try:
            result = intelligent_llm.query_with_context(query)
            
            print(f"📋 Query Intent: {result.get('query_intent', {}).get('type', 'unknown')}")
            print(f"🔍 Context Documents: {len(result.get('context_documents', []))}")
            print(f"📊 SQL Results: {len(result.get('sql_results', []))}")
            print(f"💬 Answer: {result.get('answer', 'No answer')[:200]}...")
            
            if result.get('sql_results'):
                print(f"📈 Sample Data: {result['sql_results'][0] if result['sql_results'] else 'None'}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("🎉 Testing completed!")

if __name__ == "__main__":
    test_intelligent_llm()