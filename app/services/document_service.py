import requests
from bs4 import BeautifulSoup
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from app.core.logging_config import get_logger, log_event, log_error
from langfuse import observe
from dotenv import load_dotenv

load_dotenv()


@observe(name="document_loading_think_python")
def load_think_python() -> str:
    """Load the Think Python book content"""
    logger = get_logger("document_service")
    log_event(logger, "think_python_load_started", "Loading Think Python book")

    # Think Python has multiple chapters, let's get the main chapters
    base_url = "https://allendowney.github.io/ThinkPython/"
    chapters = [f"chap{i:02d}.html" for i in range(1, 20)]

    all_content = []

    for chapter in chapters:
        try:
            url = base_url + chapter
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract main content (remove navigation, headers, etc.)
            main_content = soup.find('main') or soup.find('div', class_='content') or soup.body
            if main_content:
                text = main_content.get_text(strip=True, separator=' ')
                all_content.append(f"Chapter: {chapter}\n\n{text}")
                log_event(logger, "chapter_loaded", f"Loaded chapter", chapter=chapter)

        except Exception as e:
            log_error(logger, e, {"operation": "load_think_python_chapter", "chapter": chapter})
            continue

    return "\n\n".join(all_content)


@observe(name="document_loading_pep8")
def load_pep8() -> str:
    """Load PEP 8 content"""
    logger = get_logger("document_service")
    log_event(logger, "pep8_load_started", "Loading PEP 8")

    try:
        url = "https://peps.python.org/pep-0008/"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # PEP 8 content is in the main section
        main_content = soup.find('section', id='pep-content') or soup.find('div', class_='section')
        if main_content:
            text = main_content.get_text(strip=True, separator=' ')
            log_event(logger, "pep8_loaded", "PEP 8 loaded successfully")
            return text
        else:
            logger.warning(
                "PEP 8 content not found",
                extra={"event_type": "pep8_content_missing"}
            )
            return ""

    except Exception as e:
        log_error(logger, e, {"operation": "load_pep8"})
        return ""


class DocumentService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.logger = get_logger("document_service")

    @observe(name="document_chunking")
    def chunk_text(self, text: str, source: str) -> List[Document]:
        """Split text into chunks"""
        log_event(
            self.logger, 
            "text_chunking_started", 
            "Starting text chunking",
            source=source,
            text_length=len(text)
        )
        chunks = self.text_splitter.split_text(text)
        documents = []

        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={"source": source, "chunk_id": i, "total_chunks": len(chunks)}
            )
            documents.append(doc)

        log_event(
            self.logger, 
            "text_chunking_completed", 
            "Text chunking completed",
            source=source,
            chunks_created=len(chunks)
        )
        return documents

    def load_all_documents(self) -> List[Document]:
        """Load and chunk all documents"""
        all_documents = []

        # Load Think Python
        think_python_text = load_think_python()
        if think_python_text:
            think_python_docs = self.chunk_text(think_python_text, "Think Python")
            all_documents.extend(think_python_docs)

        # Load PEP 8
        pep8_text = load_pep8()
        if pep8_text:
            pep8_docs = self.chunk_text(pep8_text, "PEP 8")
            all_documents.extend(pep8_docs)

        log_event(
            self.logger, 
            "document_loading_completed", 
            "All documents loaded",
            total_documents=len(all_documents)
        )
        return all_documents
