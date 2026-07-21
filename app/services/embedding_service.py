from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from typing import List
from app.core.logging_config import get_logger, log_event, log_error
from app.core.metrics import metrics_recorder
from langfuse import observe
import os
import time
from dotenv import load_dotenv

load_dotenv()


class EmbeddingService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",  # Cost-effective and good quality
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.logger = get_logger("embedding_service")

    @observe(name="embedding_computation_documents")
    def generate_embeddings(self, documents: List[Document]) -> List[List[float]]:
        """Generate embeddings for a list of documents"""
        start_time = time.time()
        log_event(
            self.logger, 
            "embedding_generation_started", 
            "Starting embedding generation",
            document_count=len(documents)
        )

        # Extract text content from documents
        texts = [doc.page_content for doc in documents]

        try:
            # Generate embeddings in batches to avoid rate limits
            embeddings = self.embeddings.embed_documents(texts)
            
            duration = time.time() - start_time
            
            # Record metrics
            metrics_recorder.record_embeddings_generated(
                count=len(embeddings),
                embedding_type="document",
                duration_seconds=duration
            )
            
            log_event(
                self.logger, 
                "embedding_generation_completed", 
                "Embedding generation completed",
                embeddings_generated=len(embeddings)
            )
            return embeddings

        except Exception as e:
            duration = time.time() - start_time
            metrics_recorder.record_error(
                error_type=type(e).__name__,
                operation="embedding_generation"
            )
            log_error(self.logger, e, {
                "operation": "embedding_generation",
                "document_count": len(documents)
            })
            raise

    @observe(name="embedding_computation_query")
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a single query"""
        start_time = time.time()
        try:
            embedding = self.embeddings.embed_query(query)
            
            duration = time.time() - start_time
            
            # Record metrics
            metrics_recorder.record_embeddings_generated(
                count=1,
                embedding_type="query",
                duration_seconds=duration
            )
            
            return embedding
        except Exception as e:
            duration = time.time() - start_time
            metrics_recorder.record_error(
                error_type=type(e).__name__,
                operation="query_embedding_generation"
            )
            log_error(self.logger, e, {
                "operation": "query_embedding_generation",
                "query": query
            })
            raise