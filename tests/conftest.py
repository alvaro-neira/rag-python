import pytest
from dotenv import load_dotenv

@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Load environment variables for testing"""
    load_dotenv()

@pytest.fixture
def sample_document():
    """Sample document for testing"""
    from langchain.schema import Document
    return Document(
        page_content="This is a sample document for testing purposes.",
        metadata={"source": "test", "chunk_id": 0}
    )

@pytest.fixture
def sample_documents():
    """Multiple sample documents for testing"""
    from langchain.schema import Document
    return [
        Document(
            page_content=f"Sample document {i} content.",
            metadata={"source": "test", "chunk_id": i}
        )
        for i in range(3)
    ]