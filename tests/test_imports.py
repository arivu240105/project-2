import sys
from pathlib import Path

# Add project root to path so we can run from anywhere
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

def test_imports():
    print("Testing module imports...")
       try:
        from src.utils.config import DATA_DIR, VECTOR_DB_DIR
        print("[OK] src.utils.config imported successfully.")
        
        from src.utils.logger import logger
        print("[OK] src.utils.logger imported successfully.")
        
        from src.ingestion.parser import DocParser
        print("[OK] src.ingestion.parser imported s
    
    try:
        from src.utils.config import DATA_DIR, VECTOR_DB_DIR
        print("[OK] src.utils.config imported successfully.")
        
        from src.utils.logger import logger
        print("[OK] src.utils.logger imported successfully.")
        
        from src.ingestion.parser import DocParser
        print("[OK] src.ingestion.parser imported successfully.")
        
        from src.ingestion.crawler import WebCrawler
        print("[OK] src.ingestion.crawler imported successfully.")
        
        from src.ingestion.github_loader import GitHubDownloader
        print("[OK] src.ingestion.github_loader imported successfully.")
        
        from src.ingestion.splitter import DocSplitter
        print("[OK] src.ingestion.splitter imported successfully.")
        
        from src.vectorstore.store import VectorStoreManager
        print("[OK] src.vectorstore.store imported successfully.")
        
        from src.retrieval.retriever import HybridRetriever
        print("[OK] src.retrieval.retriever imported successfully.")
        
        from src.retrieval.reranker import CrossEncoderReranker
        print("[OK] src.retrieval.reranker imported successfully.")
        
        from src.retrieval.compressor import ContextCompressor
        print("[OK] src.retrieval.compressor imported successfully.")
        
        from src.llm.groq_client import GroqClient
        print("[OK] src.llm.groq_client imported successfully.")
        
        from src.utils.evaluator import RAGEvaluator
        print("[OK] src.utils.evaluator imported successfully.")
        
        print("\nAll local code modules imported successfully without errors!")
        return True
    except Exception as e:
        print(f"\n[FAIL] Import test failed: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
