"""
Main orchestration script for HCMUT LMS Crawler.
Coordinates all crawling operations with multi-threading support.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Set
from config import Config
from html_saver import HtmlSaver
from semester_crawler import SemesterCrawler
from course_crawler import CourseCrawler
from user_crawler import UserCrawler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("MainCrawler")


class MainCrawler:
    """Main crawler orchestrator."""
    
    def __init__(self, config: Config):
        """
        Initialize main crawler with configuration.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.html_saver = HtmlSaver(config.output_dir)
        
        # Initialize crawlers
        headers = config.get_headers()
        self.semester_crawler = SemesterCrawler(config.base_url, headers, self.html_saver)
        self.course_crawler = CourseCrawler(config.base_url, headers, self.html_saver)
        self.user_crawler = UserCrawler(config.base_url, headers, self.html_saver)
        
        # Track processed items
        self.processed_courses: Set[str] = set()
        self.processed_users: Set[str] = set()
    
    def run(self):
        """Execute the full crawling workflow."""
        logger.info("=" * 60)
        logger.info("Starting HCMUT LMS Crawler")
        logger.info("=" * 60)
        
        # Step 1: Discover and crawl semesters
        logger.info("Step 1: Discovering semesters...")
        semesters = self.semester_crawler.discover_semesters()
        
        if not semesters:
            logger.error("No semesters found. Exiting.")
            return
        
        logger.info(f"Found {len(semesters)} semesters")
        
        # Step 2: Crawl semester pages
        logger.info("Step 2: Crawling semester pages...")
        all_course_urls = []
        
        with ThreadPoolExecutor(max_workers=self.config.number_of_workers) as executor:
            futures = {
                executor.submit(self.crawl_semester_and_extract, sem): sem
                for sem in semesters
            }
            
            for future in as_completed(futures):
                semester = futures[future]
                try:
                    course_urls = future.result()
                    if course_urls:
                        all_course_urls.extend(course_urls)
                except Exception as e:
                    logger.error(f"Error processing semester {semester.get('category_id')}: {e}")
        
        logger.info(f"Discovered {len(all_course_urls)} course URLs from semesters")
        
        # Step 3: Crawl courses and discover users
        logger.info("Step 3: Crawling courses and discovering users...")
        all_user_urls = []
        
        with ThreadPoolExecutor(max_workers=self.config.number_of_workers) as executor:
            futures = {
                executor.submit(self.crawl_course_and_extract, url): url
                for url in all_course_urls
            }
            
            for future in as_completed(futures):
                course_url = futures[future]
                try:
                    user_urls = future.result()
                    if user_urls:
                        all_user_urls.extend(user_urls)
                except Exception as e:
                    logger.error(f"Error processing course {course_url}: {e}")
        
        logger.info(f"Discovered {len(all_user_urls)} user URLs from courses")
        
        # Step 4: Crawl users and discover additional courses
        logger.info("Step 4: Crawling users and discovering additional courses...")
        additional_course_urls = []
        
        with ThreadPoolExecutor(max_workers=self.config.number_of_workers) as executor:
            futures = {
                executor.submit(self.crawl_user_and_extract, url): url
                for url in all_user_urls
            }
            
            for future in as_completed(futures):
                user_url = futures[future]
                try:
                    course_urls = future.result()
                    if course_urls:
                        additional_course_urls.extend(course_urls)
                except Exception as e:
                    logger.error(f"Error processing user {user_url}: {e}")
        
        logger.info(f"Discovered {len(additional_course_urls)} additional course URLs from users")
        
        # Step 5: Crawl additional courses discovered from users
        if additional_course_urls:
            logger.info("Step 5: Crawling additional courses from user profiles...")
            
            with ThreadPoolExecutor(max_workers=self.config.number_of_workers) as executor:
                futures = {
                    executor.submit(self.crawl_course_and_extract, url): url
                    for url in additional_course_urls
                }
                
                for future in as_completed(futures):
                    course_url = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Error processing additional course {course_url}: {e}")
        
        logger.info("=" * 60)
        logger.info("Crawling completed!")
        logger.info(f"Total courses processed: {len(self.processed_courses)}")
        logger.info(f"Total users processed: {len(self.processed_users)}")
        logger.info("=" * 60)
    
    def crawl_semester_and_extract(self, semester_info: dict) -> list:
        """
        Crawl a semester and extract course URLs.
        
        Args:
            semester_info: Semester information dictionary
            
        Returns:
            List of course URLs
        """
        file_path = self.semester_crawler.crawl_semester(semester_info)
        if not file_path:
            return []
        
        # Read the saved file and extract course links
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        return self.semester_crawler.extract_course_links(html_content)
    
    def crawl_course_and_extract(self, course_url: str) -> list:
        """
        Crawl a course and extract user URLs.
        
        Args:
            course_url: Course URL
            
        Returns:
            List of user URLs
        """
        # Extract course ID to check if already processed
        course_id = self.course_crawler.extract_id_from_url(course_url, "id")
        if course_id in self.processed_courses:
            return []
        
        course_info = self.course_crawler.crawl_course(course_url)
        if not course_info:
            return []
        
        self.processed_courses.add(course_id)
        return course_info.get("teacher_links", [])
    
    def crawl_user_and_extract(self, user_url: str) -> list:
        """
        Crawl a user and extract course URLs.
        
        Args:
            user_url: User URL
            
        Returns:
            List of course URLs (only new courses not yet processed)
        """
        # Extract user ID to check if already processed
        user_id = self.user_crawler.extract_id_from_url(user_url, "id")
        if user_id in self.processed_users:
            return []
        
        user_info = self.user_crawler.crawl_user(user_url)
        if not user_info:
            return []
        
        self.processed_users.add(user_id)
        
        # Filter out courses that have already been processed
        course_links = user_info.get("course_links", [])
        new_course_urls = []
        
        for course_url in course_links:
            course_id = self.course_crawler.extract_id_from_url(course_url, "id")
            if course_id and course_id not in self.processed_courses:
                new_course_urls.append(course_url)
        
        return new_course_urls


def main():
    """Main entry point."""
    try:
        # Load configuration
        config = Config()
        
        # Create and run crawler
        crawler = MainCrawler(config)
        crawler.run()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file")
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    main()

