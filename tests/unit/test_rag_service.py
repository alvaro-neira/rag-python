import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.rag_service import RAGService, _create_rag_prompt
from langchain_core.documents import Document

class TestRAGService:
    @pytest.fixture
    def rag_service(self):
        return RAGService()
    
    def test_create_rag_prompt(self, rag_service):
        """Test RAG prompt creation"""
        question = "What is a variable?"
        context = "A variable is a named storage location."
        
        prompt = _create_rag_prompt(question, context)
        
        assert question in prompt
        assert context in prompt
        assert "Context from relevant documents:" in prompt
    
    @patch('app.services.rag_service.RAGService.__init__')
    def test_query_no_results(self, mock_init, rag_service):
        """Test query when no documents found"""
        mock_init.return_value = None
        rag_service.vector_store = Mock()
        rag_service.embedding_service = Mock()
        
        # Mock empty search results
        rag_service.embedding_service.generate_query_embedding.return_value = [0.1] * 1536
        rag_service.vector_store.similarity_search.return_value = []
        
        result = rag_service.query("test question")
        
        assert "couldn't find any relevant information" in result["answer"]
        assert result["sources"] == []

    # INGESTION TESTS
    @patch('app.services.rag_service.RAGService.__init__')
    def test_ingest_documents_success(self, mock_init, rag_service):
        """Test successful document ingestion"""
        mock_init.return_value = None
        
        # Mock dependencies
        rag_service.document_service = Mock()
        rag_service.embedding_service = Mock()
        rag_service.vector_store = Mock()
        
        # Mock document data
        mock_documents = [
            Document(page_content="Test content 1", metadata={"source": "test1.py", "chunk_id": 0}),
            Document(page_content="Test content 2", metadata={"source": "test2.py", "chunk_id": 1})
        ]
        mock_embeddings = [[0.1] * 1536, [0.2] * 1536]
        
        rag_service.document_service.load_all_documents.return_value = mock_documents
        rag_service.embedding_service.generate_embeddings.return_value = mock_embeddings
        rag_service.vector_store.get_collection_stats.return_value = {
            'total_documents': 2,
            'sources': {'test1.py': 1, 'test2.py': 1}
        }
        
        result = rag_service.ingest_documents()
        
        # Verify calls
        rag_service.document_service.load_all_documents.assert_called_once()
        rag_service.embedding_service.generate_embeddings.assert_called_once_with(mock_documents)
        rag_service.vector_store.add_documents.assert_called_once_with(mock_documents, mock_embeddings)
        
        # Verify result
        assert result["status"] == "success"
        assert result["total_documents"] == 2
        assert "test1.py" in result["sources"]
        assert "Successfully ingested" in result["message"]

    @patch('app.services.rag_service.RAGService.__init__')
    def test_ingest_documents_empty(self, mock_init, rag_service):
        """Test ingestion with empty document set"""
        mock_init.return_value = None
        
        rag_service.document_service = Mock()
        rag_service.embedding_service = Mock()
        rag_service.vector_store = Mock()
        
        rag_service.document_service.load_all_documents.return_value = []
        rag_service.embedding_service.generate_embeddings.return_value = []
        rag_service.vector_store.get_collection_stats.return_value = {
            'total_documents': 0,
            'sources': {}
        }
        
        result = rag_service.ingest_documents()
        
        assert result["status"] == "success"
        assert result["total_documents"] == 0
        assert result["sources"] == {}

    @patch('app.services.rag_service.RAGService.__init__')
    def test_ingest_documents_error_handling(self, mock_init, rag_service):
        """Test ingestion error handling"""
        mock_init.return_value = None
        
        rag_service.document_service = Mock()
        rag_service.document_service.load_all_documents.side_effect = Exception("Document loading failed")
        
        with pytest.raises(Exception, match="Document loading failed"):
            rag_service.ingest_documents()

    # QUERY TESTS
    @patch('app.services.rag_service.RAGService.__init__')
    def test_query_success_with_results(self, mock_init, rag_service):
        """Test successful query with results"""
        mock_init.return_value = None
        
        # Mock dependencies
        rag_service.embedding_service = Mock()
        rag_service.vector_store = Mock()
        rag_service.llm = Mock()
        
        # Mock search results
        mock_search_results = [
            {
                'text': 'A variable is a named storage location in memory.',
                'metadata': {'source': 'python_basics.py', 'chunk_id': 5},
                'distance': 0.2
            },
            {
                'text': 'Variables in Python are dynamically typed.',
                'metadata': {'source': 'python_types.py', 'chunk_id': 10},
                'distance': 0.3
            }
        ]
        
        rag_service.embedding_service.generate_query_embedding.return_value = [0.1] * 1536
        rag_service.vector_store.similarity_search.return_value = mock_search_results
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "A variable is a named storage location that holds data."
        rag_service.llm.invoke.return_value = mock_response
        
        result = rag_service.query("What is a variable?")
        
        # Verify calls
        rag_service.embedding_service.generate_query_embedding.assert_called_once_with("What is a variable?")
        rag_service.vector_store.similarity_search.assert_called_once_with([0.1] * 1536, k=5)
        rag_service.llm.invoke.assert_called_once()
        
        # Verify result structure
        assert "answer" in result
        assert "sources" in result
        assert result["answer"] == "A variable is a named storage location that holds data."
        assert len(result["sources"]) == 2
        assert result["sources"][0]["source"] == "python_basics.py"
        assert result["sources"][0]["distance"] == 0.2

    @patch('app.services.rag_service.RAGService.__init__')
    def test_query_with_custom_k_value(self, mock_init, rag_service):
        """Test query with different k values"""
        mock_init.return_value = None
        
        rag_service.embedding_service = Mock()
        rag_service.vector_store = Mock()
        rag_service.llm = Mock()
        
        rag_service.embedding_service.generate_query_embedding.return_value = [0.1] * 1536
        rag_service.vector_store.similarity_search.return_value = []
        
        rag_service.query("test question", k=10)
        
        rag_service.vector_store.similarity_search.assert_called_once_with([0.1] * 1536, k=10)

    @patch('app.services.rag_service.RAGService.__init__')
    def test_query_embedding_error(self, mock_init, rag_service):
        """Test query error handling for embedding failures"""
        mock_init.return_value = None
        
        rag_service.embedding_service = Mock()
        rag_service.embedding_service.generate_query_embedding.side_effect = Exception("Embedding failed")
        
        with pytest.raises(Exception, match="Embedding failed"):
            rag_service.query("test question")

    @patch('app.services.rag_service.RAGService.__init__')
    def test_query_search_error(self, mock_init, rag_service):
        """Test query error handling for search failures"""
        mock_init.return_value = None
        
        rag_service.embedding_service = Mock()
        rag_service.vector_store = Mock()
        
        rag_service.embedding_service.generate_query_embedding.return_value = [0.1] * 1536
        rag_service.vector_store.similarity_search.side_effect = Exception("Search failed")
        
        with pytest.raises(Exception, match="Search failed"):
            rag_service.query("test question")

    @patch('app.services.rag_service.RAGService.__init__')
    def test_query_llm_error(self, mock_init, rag_service):
        """Test query error handling for LLM failures"""
        mock_init.return_value = None
        
        rag_service.embedding_service = Mock()
        rag_service.vector_store = Mock()
        rag_service.llm = Mock()
        
        rag_service.embedding_service.generate_query_embedding.return_value = [0.1] * 1536
        rag_service.vector_store.similarity_search.return_value = [
            {'text': 'test', 'metadata': {'source': 'test.py'}, 'distance': 0.1}
        ]
        rag_service.llm.invoke.side_effect = Exception("LLM failed")
        
        with pytest.raises(Exception, match="LLM failed"):
            rag_service.query("test question")

    @patch('app.services.rag_service.RAGService.__init__')
    def test_query_context_building(self, mock_init, rag_service):
        """Test context building from search results"""
        mock_init.return_value = None
        
        rag_service.embedding_service = Mock()
        rag_service.vector_store = Mock()
        rag_service.llm = Mock()
        
        # Mock search results with long text to test truncation
        long_text = "A" * 300
        mock_search_results = [
            {
                'text': long_text,
                'metadata': {'source': 'test.py', 'chunk_id': 1},
                'distance': 0.1
            }
        ]
        
        rag_service.embedding_service.generate_query_embedding.return_value = [0.1] * 1536
        rag_service.vector_store.similarity_search.return_value = mock_search_results
        
        mock_response = Mock()
        mock_response.content = "test answer"
        rag_service.llm.invoke.return_value = mock_response
        
        result = rag_service.query("test question")
        
        # Verify source text is truncated
        assert len(result["sources"][0]["text"]) == 203  # 200 chars + "..."
        assert result["sources"][0]["text"].endswith("...")

    @patch('app.services.rag_service.RAGService.__init__')
    def test_query_response_format(self, mock_init, rag_service):
        """Test query response format validation"""
        mock_init.return_value = None
        
        rag_service.embedding_service = Mock()
        rag_service.vector_store = Mock()
        rag_service.llm = Mock()
        
        mock_search_results = [
            {
                'text': 'test content',
                'metadata': {'source': 'test.py', 'chunk_id': 1},
                'distance': 0.1
            }
        ]
        
        rag_service.embedding_service.generate_query_embedding.return_value = [0.1] * 1536
        rag_service.vector_store.similarity_search.return_value = mock_search_results
        
        mock_response = Mock()
        mock_response.content = "test answer"
        rag_service.llm.invoke.return_value = mock_response
        
        result = rag_service.query("test question")
        
        # Verify response format
        assert isinstance(result, dict)
        assert "answer" in result
        assert "sources" in result
        assert isinstance(result["sources"], list)
        assert len(result["sources"]) == 1
        
        source = result["sources"][0]
        assert "page" in source
        assert "text" in source
        assert "source" in source
        assert "distance" in source

# Install pytest first: pip install pytest
# Run tests: pytest tests/ -v