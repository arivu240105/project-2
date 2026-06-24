from typing import List
from langchain_core.documents import Document
from src.vectorstore.store import VectorStoreManager
from src.utils.config import DEFAULT_RETRIEVE_K
from src.utils.logger import logger

class HybridRetriever:
    """
    Combines Dense retrieval (FAISS) and Sparse retrieval (BM25)
    using LangChain's EnsembleRetriever.
    """
    def __init__(self, store_manager: VectorStoreManager):
        self.store_manager = store_manager
        self.dense_retriever = None
        self.sparse_retriever = None
        self.ensemble_retriever = None
        self.last_doc_count = 0
        self.last_k = None

    def update_retrievers(self, retrieve_k: int = None):
        """
        Rebuilds retrieval engines (Dense and Sparse) from the current state of vector_store.
        """
        k = retrieve_k or DEFAULT_RETRIEVE_K
        
        # Check if vector store is initialized
        if self.store_manager.vector_store is None:
            logger.warning("Vector store is not initialized. Hybrid retrieval will be unavailable.")
            self.ensemble_retriever = None
            self.last_doc_count = 0
            self.last_k = k
            return
 
        all_docs = self.store_manager.get_all_documents()
        if not all_docs:
            logger.warning("No documents indexed. Hybrid retrieval is unavailable.")
            self.ensemble_retriever = None
            self.last_doc_count = 0
            self.last_k = k
            return
 
        try:
            from langchain_community.retrievers import BM25Retriever
            try:
                from langchain.retrievers import EnsembleRetriever
            except ImportError:
                from langchain_classic.retrievers import EnsembleRetriever

            logger.info(f"Rebuilding retrievers for {len(all_docs)} documents, retrieving top {k}...")
            
            # 1. Initialize Dense Retriever
            self.dense_retriever = self.store_manager.vector_store.as_retriever(
                search_kwargs={"k": k}
            )
            
            # 2. Initialize Sparse Retriever (BM25)
            # BM25 requires all documents to calculate term frequencies
            self.sparse_retriever = BM25Retriever.from_documents(all_docs)
            self.sparse_retriever.k = k
            
            # 3. Combine in EnsembleRetriever
            # Weights are set to 0.5 each for equal weighting of semantic and keyword search
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[self.dense_retriever, self.sparse_retriever],
                weights=[0.5, 0.5]
            )
            
            # Track state to avoid redundant rebuilds
            self.last_doc_count = len(all_docs)
            self.last_k = k
            logger.info("Hybrid Ensemble Retriever successfully initialized.")
        except Exception as e:
            logger.error(f"Error initializing hybrid retriever: {e}")
            self.ensemble_retriever = None
            self.last_doc_count = 0
            self.last_k = k
 
    def retrieve(self, query: str, retrieve_k: int = None) -> List[Document]:
        """
        Retrieves matching documents using Hybrid Ensemble Retriever.
        If retriever is not ready, falls back to direct FAISS search if possible.
        """
        k = retrieve_k or DEFAULT_RETRIEVE_K
        
        # Check current document count from memory
        all_docs = self.store_manager.get_all_documents()
        current_doc_count = len(all_docs)
        
        # Only rebuild if state has changed or not yet initialized
        if (self.ensemble_retriever is None or 
            current_doc_count != self.last_doc_count or 
            k != self.last_k):
            logger.info("Retriever state out of date or uninitialized. Rebuilding...")
            self.update_retrievers(retrieve_k=k)
        
        if not self.ensemble_retriever:
            # Fallback to direct FAISS similarity search if available
            if self.store_manager.vector_store:
                logger.info("Fallback: Performing direct FAISS similarity search.")
                return self.store_manager.vector_store.similarity_search(query, k=k)
            logger.warning("No documents in database. Empty retrieval list returned.")
            return []
 
        try:
            logger.info(f"Performing hybrid retrieval for query: '{query}'...")
            results = self.ensemble_retriever.invoke(query)
            
            # RRF sometimes returns more than K documents due to combining. Limit to K.
            results = results[:k]
            
            logger.info(f"Retrieved {len(results)} candidate chunks.")
            return results
        except Exception as e:
            logger.error(f"Error during hybrid retrieval: {e}")
            # Final fallback
            if self.store_manager.vector_store:
                return self.store_manager.vector_store.similarity_search(query, k=k)
            return []

