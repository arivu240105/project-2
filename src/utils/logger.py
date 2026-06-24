import logging
import sys
from src.utils.config import LOGS_DIR

# Log file path
LOG_FILE_PATH = LOGS_DIR / "devdocs_rag.log"

def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a logger with dual handlers:
    1. StreamHandler (Console)
    2. FileHandler (logs/devdocs_rag.log)
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup multiple times
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Format for logs
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # File Handler
    try:
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to initialize file logger handler: {e}", file=sys.stderr)
        
    return logger

# Export standard workspace logger
logger = setup_logger("devdocs_rag")
