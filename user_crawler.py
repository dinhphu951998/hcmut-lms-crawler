"""
User Crawler module for HCMUT LMS Crawler.
Handles parsing and crawling of user profile pages.
"""
from typing import List, Dict, Optional
from lms_crawler import LmsCrawler
from html_saver import HtmlSaver


class UserCrawler(LmsCrawler):
    """Crawler for user profile pages."""
    
    def __init__(self, base_url: str, headers: dict, html_saver: HtmlSaver):
        """
        Initialize user crawler.
        
        Args:
            base_url: Base URL of the LMS
            headers: HTTP headers including authentication
            html_saver: HtmlSaver instance for file operations
        """
        super().__init__(base_url, headers)
        self.html_saver = html_saver
    
    def crawl_user(self, user_url: str) -> Optional[Dict[str, any]]:
        """
        Crawl a single user profile page and save it.
        
        Args:
            user_url: URL of the user profile page
            
        Returns:
            Dictionary with user info and course links, or None if failed
        """
        # Extract user ID from URL
        user_id = self.extract_id_from_url(user_url, "id")
        if not user_id:
            self.logger.warning(f"Could not extract user ID from: {user_url}")
            return None
        
        # Ensure showallcourses=1 parameter is included
        if "showallcourses" not in user_url:
            separator = "&" if "?" in user_url else "?"
            user_url = f"{user_url}{separator}showallcourses=1"
        
        # Check if file already exists (idempotency)
        if self.html_saver.file_exists("users", user_id):
            self.logger.info(f"User {user_id} already exists, skipping download")
            # Still need to extract course links for processing
            file_path = self.html_saver.get_file_path("users", user_id)
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        else:
            # Fetch the page
            html_content = self.fetch_page(user_url)
            if not html_content:
                self.logger.error(f"Failed to fetch user {user_id}")
                return None
            
            # Save the HTML
            file_path = self.html_saver.save_html("users", user_id, html_content)
            self.logger.info(f"Saved user {user_id} to {file_path}")
        
        # Extract user information
        user_info = self.extract_user_info(html_content, user_id)
        return user_info
    
    def extract_user_info(self, html_content: str, user_id: str) -> Dict[str, any]:
        """
        Extract user information from HTML.
        
        Args:
            html_content: HTML content of user profile page
            user_id: ID of the user
            
        Returns:
            Dictionary with user information
        """
        soup = self.parse_html(html_content)
        if not soup:
            return {"user_id": user_id, "course_links": []}
        
        # Extract teacher name from page-header-headings
        teacher_name = ""
        header = soup.find(class_="page-header-headings")
        if header:
            teacher_name = self.normalize_text(header.get_text())
        
        # Extract role from .userprofile .description
        role = ""
        userprofile = soup.find(class_="userprofile")
        if userprofile:
            description = userprofile.find(class_="description")
            if description:
                role = self.normalize_text(description.get_text())
        
        # Extract profile details from div.profile_tree (Section 0 - dt/dd pairs)
        profile_details = {}
        profile_tree = soup.find("div", class_="profile_tree")
        if profile_tree:
            sections = profile_tree.find_all("section", recursive=False)
            if sections:
                # Section 0 contains profile details (dt/dd pairs)
                first_section = sections[0]
                dts = first_section.find_all("dt")
                dds = first_section.find_all("dd")
                
                for dt, dd in zip(dts, dds):
                    key = self.normalize_text(dt.get_text())
                    value = self.normalize_text(dd.get_text())
                    if key:
                        profile_details[key] = value
        
        # Extract course links from div.profile_tree (Section 1 - a tags)
        course_links = []
        if profile_tree:
            sections = profile_tree.find_all("section", recursive=False)
            if len(sections) > 1:
                # Section 1 contains course profiles
                course_section = sections[1]
                course_anchors = course_section.find_all("a")
                
                for anchor in course_anchors:
                    href = anchor.get("href", "")
                    teaching_course_id = self.extract_id_from_url(href, "course")
                    full_url = self.build_url(f"enrol/index.php?id={teaching_course_id}")
                    course_links.append(full_url)
                        
        
        user_info = {
            "user_id": user_id,
            "teacher_name": teacher_name,
            "role": role,
            "profile_details": profile_details,
            "course_links": course_links
        }
        
        self.logger.info(f"User {user_id}: {teacher_name}, {len(course_links)} courses")
        return user_info
    
    def extract_course_links_from_file(self, user_id: str) -> List[str]:
        """
        Extract course links from a saved user file.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of course URLs
        """
        if not self.html_saver.file_exists("users", user_id):
            return []
        
        file_path = self.html_saver.get_file_path("users", user_id)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            user_info = self.extract_user_info(html_content, user_id)
            return user_info.get("course_links", [])
        except Exception as e:
            self.logger.error(f"Failed to read user file {user_id}: {e}")
            return []

