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
        


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
