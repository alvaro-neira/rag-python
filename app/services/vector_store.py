import chromadb
from typing import List, Dict, Any
from langchain.schema import Document
from app.core.logging_config import get_logger, log_event
from app.core.metrics import metrics_recorder
from langfuse import observe
import os
from dotenv import load_dotenv

load_dotenv()


class VectorStore:
    def __init__(self, persist_directory: str = None):
        """Initialize Chroma vector store"""
        self.logger = get_logger("vector_store")
        
        # Use environment variable or default path
        if persist_directory is None:
            persist_directory = "data/chroma_db"
        
        # Convert to absolute path for clarity
        persist_directory = os.path.abspath(persist_directory)
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        log_event(
            self.logger, 
            "vector_store_path", 
            "ChromaDB path initialized",
            path=persist_directory
        )

        # Initialize Chroma client with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="rag_documents",
            metadata={"description": "RAG microservice document collection"}
        )

        collection_size = self.collection.count()
        log_event(
            self.logger, 
            "vector_store_initialized", 
            "Vector store initialized",
            collection_size=collection_size,
            persist_directory=persist_directory
        )

    def add_documents(self, documents: List[Document], embeddings: List[List[float]]):
        """Add documents and their embeddings to the vector store"""
        log_event(
            self.logger, 
            "documents_add_started", 
            "Adding documents to vector store",
            document_count=len(documents)
        )

        try:
            # Prepare data for Chroma
            ids = [f"doc_{i}" for i in range(len(documents))]
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            # Add to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )

            total_count = self.collection.count()
            
            # Record metrics
            metrics_recorder.record_vector_store_operation("add", success=True)
            metrics_recorder.update_vector_store_size(total_count)
            
            log_event(
                self.logger, 
                "documents_add_completed", 
                "Documents added to vector store",
                documents_added=len(documents),
                total_collection_size=total_count
            )
        except Exception as e:
            metrics_recorder.record_vector_store_operation("add", success=False)
            metrics_recorder.record_error(
                error_type=type(e).__name__,
                operation="vector_store_add"
            )
            raise

    @observe(name="similarity_search")
    def similarity_search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i]
                    })

            # Record metrics
            metrics_recorder.record_vector_store_operation("search", success=True)
            
            return formatted_results
        
        except Exception as e:
            metrics_recorder.record_vector_store_operation("search", success=False)
            metrics_recorder.record_error(
                error_type=type(e).__name__,
                operation="vector_store_search"
            )
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        count = self.collection.count()

        # Get some sample documents to analyze sources
        sample_results = self.collection.get(limit=count, include=["metadatas"])
        sources = {}

        if sample_results['metadatas']:
            for metadata in sample_results['metadatas']:
                source = metadata.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1

        return {
            'total_documents': count,
            'sources': sources
        }
