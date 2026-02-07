"""
Semester Crawler module for HCMUT LMS Crawler.
Handles parsing and crawling of semester pages.
"""
import re
from typing import List, Dict, Optional
from crawler.lms_crawler import LmsCrawler
from utils.html_saver import HtmlSaver


class SemesterCrawler(LmsCrawler):
    """Crawler for semester pages."""
    
    def __init__(self, base_url: str, headers: dict, html_saver: HtmlSaver):
        """
        Initialize semester crawler.
        
        Args:
            base_url: Base URL of the LMS
            headers: HTTP headers including authentication
            html_saver: HtmlSaver instance for file operations
        """
        super().__init__(base_url, headers)
        self.html_saver = html_saver
    
    def discover_semesters(self) -> List[Dict[str, str]]:
        """
        Discover all semesters from the course list page.
        
        Returns:
            List of semester dictionaries with url, category_id, and metadata
        """
        html_content = None
        if self.html_saver.file_exists("semesters", "discover_semester_result"):
            self.logger.info("Using cached discover_semester_result.html")
            file_path = self.html_saver.get_file_path("semesters", "discover_semester_result")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
            except Exception as e:
                self.logger.error(f"Failed to read discover_semester_result.html: {e}")
        
        if not html_content:
            course_list_url = self.build_url("/course/")
            html_content = self.fetch_page(course_list_url)
        
        soup = self.parse_html(html_content)
        if not soup:
            return []
        
        # Find the select.urlselect element
        select_elem = soup.find("select", class_="urlselect")
        if not select_elem:
            self.logger.error("Could not find select.urlselect element")
            return []
        
        semesters = []
        options = select_elem.find_all("option")
        
        for option in options:
            option_text = self.normalize_text(option.get_text())
            option_value = option.get("value", "")
            
            if not option_value or not option_text:
                continue
            
            # Validate format: "Semester / Faculty / Major"
            # Looking for text with at least 2 forward slashes
            if option_text.count(" / ") < 2:
                continue
            
            parts = [self.normalize_text(p) for p in option_text.split("/")]
            if len(parts) < 3:
                continue
            
            # Extract category ID from URL
            category_id = self.extract_id_from_url(option_value, "categoryid")
            if not category_id:
                self.logger.warning(f"Could not extract category ID from: {option_value}")
                continue
            
            semester_info = {
                "category_id": category_id,
                "url": option_value,
                "semester": parts[0],
                "faculty": parts[1],
                "major": parts[2],
                "full_text": option_text
            }

            semesters.append(semester_info)
            self.logger.info(f"Discovered semester: {option_text} (ID: {category_id})")
        
        self.logger.info(f"Discovered {len(semesters)} semesters")
        return semesters
    
    def crawl_semester(self, semester_info: Dict[str, str]) -> Optional[str]:
        """
        Crawl a single semester page and save it.
        
        Args:
            semester_info: Dictionary containing semester information
            
        Returns:
            Path to saved file, or None if failed
        """
        category_id = semester_info["category_id"]
        
        # Check if file already exists (idempotency)
        if self.html_saver.file_exists("semesters", category_id):
            self.logger.info(f"Semester {category_id} already exists, skipping")
            return self.html_saver.get_file_path("semesters", category_id)
        
        # Build URL with perpage=all to bypass pagination
        url = semester_info["url"]
        if "?" in url:
            url = f"{url}&perpage=all"
        else:
            url = f"{url}?perpage=all"
        
        # Ensure full URL
        url = self.build_url(url)
        
        # Fetch the page
        html_content = self.fetch_page(url)
        if not html_content:
            self.logger.error(f"Failed to fetch semester {category_id}")
            return None
        
        # Save the HTML
        file_path = self.html_saver.save_html("semesters", category_id, html_content)
        self.logger.info(f"Saved semester {category_id} to {file_path}")
        
        return file_path
    
    def extract_course_links(self, semester_html: str) -> List[str]:
        """
        Extract course links from semester HTML.
        
        Args:
            semester_html: HTML content of semester page
            
        Returns:
            List of course URLs
        """
        soup = self.parse_html(semester_html)
        if not soup:
            return []
        
        course_links = []
        # Find all links with class "aalink"
        aalinks = soup.find_all("a", class_="aalink")
        
        for link in aalinks:
            href = link.get("href", "")
            if href and "/course/view.php" in href:
                full_url = self.build_url(href)
                course_links.append(full_url)
        
        self.logger.info(f"Extracted {len(course_links)} course links")
        return course_links

