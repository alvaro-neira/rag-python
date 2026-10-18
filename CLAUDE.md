# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with required environment variables:
# OPENAI_API_KEY=...
# LANGFUSE_PUBLIC_KEY=pk-...
# LANGFUSE_SECRET_KEY=sk-...
# LANGFUSE_HOST=https://....cloud.langfuse.com
```

### Running the Application
```bash
# Run locally (development)
python -m app.main

# Run with Docker
docker compose up --build

# Health check
curl http://localhost:8000/health
```

### Testing
```bash
# Install test dependencies (if not already installed)
pip install pytest

# Run unit tests
pytest tests/ -v

# Run integration tests
python test_api.py
python test_rag_complete.py
python test_vector_store.py
python test_documents.py
```

## Architecture Overview

This is a RAG (Retrieval-Augmented Generation) microservice built with FastAPI that processes documents and answers questions using OpenAI's GPT models with observability via Langfuse.

### Core Components

**Service Layer (`app/services/`)**:
- `rag_service.py`: Main orchestrator that coordinates document ingestion and query processing with Langfuse tracing
- `document_service.py`: Handles document loading and text preprocessing 
- `embedding_service.py`: Manages OpenAI text-embedding-3-small model interactions
- `vector_store.py`: ChromaDB integration for persistent vector storage

**API Layer (`app/api/`)**:
- `endpoints.py`: FastAPI endpoints for `/health`, `/ingest`, and `/query`
- Request/response models using Pydantic

**Configuration (`app/core/`)**:
- `config.py`: Application configuration management

### Key Technical Details

- **Vector Database**: ChromaDB (local/persistent) stored in `./data/chroma_db/`
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Text Chunking**: 1000 characters with 200 character overlap
- **LLM**: GPT-3.5-turbo with temperature 0.1
- **Observability**: Langfuse tracing with `@observe()` decorators
- **Framework**: FastAPI with uvicorn server on port 8000

### Data Flow

1. **Ingestion**: Documents → DocumentService → EmbeddingService → VectorStore (ChromaDB)
2. **Query**: Question → EmbeddingService → VectorStore similarity search → LLM with context → Response

### Environment Variables Required

The application requires these environment variables in a `.env` file:
- `OPENAI_API_KEY`: OpenAI API key for embeddings and LLM
- `LANGFUSE_PUBLIC_KEY`: Langfuse public key for observability
- `LANGFUSE_SECRET_KEY`: Langfuse secret key
- `LANGFUSE_HOST`: Langfuse host URL

### Docker Configuration

The application is containerized with Python 3.11-slim base image and includes:
- Volume mounting for persistent ChromaDB storage (`./data:/app/data`)
- Health check endpoint
- Environment variable passthrough from host