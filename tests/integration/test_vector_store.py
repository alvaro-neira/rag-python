"""
Doesn't need the FastAPI server running
"""

from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


def test_vector_pipeline():
    print("Testing complete vector pipeline...")

    # Step 1: Load documents
    doc_service = DocumentService()
    documents = doc_service.load_all_documents()
    print(f"Loaded {len(documents)} documents")

    # Step 2: Generate embeddings (test with first 20 to keep costs reasonable)
    embedding_service = EmbeddingService()
    test_docs = documents[:20]  # Start small
    embeddings = embedding_service.generate_embeddings(test_docs)
    print(f"Generated {len(embeddings)} embeddings")

    # Step 3: Store in vector database
    vector_store = VectorStore()
    vector_store.add_documents(test_docs, embeddings)

    # Step 4: Test similarity search
    test_queries = [
        "What is a variable in Python?",
        "How do you write good Python code?",
        "What are functions in programming?"
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        query_embedding = embedding_service.generate_query_embedding(query)
        results = vector_store.similarity_search(query_embedding, k=3)

        for i, result in enumerate(results):
            print(f"  {i + 1}. [{result['metadata']['source']}] Distance: {result['distance']:.3f}")
            print(f"     {result['text'][:150]}...")

    # Step 5: Show collection stats
    stats = vector_store.get_collection_stats()
    print(f"\nCollection Statistics:")
    print(f"Total documents: {stats['total_documents']}")
    print(f"Sources: {stats['sources']}")


if __name__ == "__main__":
    test_vector_pipeline()