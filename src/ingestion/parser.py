import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from pypdf import PdfReader
from langchain_core.documents import Document
from src.utils.logger import logger

class DocParser:
    """
    Parses various document types (PDF, TXT, MD) into a list of LangChain Document objects.
    """
    
    @staticmethod
    def parse_pdf(file_path: Path) -> List[Document]:
        """
        Parses a PDF file page-by-page.
        """
        documents = []
        try:
            logger.info(f"Parsing PDF: {file_path}")
            reader = PdfReader(str(file_path))
            file_name = file_path.name
            
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text or not text.strip():
                    continue
                
                # Metadata dictionary
                metadata = {
                    "source": str(file_path),
                    "file_name": file_name,
                    "type": "pdf",
                    "page": page_idx + 1,
                    "total_pages": len(reader.pages),
                    "title": file_name.replace(".pdf", ""),
                    "timestamp": datetime.now().isoformat()
                }
                
                documents.append(Document(page_content=text, metadata=metadata))
            
            logger.info(f"Successfully parsed PDF {file_name} into {len(documents)} pages.")
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            
        return documents

    @staticmethod
    def parse_text(file_path: Path) -> List[Document]:
        """
        Parses text files (.txt, .md).
        """
        documents = []
        try:
            logger.info(f"Parsing text file: {file_path}")
            file_name = file_path.name
            suffix = file_path.suffix.lower().replace(".", "")
            
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            if content.strip():
                metadata = {
                    "source": str(file_path),
                    "file_name": file_name,
                    "type": suffix,
                    "title": file_name.replace(f".{suffix}", ""),
                    "timestamp": datetime.now().isoformat()
                }
                documents.append(Document(page_content=content, metadata=metadata))
                
            logger.info(f"Successfully parsed text file {file_name}.")
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {e}")
            
        return documents

    @classmethod
    def parse(cls, file_path: Path) -> List[Document]:
        """
        Automatically detects file extension and routes to the correct parser.
        """
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return []
            
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return cls.parse_pdf(file_path)
        elif suffix in [".txt", ".md", ".rst", ".json", ".py", ".js", ".ts", ".html", ".css"]:
            return cls.parse_text(file_path)
        else:
            # Fallback parsing as text file if we can read it
            logger.warning(f"Unsupported extension {suffix} for {file_path}. Trying fallback text parser.")
            return cls.parse_text(file_path)
