"""
HTML Saver module for HCMUT LMS Crawler.
Handles file system operations.
"""
import os
from pathlib import Path
from typing import Optional


class HtmlSaver:
    """Handles file system operations for saving HTML files."""
    
    def __init__(self, output_dir: str = "./"):
        """
        Initialize HTML saver with output directory.
        
        Args:
            output_dir: Base directory for output files
        """
        self.output_dir = Path(output_dir)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary output directories if they don't exist."""
        directories = ["semesters", "courses", "users"]
        for dir_name in directories:
            dir_path = self.output_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def file_exists(self, category: str, file_id: str) -> bool:
        """
        Check if a file already exists.
        
        Args:
            category: Category of the file (semesters, courses, or users)
            file_id: ID of the file
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self.output_dir / category / f"{file_id}.html"
        return file_path.exists()
    
    def save_html(self, category: str, file_id: str, content: str) -> str:
        """
        Save HTML content to a file.
        
        Args:
            category: Category of the file (semesters, courses, or users)
            file_id: ID of the file
            content: HTML content to save
            
        Returns:
            Path to the saved file
        """
        file_path = self.output_dir / category / f"{file_id}.html"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(file_path)
    
    def get_file_path(self, category: str, file_id: str) -> str:
        """
        Get the full path for a file.
        
        Args:
            category: Category of the file (semesters, courses, or users)
            file_id: ID of the file
            
        Returns:
            Full path to the file
        """
        file_path = self.output_dir / category / f"{file_id}.html"
        return str(file_path)

