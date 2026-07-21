from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService


def test_document_pipeline():
    # Load documents
    doc_service = DocumentService()
    documents = doc_service.load_all_documents()

    print(f"\nDocument Summary:")
    print(f"Total chunks: {len(documents)}")

    # Test embeddings with just a few documents first
    print(f"\nTesting embeddings...")
    embedding_service = EmbeddingService()

    # Test with first 5 documents to avoid high API costs
    test_docs = documents[:5]
    embeddings = embedding_service.generate_embeddings(test_docs)

    print(f"Generated embeddings shape: {len(embeddings)} x {len(embeddings[0])}")
    print(f"Each embedding has {len(embeddings[0])} dimensions")

    # Test query embedding
    test_query = "What is a variable in Python?"
    query_embedding = embedding_service.generate_query_embedding(test_query)
    print(f"Query embedding shape: {len(query_embedding)} dimensions")

    # Show sample from each source
    sources = set(doc.metadata['source'] for doc in documents)
    for source in sources:
        source_docs = [doc for doc in documents if doc.metadata['source'] == source]
        print(f"\n{source}: {len(source_docs)} chunks")
        if source_docs:
            print(f"Sample chunk: {source_docs[0].page_content[:150]}...")


if __name__ == "__main__":
    test_document_pipeline()