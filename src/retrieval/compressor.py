import re
from typing import List
from langchain_core.documents import Document
from src.utils.logger import logger

class ContextCompressor:
    """
    Compresses retrieved context documents to optimize LLM context window usage.
    Removes redundancy, duplicates, and boilerplate text.
    """
    def __init__(self, max_words_per_chunk: int = 300):
        self.max_words_per_chunk = max_words_per_chunk

    def clean_text(self, text: str) -> str:
        """
        Normalizes whitespaces, replaces multiple newlines, and strips leading/trailing spaces.
        """
        # Replace multiple spaces with a single space
        text = re.sub(r"[ \t]+", " ", text)
        # Replace 3 or more newlines with a double newline
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def remove_boilerplate_redundancy(self, documents: List[Document]) -> List[Document]:
        """
        Identifies and removes duplicate sentences or paragraphs across retrieved chunks
        to maximize information density.
        """
        seen_sentences = set()
        compressed_docs = []

        for doc in documents:
            content = doc.page_content
            # Split text by sentences (rough heuristic splitting by period, exclamation, question mark followed by space/newline)
            sentences = re.split(r'(?<=[.!?])\s+', content)
            
            unique_sentences = []
            for sentence in sentences:
                sentence_strip = sentence.strip()
                if not sentence_strip:
                    continue
                
                # Check normalized version of sentence to find duplicates
                norm_sentence = re.sub(r'\W+', '', sentence_strip).lower()
                
                # Ignore very short boilerplate sentences (e.g. "read more", "see also") if they are duplicated
                if len(norm_sentence) < 15:
                    if norm_sentence not in seen_sentences:
                        seen_sentences.add(norm_sentence)
                        unique_sentences.append(sentence_strip)
                else:
                    if norm_sentence not in seen_sentences:
                        seen_sentences.add(norm_sentence)
                        unique_sentences.append(sentence_strip)
            
            # Reconstruct content
            new_content = " ".join(unique_sentences)
            new_content = self.clean_text(new_content)
            
            # Only append if we still have content after compression
            if new_content:
                # Create a new Document object to avoid mutating the original documents stored in the database
                compressed_doc = Document(
                    page_content=new_content,
                    metadata=doc.metadata.copy()
                )
                # Keep track of compression ratio
                compressed_doc.metadata["original_length"] = len(content)
                compressed_doc.metadata["compressed_length"] = len(new_content)
                compressed_docs.append(compressed_doc)

        return compressed_docs

    def truncate_to_max_words(self, documents: List[Document]) -> List[Document]:
        """
        Limits the word count of each chunk to self.max_words_per_chunk
        to prevent a single giant document from consuming the entire context window.
        """
        for doc in documents:
            words = doc.page_content.split()
            if len(words) > self.max_words_per_chunk:
                truncated_text = " ".join(words[:self.max_words_per_chunk]) + "..."
                doc.page_content = truncated_text
                doc.metadata["truncated"] = True
        return documents

    def compress(self, documents: List[Document]) -> List[Document]:
        """
        Orchestrates the context compression pipeline.
        """
        if not documents:
            return []

        logger.info(f"Compressing {len(documents)} context documents...")
        original_char_count = sum(len(doc.page_content) for doc in documents)
        
        # 1. Deduplicate sentences
        compressed_docs = self.remove_boilerplate_redundancy(documents)
        
        # 2. Truncate long documents
        compressed_docs = self.truncate_to_max_words(compressed_docs)
        
        compressed_char_count = sum(len(doc.page_content) for doc in compressed_docs)
        compression_ratio = (1 - (compressed_char_count / (original_char_count or 1))) * 100
        
        logger.info(f"Compression complete. Char count reduced from {original_char_count} to {compressed_char_count} ({compression_ratio:.1f}% reduction).")
        return compressed_docs
