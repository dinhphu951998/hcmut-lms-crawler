"""
Course Crawler module for HCMUT LMS Crawler.
Handles parsing and crawling of course pages.
"""
from typing import List, Dict, Optional
from crawler.lms_crawler import LmsCrawler
from utils.html_saver import HtmlSaver


class CourseCrawler(LmsCrawler):
    """Crawler for course pages."""
    
    def __init__(self, base_url: str, headers: dict, html_saver: HtmlSaver):
        """
        Initialize course crawler.
        
        Args:
            base_url: Base URL of the LMS
            headers: HTTP headers including authentication
            html_saver: HtmlSaver instance for file operations
        """
        super().__init__(base_url, headers)
        self.html_saver = html_saver
    
    def crawl_course(self, course_url: str) -> Optional[Dict[str, any]]:
        """
        Crawl a single course page and save it.
        
        Args:
            course_url: URL of the course page
            
        Returns:
            Dictionary with course info and teacher links, or None if failed
        """
        # Extract course ID from URL
        course_id = self.extract_id_from_url(course_url, "id")
        if not course_id:
            self.logger.warning(f"Could not extract course ID from: {course_url}")
            return None
        
        # Check if file already exists (idempotency)
        if self.html_saver.file_exists("courses", course_id):
            self.logger.info(f"Course {course_id} already exists, skipping download")
            # Still need to extract teacher links for processing
            file_path = self.html_saver.get_file_path("courses", course_id)
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        else:
            # Fetch the page
            course_url = self.build_url(f"enrol/index.php?id={course_id}")
            html_content = self.fetch_page(course_url)
            if not html_content:
                self.logger.error(f"Failed to fetch course {course_id}")
                return None
            
            # Save the HTML
            file_path = self.html_saver.save_html("courses", course_id, html_content)
            self.logger.info(f"Saved course {course_id} to {file_path}")
        
        # Extract course information
        course_info = self.extract_course_info(html_content, course_id)
        return course_info
    
    def extract_course_info(self, html_content: str, course_id: str) -> Dict[str, any]:
        """
        Extract course information from HTML.
        
        Args:
            html_content: HTML content of course page
            course_id: ID of the course
            
        Returns:
            Dictionary with course information
        """
        soup = self.parse_html(html_content)
        if not soup:
            return {"course_id": course_id, "teacher_links": []}
        
        # Extract course name
        course_name = ""
        coursename_div = soup.find("h3", class_="coursename")
        if coursename_div:
            course_name = self.normalize_text(coursename_div.get_text())
        
        # Extract teachers text
        teachers_text = ""
        teachers_ul = soup.find("ul", class_="teachers")
        if teachers_ul:
            teachers_text = self.normalize_text(teachers_ul.get_text())
        
        # Extract teacher links
        teacher_links = []
        if teachers_ul:
            teacher_anchors = teachers_ul.find_all("a")
            for anchor in teacher_anchors:
                href = anchor.get("href", "")
                if href and "/user/profile.php" in href:
                    full_url = self.build_url(href)
                    teacher_links.append(full_url)
        
        course_info = {
            "course_id": course_id,
            "course_name": course_name,
            "teachers_text": teachers_text,
            "teacher_links": teacher_links
        }
        
        self.logger.info(f"Course {course_id}: {course_name}, {len(teacher_links)} teachers")
        return course_info
    
    def extract_teacher_links_from_file(self, course_id: str) -> List[str]:
        """
        Extract teacher links from a saved course file.
        
        Args:
            course_id: ID of the course
            
        Returns:
            List of teacher URLs
        """
        if not self.html_saver.file_exists("courses", course_id):
            return []
        
        file_path = self.html_saver.get_file_path("courses", course_id)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            course_info = self.extract_course_info(html_content, course_id)
            return course_info.get("teacher_links", [])
        except Exception as e:
            self.logger.error(f"Failed to read course file {course_id}: {e}")
            return []

