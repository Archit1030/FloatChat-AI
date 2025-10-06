"""
Demo of the Intelligent Chat Interface
Shows how the system now provides specific answers with real data
"""

from intelligent_llm_interface import intelligent_llm
import json

def demo_intelligent_chat():
    """Demonstrate the intelligent chat capabilities"""
    
    print("🧠 ARGO Float Intelligent Chat Interface Demo")
    print("=" * 60)
    print("Now with RAG pipeline and SQL query generation!")
    print()
    
    # Initialize
    print("🔄 Initializing intelligent system...")
    intelligent_llm.initialize()
    
    if not intelligent_llm.initialized:
        print("❌ Failed to initialize")
        return
    
    print("✅ System ready!")
    print()
    
    # Demo queries that show the intelligence
    demo_queries = [
        {
            "query": "What was the temperature in 2010?",
            "description": "Tests temporal filtering and data retrieval"
        },
        {
            "query": "Average temperature in 2010",
            "description": "Tests statistical analysis with SQL aggregation"
        },
        {
            "query": "How many measurements do we have?",
            "description": "Tests counting queries"
        },
        {
            "query": "What is the highest temperature recorded?",
            "description": "Tests maximum value queries with location data"
        }
    ]
    
    for i, demo in enumerate(demo_queries, 1):
        print(f"🧪 Demo {i}: {demo['query']}")
        print(f"📋 Purpose: {demo['description']}")
        print("-" * 50)
        
        try:
            result = intelligent_llm.query_with_context(demo['query'])
            
            # Show the intelligence
            intent = result.get('query_intent', {})
            print(f"🎯 Detected Intent: {intent.get('type', 'unknown')}")
            
            if intent.get('temporal'):
                print(f"📅 Temporal Context: {intent['temporal']}")
            
            if intent.get('measurement_type'):
                print(f"🌡️ Parameters: {intent['measurement_type']}")
            
            print(f"🔍 Context Retrieved: {len(result.get('context_documents', []))} documents")
            print(f"📊 SQL Results: {len(result.get('sql_results', []))} records")
            
            print(f"\n💬 **Answer:**")
            print(result.get('answer', 'No answer'))
            
            # Show sample data if available
            if result.get('sql_results'):
                print(f"\n📈 **Sample Data:**")
                sample = result['sql_results'][0]
                for key, value in sample.items():
                    if value is not None:
                        print(f"   {key}: {value}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60 + "\n")
    
    print("🎉 Demo completed!")
    print("\n🌊 **Key Improvements:**")
    print("✅ Extracts temporal information (years, months)")
    print("✅ Generates specific SQL queries based on intent")
    print("✅ Retrieves actual data from PostgreSQL")
    print("✅ Provides specific answers with real measurements")
    print("✅ Uses ChromaDB for semantic context retrieval")
    print("✅ Handles complex oceanographic queries intelligently")

if __name__ == "__main__":
    demo_intelligent_chat()