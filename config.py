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
            "Cookie": self.cookie
        }

