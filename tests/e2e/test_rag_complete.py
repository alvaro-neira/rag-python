"""
Doesn't need the FastAPI server running
"""

from app.services.rag_service import RAGService


def test_complete_rag():
    print("Testing Complete RAG Pipeline")

    # Initialize RAG service
    rag_service = RAGService()

    # Test ingestion (using small sample to keep costs reasonable)
    print("\nTesting document ingestion...")
    # Note: This will use existing documents in vector store or ingest new ones

    # Test queries
    test_questions = [
        "What is a variable in Python?",
        "How should I name my Python functions according to PEP 8?",
        "What are the different types of errors in Python?",
        "How do you define a function in Python?"
    ]

    for question in test_questions:
        print(f"\n" + "=" * 60)
        print(f"Question: {question}")
        print("-" * 60)

        result = rag_service.query(question)

        print(f"Answer:")
        print(result['answer'])

        print(f"\nSources ({len(result['sources'])} found):")
        for i, source in enumerate(result['sources'][:3]):  # Show top 3 sources
            print(f"  {i + 1}. [{source['source']}] Distance: {source['distance']:.3f}")
            print(f"     {source['text']}")


if __name__ == "__main__":
    test_complete_rag()
