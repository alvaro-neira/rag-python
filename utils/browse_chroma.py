import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = "../data/chroma_db"


def browse_chroma_data():
    # Connect to your existing database
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Get your collection
    collection = client.get_or_create_collection("rag_documents")

    print("=" * 60)
    print("CHROMA DATABASE OVERVIEW")
    print("=" * 60)

    # Basic stats
    count = collection.count()
    print(f"Total documents: {count}")

    # Get all documents (with limit for performance)
    results = collection.get(
        limit=count,  # Get all, but be careful with large collections
        include=["documents", "metadatas", "embeddings"]
    )

    print(f"\nSOURCES BREAKDOWN:")
    sources = {}
    for metadata in results['metadatas']:
        source = metadata.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1

    for source, count in sources.items():
        print(f"  {source}: {count} chunks")

    print(f"\nSAMPLE DOCUMENTS:")
    for i in range(min(5, len(results['documents']))):
        doc = results['documents'][i]
        metadata = results['metadatas'][i]
        embedding_size = len(results['embeddings'][i]) if results['embeddings'].size > 0 else 0

        print(f"\n--- Document {i + 1} ---")
        print(f"Source: {metadata.get('source', 'unknown')}")
        print(f"Chunk ID: {metadata.get('chunk_id', 'unknown')}")
        print(f"Embedding dimensions: {embedding_size}")
        print(f"Content preview: {doc[:200]}...")
        print(f"Content length: {len(doc)} characters")

    print(f"\nEMBEDDING ANALYSIS:")
    if results['embeddings'].size > 0:
        embedding = results['embeddings'][0]
        print(f"Embedding dimensions: {len(embedding)}")
        print(f"Sample values: {embedding[:5]}...")  # First 5 values
        print(f"Value range: {min(embedding):.4f} to {max(embedding):.4f}")
    else:
        print(f"\n embeddings not found in collection. Ensure they were generated and stored correctly.")


def search_documents(query_text):
    """Search for specific content"""
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection("rag_documents")

    # Simple text search (not semantic)
    results = collection.get(
        where_document={"$contains": query_text},
        include=["documents", "metadatas"]
    )

    print(f"\nSEARCH RESULTS for '{query_text}':")
    print(f"Found {len(results['documents'])} documents")

    for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
        print(f"\n--- Result {i + 1} ---")
        print(f"Source: {metadata.get('source')}")
        print(f"Chunk: {metadata.get('chunk_id')}")
        print(f"Content: {doc[:300]}...")


if __name__ == "__main__":
    browse_chroma_data()

    # Optional: Search for specific content
    search_query = input("\nEnter search term (or press Enter to skip): ")
    if search_query.strip():
        search_documents(search_query)
