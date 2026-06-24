import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse
import requests
from langchain_core.documents import Document
from src.ingestion.parser import DocParser
from src.utils.config import DATA_DIR
from src.utils.logger import logger

class GitHubDownloader:
    """
    Downloads or clones a GitHub repository, filters for documentation files,
    and extracts text documents with metadata.
    """
    def __init__(self, repo_url: str):
        self.repo_url = repo_url.strip().rstrip("/")
        self.owner, self.repo_name = self.parse_repo_url(self.repo_url)
        self.temp_dir = DATA_DIR / "temp_repos" / f"{self.owner}_{self.repo_name}"

    @staticmethod
    def parse_repo_url(url: str) -> tuple[str, str]:
        """
        Parses owner and repo name from GitHub URL.
        """
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        
        if len(path_parts) >= 2:
            owner = path_parts[0]
            # Remove .git suffix if present
            repo_name = path_parts[1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            return owner, repo_name
        raise ValueError(f"Invalid GitHub URL: {url}")

    def clone_repo(self) -> bool:
        """
        Tries to perform a shallow clone using the Git CLI.
        """
        try:
            logger.info(f"Attempting to clone repository {self.repo_url} via Git CLI...")
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            
            # Execute git clone
            result = subprocess.run(
                ["git", "clone", "--depth", "1", self.repo_url, str(self.temp_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("Successfully cloned repository using Git CLI.")
            return True
        except Exception as e:
            logger.warning(f"Git clone failed or Git not available. Error: {e}. Falling back to ZIP download.")
            return False

    def download_zip(self) -> bool:
        """
        Downloads the repository as a ZIP archive and extracts it.
        Tries 'main' branch first, then 'master' branch.
        """
        branches = ["main", "master"]
        success = False
        
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self.temp_dir.parent / f"{self.owner}_{self.repo_name}.zip"
        
        for branch in branches:
            zip_url = f"https://github.com/{self.owner}/{self.repo_name}/archive/refs/heads/{branch}.zip"
            logger.info(f"Trying ZIP download from: {zip_url}")
            try:
                response = requests.get(zip_url, stream=True, timeout=20)
                if response.status_code == 200:
                    with open(zip_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    logger.info("Download complete. Extracting ZIP...")
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.extractall(self.temp_dir.parent)
                    
                    # Clean up zip file
                    if zip_path.exists():
                        os.remove(zip_path)
                        
                    # GitHub extracts into a folder like {repo_name}-{branch}
                    extracted_dir = self.temp_dir.parent / f"{self.repo_name}-{branch}"
                    if extracted_dir.exists():
                        shutil.move(str(extracted_dir), str(self.temp_dir))
                        
                    logger.info("Successfully extracted repository ZIP archive.")
                    success = True
                    break
                else:
                    logger.warning(f"Failed to download zip from {zip_url} (Status: {response.status_code})")
            except Exception as ex:
                logger.error(f"Error downloading ZIP for branch {branch}: {ex}")
                
        return success

    def load_documents(self) -> List[Document]:
        """
        Downloads/Clones the repo, scans for READMEs, markdown files, and docs folders,
        and parses them into LangChain Document objects.
        """
        documents: List[Document] = []
        
        # Try cloning first, fall back to downloading ZIP
        loaded = self.clone_repo()
        if not loaded:
            loaded = self.download_zip()
            
        if not loaded:
            logger.error(f"Failed to retrieve repository {self.repo_url} via Git or ZIP.")
            return []
            
        try:
            logger.info(f"Scanning repository {self.owner}/{self.repo_name} for documentation files...")
            
            # Supported file suffixes
            doc_suffixes = {".md", ".txt", ".rst"}
            # Directories that are likely to contain documentation
            doc_dirs = {"docs", "doc", "wiki", "documentation"}
            
            for root, dirs, files in os.walk(self.temp_dir):
                # Calculate relative path
                rel_root = Path(root).relative_to(self.temp_dir)
                
                # Check if we are inside a documentation directory or in the root
                is_root = str(rel_root) == "."
                is_doc_dir = any(part.lower() in doc_dirs for part in rel_root.parts)
                
                # We want: 
                # 1. Any files in a documentation directory (e.g. docs/*.md)
                # 2. README and main-level md files in the root folder
                for file in files:
                    file_path = Path(root) / file
                    suffix = file_path.suffix.lower()
                    
                    if suffix not in doc_suffixes:
                        continue
                        
                    file_name = file_path.name.lower()
                    should_parse = False
                    
                    if is_doc_dir:
                        should_parse = True
                    elif is_root and ("readme" in file_name or suffix == ".md"):
                        should_parse = True
                        
                    if should_parse:
                        parsed_docs = DocParser.parse(file_path)
                        for doc in parsed_docs:
                            # Rewrite metadata for git source representation
                            rel_file_path = file_path.relative_to(self.temp_dir)
                            source_url = f"{self.repo_url}/blob/main/{rel_file_path.as_posix()}"
                            
                            doc.metadata.update({
                                "source": source_url,
                                "file_name": file_path.name,
                                "type": "github",
                                "repo": f"{self.owner}/{self.repo_name}",
                                "relative_path": str(rel_file_path)
                            })
                            documents.append(doc)
                            
            logger.info(f"GitHub loader finished. Parsed {len(documents)} docs from repo.")
        except Exception as e:
            logger.error(f"Error walking and parsing repository files: {e}")
        finally:
            # Clean up cloned files to free space
            self.cleanup()
            
        return documents

    def cleanup(self):
        """
        Removes temporary repository files.
        """
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp repository folder: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Could not clean up temp repo folder: {e}")
