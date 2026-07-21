from unittest.mock import patch
from app.services.document_service import DocumentService


class TestDocumentService:

    def test_chunk_text(self):
        """Test text chunking without external dependencies"""
        doc_service = DocumentService()

        # Create test text longer than chunk size
        test_text = "A" * 1500  # 1500 characters

        chunks = doc_service.chunk_text(test_text, "test_source")

        assert len(chunks) >= 1  # Should create at least one chunk
        assert all(chunk.metadata["source"] == "test_source" for chunk in chunks)
        assert all(len(chunk.page_content) <= 1200 for chunk in chunks)  # Within chunk size + overlap

    @patch('app.services.document_service.load_pep8')
    def test_load_all_documents_with_pep8(self, mock_load_pep8):
        """Test load_all_documents with mocked PEP 8 content"""
        mock_load_pep8.return_value = "Sample PEP 8 content for testing"
        
        with patch('app.services.document_service.load_think_python') as mock_think_python:
            mock_think_python.return_value = "Sample Think Python content"
            
            doc_service = DocumentService()
            documents = doc_service.load_all_documents()
            
            assert len(documents) > 0
            assert any("Think Python" in doc.metadata["source"] for doc in documents)
            assert any("PEP 8" in doc.metadata["source"] for doc in documents)
