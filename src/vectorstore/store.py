import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from src.utils.config import VECTOR_DB_DIR, EMBEDDING_MODEL_NAME
from src.utils.logger import logger

class LazyHuggingFaceEmbeddings(Embeddings):
    """
    A lazy-loading wrapper for HuggingFaceEmbeddings.
    Prevents loading the heavy model and PyTorch modules on startup.
    """
    def __init__(self, model_name: str, model_kwargs: dict, encode_kwargs: dict):
        self.model_name = model_name
        self.model_kwargs = model_kwargs
        self.encode_kwargs = encode_kwargs
        self._embeddings = None

    @property
    def embeddings(self):
        if self._embeddings is None:
            logger.info(f"Lazily initializing HuggingFaceEmbeddings: {self.model_name}...")
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs=self.model_kwargs,
                encode_kwargs=self.encode_kwargs
            )
            logger.info("Embeddings model initialized successfully.")
        return self._embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

class VectorStoreManager:
    """
    Manages the local FAISS vector store database.
    Initializes embeddings, creates/saves/loads indices, and adds documents.
    """
    def __init__(self, index_name: str = "devdocs_faiss"):
        self.index_name = index_name
        self.index_path = VECTOR_DB_DIR / index_name
        self._embeddings = None
        self._vector_store: Optional[Any] = None
        self._loaded = False

    @property
    def embeddings(self) -> Embeddings:
        """
        Initializes the SentenceTransformers embedding model lazily on demand.
        """
        if self._embeddings is None:
            self._embeddings = self._init_embeddings()
        return self._embeddings

    @property
    def vector_store(self) -> Optional[Any]:
        """
        Loads the FAISS vector store lazily on demand.
        """
        if not self._loaded:
            self._load_vector_store()
        return self._vector_store

    @vector_store.setter
    def vector_store(self, value):
        self._vector_store = value
        self._loaded = True

    def _init_embeddings(self) -> Embeddings:
        """
        Initializes the SentenceTransformers embedding model.
        """
        logger.info(f"Configuring lazy embedding model: {EMBEDDING_MODEL_NAME}...")
        try:
            model_kwargs = {'device': 'cpu'}
            encode_kwargs = {'normalize_embeddings': True} # standard for BGE models
            embeddings = LazyHuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL_NAME,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
            logger.info("Lazy embeddings configuration completed.")
            return embeddings
        except Exception as e:
            logger.error(f"Error initializing embeddings model: {e}")
            raise e

    def _load_vector_store(self):
        """
        Loads the FAISS index from disk if it exists.
        """
        self._loaded = True
        if self.index_path.exists() and (self.index_path / "index.faiss").exists():
            logger.info(f"Loading existing FAISS index from {self.index_path}...")
            try:
                from langchain_community.vectorstores import FAISS
                self._vector_store = FAISS.load_local(
                    folder_path=str(self.index_path),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True # Required by LangChain to deserialize python pickles safely
                )
                logger.info("FAISS index loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}. Reinitializing database...")
                self._vector_store = None
        else:
            logger.info(f"No existing FAISS index found at {self.index_path}. Ready to initialize on first ingest.")
            self._vector_store = None

    def save(self):
        """
        Persists the current FAISS index to disk.
        """
        if self.vector_store:
            try:
                self.index_path.mkdir(parents=True, exist_ok=True)
                self.vector_store.save_local(str(self.index_path))
                logger.info(f"Saved FAISS index to {self.index_path}")
            except Exception as e:
                logger.error(f"Error saving FAISS index: {e}")
        else:
            logger.warning("No vector store instance to save.")

    def save_metadata(self):
        """
        Saves index metadata (chunk count, size, sources list) to a fast-to-read JSON file.
        """
        try:
            summary = self.get_ingested_sources_summary()
            total_chars = sum(s["char_count"] for s in summary)
            total_kb = round(total_chars / 1024, 2)
            
            metadata = {
                "total_sources": len(summary),
                "total_chunks": len(self.get_all_documents()),
                "total_kb": total_kb,
                "sources_summary": summary
            }
            metadata_path = self.index_path / "metadata.json"
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4)
            logger.info("Saved FAISS metadata successfully.")
        except Exception as e:
            logger.error(f"Error saving FAISS metadata: {e}")

    def get_cached_metadata(self) -> Dict[str, Any]:
        """
        Reads database metadata directly from the JSON file without loading FAISS or embeddings.
        If the database exists but the cache is missing, it loads the database once to rebuild it.
        """
        metadata_path = self.index_path / "metadata.json"
        if metadata_path.exists():
            try:
                import json
                with open(metadata_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cached metadata: {e}")
                
        # Rebuild if index folder exists but metadata.json does not
        if self.index_path.exists() and (self.index_path / "index.faiss").exists():
            logger.info("Metadata cache missing but FAISS index directory exists. Rebuilding metadata cache...")
            try:
                self.save_metadata()
                if metadata_path.exists():
                    import json
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception as e:
                logger.error(f"Failed to generate missing metadata cache: {e}")

        return {
            "total_sources": 0,
            "total_chunks": 0,
            "total_kb": 0.0,
            "sources_summary": []
        }


    def add_documents(self, documents: List[Document]):
        """
        Adds documents to the FAISS index. If the index does not exist yet,
        it initializes a new one.
        """
        if not documents:
            logger.warning("No documents provided to add to vector store.")
            return

        logger.info(f"Adding {len(documents)} document chunks to FAISS index...")
        try:
            from langchain_community.vectorstores import FAISS
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
            else:
                self.vector_store.add_documents(documents)
            
            # Persist changes
            self.save()
            self.save_metadata()
            logger.info("Successfully added documents to vector store.")
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise e


    def get_all_documents(self) -> List[Document]:
        """
        Returns all Document objects stored in the local vector store.
        """
        if not self.vector_store:
            return []
        try:
            # Langchain FAISS stores documents in memory docstore: self.vector_store.docstore._dict
            docstore = self.vector_store.docstore
            if hasattr(docstore, "_dict"):
                return list(docstore._dict.values())
        except Exception as e:
            logger.error(f"Error retrieving documents from FAISS store: {e}")
        return []

    def get_ingested_sources_summary(self) -> List[Dict[str, Any]]:
        """
        Aggregates documents in the store to provide a summary of ingested sources.
        """
        documents = self.get_all_documents()
        sources_map = {}
        
        for doc in documents:
            source = doc.metadata.get("source", "Unknown Source")
            file_name = doc.metadata.get("file_name") or doc.metadata.get("title") or source
            doc_type = doc.metadata.get("type", "unknown")
            
            if source not in sources_map:
                sources_map[source] = {
                    "source": source,
                    "title": file_name,
                    "type": doc_type,
                    "chunks_count": 0,
                    "char_count": 0
                }
            
            sources_map[source]["chunks_count"] += 1
            sources_map[source]["char_count"] += len(doc.page_content)
            
        return list(sources_map.values())

    def reset_database(self):
        """
        Deletes the FAISS index folder and resets state.
        """
        logger.info(f"Resetting FAISS index at {self.index_path}...")
        try:
            # Clear vector store references and force GC to release file handles
            self.vector_store = None
            self._loaded = True # mark as loaded so properties don't reload it
            import gc
            gc.collect()
            
            # Delete cached metadata
            metadata_path = self.index_path / "metadata.json"
            if metadata_path.exists():
                try:
                    metadata_path.unlink()
                except Exception:
                    pass
            
            if self.index_path.exists():
                import shutil
                import stat
                import time
                import random
 
                def remove_readonly(func, path, excinfo):
                    try:
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    except Exception:
                        pass
 
                # Windows file locking workaround: rename the directory first
                temp_path = self.index_path.parent / f"{self.index_path.name}_old_{int(time.time())}_{random.randint(1000, 9999)}"
                try:
                    os.rename(str(self.index_path), str(temp_path))
                    target_to_delete = temp_path
                    logger.info(f"Successfully renamed index folder to temporary path: {temp_path}")
                except Exception as rename_err:
                    logger.warning(f"Could not rename directory (might be locked by other processes): {rename_err}. Will attempt direct deletion.")
                    target_to_delete = self.index_path
 
                # Retry loop to handle Windows file locks (e.g. OneDrive, index loading)
                for attempt in range(5):
                    try:
                        shutil.rmtree(target_to_delete, onerror=remove_readonly)
                        break
                    except Exception as e:
                        if attempt == 4:
                            # If we renamed it, a deletion failure isn't fatal to the user,
                            # since the original index path has been successfully freed up.
                            if target_to_delete == self.index_path:
                                raise e
                            else:
                                logger.warning(f"Failed to delete renamed temp folder {target_to_delete}: {e}")
                        else:
                            logger.warning(f"Deletion attempt {attempt + 1} failed, retrying: {e}")
                            gc.collect()
                            time.sleep(0.2)
                        
            logger.info("FAISS index deleted and database reset.")
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            raise e

