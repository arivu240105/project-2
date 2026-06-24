from typing import List
from langchain_core.documents import Document
from src.utils.config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from src.utils.logger import logger

class DocSplitter:
    """
    Splits text documents into manageable chunks for vector database ingestion.
    """
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or DEFAULT_CHUNK_OVERLAP
        self._splitter = None

    @property
    def splitter(self):
        if self._splitter is None:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            self._splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        return self._splitter

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Splits a list of Documents and adds detailed chunk indexes to metadata.
        """
        if not documents:
            return []
            
        logger.info(f"Splitting {len(documents)} documents with chunk_size={self.chunk_size}, overlap={self.chunk_overlap}...")
        
        split_docs = self.splitter.split_documents(documents)
        
        # Post-process metadata to add chunk identifier info
        source_chunk_counts = {}
        for doc in split_docs:
            source = doc.metadata.get("source", "unknown")
            source_chunk_counts[source] = source_chunk_counts.get(source, 0) + 1
            
            # Enrich metadata
            doc.metadata.update({
                "chunk_index": source_chunk_counts[source] - 1,
                "chunk_size": len(doc.page_content),
                # Ensure a clean title is present
                "title": doc.metadata.get("title") or doc.metadata.get("file_name") or "Untitled"
            })
            
        # Write total chunks to each document's metadata
        for doc in split_docs:
            source = doc.metadata.get("source", "unknown")
            doc.metadata["total_chunks_for_source"] = source_chunk_counts[source]

        logger.info(f"Splitting complete. Generated {len(split_docs)} chunks from {len(documents)} documents.")
        return split_docs
