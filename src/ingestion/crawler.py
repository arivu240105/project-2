import re
import time
from urllib.parse import urljoin, urlparse
from typing import List, Set, Dict, Any
import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from src.utils.logger import logger

class WebCrawler:
    """
    Crawls website URLs recursively up to a configurable depth and page limit.
    Extracts text and structures documents with metadata.
    """
    def __init__(self, max_depth: int = 1, max_pages: int = 20, timeout: int = 10):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout = timeout
        self.visited_urls: Set[str] = set()
        self.session = requests.Session()
        # Add basic User-Agent to avoid simple blocking
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """
        Ensures the URL is valid, belongs to the same domain, and is not a resource file.
        """
        try:
            parsed = urlparse(url)
            # Stay within the same domain
            parsed_base = urlparse(base_domain)
            if parsed.netloc != parsed_base.netloc:
                return False
                
            # Exclude files (images, PDFs, archives, etc.)
            path = parsed.path.lower()
            excluded_extensions = [
                ".pdf", ".zip", ".tar.gz", ".tgz", ".png", ".jpg", ".jpeg", 
                ".gif", ".svg", ".css", ".js", ".xml", ".json", ".csv"
            ]
            if any(path.endswith(ext) for ext in excluded_extensions):
                return False
                
            # Exclude query parameters/fragments that are just links/anchors if needed
            # (though we can keep query params if they represent separate pages, e.g. ?id=...)
            return True
        except Exception:
            return False

    def clean_url(self, url: str) -> str:
        """
        Removes URL fragments (#heading) so we don't fetch the same page multiple times.
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parses page HTML with BeautifulSoup and extracts clean text contents and metadata.
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove unwanted script, style, nav, footer, header elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            element.decompose()
            
        # Get title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.h1:
            title = soup.h1.get_text().strip()
        else:
            title = url
            
        # Prioritize main content blocks if they exist
        content_selectors = ["main", "article", "[role='main']", "#content", ".content", ".body"]
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
                
        if not main_content:
            main_content = soup.body if soup.body else soup
            
        # Extract clean text
        # Replace consecutive newlines and clean up whitespaces
        text = main_content.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        # Remove empty lines
        clean_text = "\n".join([line for line in lines if line])
        
        # Find all valid internal links
        links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(url, href)
            links.add(full_url)
            
        return {
            "title": title,
            "text": clean_text,
            "links": links
        }

    def crawl(self, start_url: str) -> List[Document]:
        """
        Performs bread-first-search (BFS) crawling up to max_depth and max_pages.
        """
        start_url = self.clean_url(start_url)
        base_domain = start_url
        queue = [(start_url, 0)] # (url, current_depth)
        documents: List[Document] = []
        
        logger.info(f"Starting web crawl of {start_url} (depth={self.max_depth}, max_pages={self.max_pages})")
        
        while queue and len(self.visited_urls) < self.max_pages:
            current_url, depth = queue.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.visited_urls.add(current_url)
            logger.info(f"Crawling ({len(self.visited_urls)}/{self.max_pages}): {current_url} at depth {depth}")
            
            try:
                # Add delay to respect website rate limits
                time.sleep(0.5)
                response = self.session.get(current_url, timeout=self.timeout)
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {current_url} (Status: {response.status_code})")
                    continue
                    
                # Verify if it's HTML content
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    logger.warning(f"Skipping non-HTML page {current_url} (Type: {content_type})")
                    continue
                
                parsed_data = self.extract_content(response.text, current_url)
                
                # Add to documents if we got text content
                if parsed_data["text"]:
                    metadata = {
                        "source": current_url,
                        "title": parsed_data["title"],
                        "type": "web",
                        "depth": depth,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                    }
                    documents.append(Document(page_content=parsed_data["text"], metadata=metadata))
                
                # If we haven't reached max depth, add new links to the queue
                if depth < self.max_depth:
                    for link in parsed_data["links"]:
                        cleaned_link = self.clean_url(link)
                        if (cleaned_link not in self.visited_urls and 
                                self.is_valid_url(cleaned_link, base_domain) and 
                                cleaned_link not in [q[0] for q in queue]):
                            queue.append((cleaned_link, depth + 1))
                            
            except Exception as e:
                logger.error(f"Error crawling {current_url}: {e}")
                
        logger.info(f"Web crawl finished. Crawled {len(self.visited_urls)} pages, generated {len(documents)} documents.")
        return documents
