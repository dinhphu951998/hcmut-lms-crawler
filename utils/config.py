"""
Configuration module for HCMUT LMS Crawler.
Handles environment variable loading and validation.
"""
import os
from dotenv import load_dotenv


class Config:
    """Configuration class that loads and validates environment variables."""
    
    def __init__(self, env_file: str = ".env"):
        """
        Initialize configuration from environment file.
        
        Args:
            env_file: Path to the .env file (default: ".env")
        """
        load_dotenv(env_file)
        
        # Load required variables
        self.base_url = os.getenv("BASE_URL", "https://lms.hcmut.edu.vn")
        self.cookie = os.getenv("COOKIE", "")
        
        # Load optional variables with defaults
        self.number_of_workers = int(os.getenv("NUMBER_OF_WORKERS", "1"))
        self.output_dir = os.getenv("OUTPUT_DIR", "./")
        
        # Validate configuration
        self._validate()
    
    def _validate(self):
        """Validate that required configuration is present."""
        if not self.cookie:
            raise ValueError("COOKIE environment variable is required")
        
        if self.number_of_workers < 1:
            raise ValueError("NUMBER_OF_WORKERS must be at least 1")
    
    def get_headers(self) -> dict:
        """
        Get HTTP headers with authentication cookie.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "host": "lms.hcmut.edu.vn",
            "referer": "https://lms.hcmut.edu.vn/",
            "cookie": self.cookie,
            "upgrade-insecure-requests": "1",
        }

