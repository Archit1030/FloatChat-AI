"""
Test script to verify ChromaDB setup and query ARGO float data
"""

import chromadb
import config

def test_chroma_setup():
    """Test that ChromaDB collection exists and can be queried"""

    print("🔍 Testing ChromaDB setup...")

    # Connect to ChromaDB
    client = chromadb.PersistentClient(path=config.CHROMA_PATH)

    try:
        # Get the collection
        collection = client.get_collection(name="argo_measurements")
        print(f"✅ Collection found with {collection.count()} documents")

        # Test a simple query
        results = collection.query(
            query_texts=["temperature measurements in Indian Ocean"],
            n_results=5
        )

        print(f"✅ Query successful, found {len(results['documents'][0])} results")
        print("Sample result:")
        print(results['documents'][0][0][:200] + "...")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_chroma_setup()
    if success:
        print("\n🎉 ChromaDB setup verified successfully!")
    else:
        print("\n❌ ChromaDB setup failed!")
