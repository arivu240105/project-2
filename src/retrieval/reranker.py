from typing import List, Tuple
from langchain_core.documents import Document
from src.utils.config import DEFAULT_RERANK_K
from src.utils.logger import logger

class CrossEncoderReranker:
    """
    Reranks candidate documents relative to a query using a Cross-Encoder model.
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """
        Loads the CrossEncoder model lazily on demand.
        """
        if self._model is None:
            self._init_model()
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

    def _init_model(self):
        """
        Loads the Cross-Encoder model from HuggingFace/SentenceTransformers.
        """
        logger.info(f"Loading Cross-Encoder reranking model: {self.model_name}...")
        try:
            from sentence_transformers import CrossEncoder
            # Load Cross-Encoder on CPU
            self._model = CrossEncoder(self.model_name, device="cpu")
            logger.info("Cross-Encoder reranker loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading Cross-Encoder model: {e}. Reranker will be disabled (bypass mode).")
            self._model = None


    def rerank(self, query: str, documents: List[Document], rerank_k: int = None) -> List[Document]:
        """
        Re-ranks a list of documents relative to the search query.
        Returns the top K ranked documents with their similarity score embedded in metadata.
        """
        k = rerank_k or DEFAULT_RERANK_K
        if not documents:
            return []

        # If model failed to load, bypass rerank and return top K
        if not self.model:
            logger.warning("Reranker model is not loaded. Bypassing reranking (returning raw candidates).")
            return documents[:k]

        try:
            logger.info(f"Reranking {len(documents)} candidate chunks for query: '{query}'...")
            
            # Form pairs of (query, document_text)
            pairs = [[query, doc.page_content] for doc in documents]
            
            # Predict similarity scores
            scores = self.model.predict(pairs)
            
            # Attach scores to document metadata and zip them
            scored_docs: List[Tuple[Document, float]] = []
            for doc, score in zip(documents, scores):
                # Save the rerank score as a float
                doc.metadata["rerank_score"] = float(score)
                scored_docs.append((doc, float(score)))
                
            # Sort documents by score in descending order
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # Select top K
            reranked_docs = [doc for doc, score in scored_docs[:k]]
            
            logger.info(f"Reranking complete. Selected top {len(reranked_docs)} chunks.")
            return reranked_docs
        except Exception as e:
            logger.error(f"Error during document reranking: {e}. Returning raw candidates.")
            return documents[:k]
