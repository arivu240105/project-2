import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.vectorstore.store import VectorStoreManager
from src.retrieval.retriever import HybridRetriever
from src.retrieval.reranker import CrossEncoderReranker

print("1. Creating VectorStoreManager...")
start = time.time()
store = VectorStoreManager()
print(f"Done. Vector store instance ready. (took {time.time() - start:.4f}s)")

print("2. Creating HybridRetriever...")
start = time.time()
retriever = HybridRetriever(store)
print(f"Done. Retriever ready. (took {time.time() - start:.4f}s)")

print("3. Performing retrieval...")
start = time.time()
# This should trigger lazy-loading of HuggingFaceEmbeddings BGE model weights!
results = retriever.retrieve("machine learning decision tree", retrieve_k=5)
print(f"Done. Retrieved {len(results)} chunks. (took {time.time() - start:.2f}s)")

for idx, doc in enumerate(results):
    print(f"Match {idx+1}: {doc.metadata.get('source')} | Index: {doc.metadata.get('chunk_index')}")
    print(f"Snippet: {doc.page_content[:100]}...\n")

print("4. Creating Reranker...")
start = time.time()
reranker = CrossEncoderReranker()
print(f"Done. Reranker ready. (took {time.time() - start:.4f}s)")

print("5. Performing Reranking...")
start = time.time()
# This should trigger lazy-loading of sentence-transformers Cross-Encoder weights!
reranked = reranker.rerank("machine learning decision tree", results, rerank_k=3)
print(f"Done. Reranked {len(reranked)} chunks. (took {time.time() - start:.2f}s)")
