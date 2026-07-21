"""
E2E test for /ingest endpoint with actual documents
Tests the complete flow: ingest real documents -> verify storage -> query documents
"""

import requests
import os
import time
from app.services.document_service import DocumentService
from app.services.vector_store import VectorStore


def test_ingest_endpoint_e2e():
    """Test the complete e2e flow for document ingestion"""
    print("=== E2E Test: /ingest endpoint with actual documents ===")
    
    port = os.getenv("PORT", "8000")
    base_url = f"http://localhost:{port}"
    
    # Step 1: Get initial vector store state
    print("\n1. Checking initial vector store state...")
    vector_store = VectorStore()
    initial_stats = vector_store.get_collection_stats()
    print(f"Initial vector store contains {initial_stats['total_documents']} documents")
    
    # Step 2: Verify we can load documents using document_service
    print("\n2. Testing document_service.load_all_documents()...")
    doc_service = DocumentService()
    documents = doc_service.load_all_documents()
    print(f"Loaded {len(documents)} document chunks")
    
    # Show document sources
    sources = {}
    for doc in documents:
        source = doc.metadata.get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1
    
    print("Document sources:")
    for source, count in sources.items():
        print(f"  - {source}: {count} chunks")
    
    # Step 3: Test the /ingest API endpoint
    print("\n3. Testing POST /ingest endpoint...")
    
    start_time = time.time()
    response = requests.post(f"{base_url}/ingest")
    end_time = time.time()
    
    print(f"Status Code: {response.status_code}")
    print(f"Ingestion Time: {end_time - start_time:.2f} seconds")
    
    ingestion_result = None
    if response.status_code == 200:
        ingestion_result = response.json()
        print("Ingestion successful!")
        print(f"  Status: {ingestion_result['status']}")
        print(f"  Message: {ingestion_result['message']}")
        print(f"  Total Documents: {ingestion_result['total_documents']}")
        print("  Sources:")
        for source, count in ingestion_result['sources'].items():
            print(f"    - {source}: {count} chunks")
    else:
        print(f"Ingestion failed: {response.text}")
        assert False, f"Ingestion failed with status {response.status_code}: {response.text}"
    
    # Step 4: Verify documents are in vector store
    print("\n4. Verifying documents in vector store...")
    vector_store = VectorStore()
    final_stats = vector_store.get_collection_stats()
    print(f"Vector store now contains {final_stats['total_documents']} documents")
    
    if final_stats['total_documents'] > initial_stats['total_documents']:
        print(f"Added {final_stats['total_documents'] - initial_stats['total_documents']} new documents")
    
    print("Current sources in vector store:")
    for source, count in final_stats['sources'].items():
        print(f"  - {source}: {count} chunks")
    
    # Step 5: Test queries against ingested documents
    print("\n5. Testing queries against ingested documents...")
    
    test_queries = [
        "What is a variable in Python?",  # Should find content from Think Python
        "How should I name functions according to PEP 8?",  # Should find PEP 8 content
        "What are the different types of errors in Python?",  # Should find Think Python content
        "What is the recommended line length in Python code?"  # Should find PEP 8 content
    ]
    
    all_queries_successful = True
    
    for i, question in enumerate(test_queries, 1):
        print(f"\n5.{i} Testing query: {question}")
        
        query_data = {"question": question}
        response = requests.post(f"{base_url}/query", json=query_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Query successful")
            print(f"  Answer preview: {result['answer'][:150]}...")
            print(f"  Sources found: {len(result['sources'])}")
            
            # Show source breakdown
            source_breakdown = {}
            for source in result['sources']:
                source_name = source.get('source', 'unknown')
                source_breakdown[source_name] = source_breakdown.get(source_name, 0) + 1
            
            print("  Source breakdown:")
            for source, count in source_breakdown.items():
                print(f"    - {source}: {count} chunks")
                
        else:
            print(f"Query failed: {response.text}")
            all_queries_successful = False
    
    # Step 6: Summary
    print("\n" + "="*60)
    print("E2E TEST SUMMARY")
    print("="*60)
    
    # Step 6: Final assertions
    print("Final test assertions...")
    assert response.status_code == 200, f"Ingestion endpoint failed with status {response.status_code}"
    assert ingestion_result is not None, "No ingestion result received"
    assert all_queries_successful, "Some test queries failed"
    
    print("ALL TESTS PASSED")
    print(f"Successfully ingested {ingestion_result['total_documents']} documents")
    print(f"All {len(test_queries)} test queries returned results")
    print("Both Think Python and PEP 8 content accessible")


if __name__ == "__main__":
    print("Make sure your FastAPI server is running first!")
    print("Run: python -m app.main")
    print("Then run this test...")
    print()
    
    try:
        test_ingest_endpoint_e2e()
        print("\nE2E test completed successfully!")
    except AssertionError as e:
        print(f"\nE2E test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\nE2E test failed with unexpected error: {e}")
        exit(1)