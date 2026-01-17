"""
Base crawler class for HCMUT LMS Crawler.
Provides shared logic for HTTP requests, error handling, and text normalization.
"""
import re
import requests
import logging
from typing import Optional
from bs4 import BeautifulSoup


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class LmsCrawler:
    """Base class for LMS crawling operations."""
    
    def __init__(self, base_url: str, headers: dict):
        """
        Initialize the base crawler.
        
        Args:
            base_url: Base URL of the LMS
            headers: HTTP headers including authentication
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.headers.update(headers)
    
    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Fetch a page with retry logic.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            
        Returns:
            HTML content as string, or None if failed
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Fetching: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
        return None
    
    def parse_html(self, html_content: str) -> Optional[BeautifulSoup]:
        """
        Parse HTML content into BeautifulSoup object.
        
        Args:
            html_content: Raw HTML string
            
        Returns:
            BeautifulSoup object, or None if parsing failed
        """
        try:
            return BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            self.logger.error(f"Failed to parse HTML: {e}")
            return None
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text by trimming and removing excessive whitespace.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        # Remove excessive whitespace and trim
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def extract_id_from_url(url: str, param_name: str = "id") -> Optional[str]:
        """
        Extract ID parameter from URL.
        
        Args:
            url: URL to extract from
            param_name: Name of the parameter to extract
            
        Returns:
            Extracted ID or None
        """
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return params.get(param_name, [None])[0]
        except Exception:
            return None
    
    def build_url(self, path: str) -> str:
        """
        Build a full URL from a path.
        
        Args:
            path: Path or full URL
            
        Returns:
            Full URL
        """
        if path.startswith("http"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

