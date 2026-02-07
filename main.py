"""
Main orchestration script for HCMUT LMS Crawler.
Coordinates all crawling operations with multi-threading support.
"""
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Set, List, Callable, Any, Optional
from utils.config import Config
from utils.html_saver import HtmlSaver
from crawler.semester_crawler import SemesterCrawler
from crawler.course_crawler import CourseCrawler
from crawler.user_crawler import UserCrawler


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

        self.all_courses: List[object] = []
        self.all_users: List[object] = []
        self.users_courses: List[object] = []
    
    def execute_parallel_flatten(
        self, 
        func: Callable, 
        items: List[Any], 
        error_message_template: str = "Error processing {item}: {error}"
    ) -> List[Any]:
        """
        Execute a function in parallel and flatten the results (for functions returning lists).
        
        Args:
            func: Function to execute for each item (should return a list)
            items: List of items to process
            error_message_template: Error message template with {item} and {error} placeholders
            
        Returns:
            Flattened list of results from all function calls
        """
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.config.number_of_workers) as executor:
            futures = {
                executor.submit(func, item): item
                for item in items
            }
            
            for future in as_completed(futures):
                item = futures[future]
                try:
                    result = future.result()
                    if result:
                        all_results.extend(result)
                except Exception as e:
                    logger.error(error_message_template.format(item=item, error=e))
        
        return all_results
    
    def execute_parallel_flatten_batched(
        self, 
        func: Callable, 
        items: List[Any], 
        error_message_template: str = "Error processing {item}: {error}",
        batch_size: Optional[int] = None
    ) -> List[Any]:
        """
        Execute a function in parallel in batches and flatten the results.
        Saves data after each batch to prevent data loss.
        
        Args:
            func: Function to execute for each item (should return a list)
            items: List of items to process
            error_message_template: Error message template with {item} and {error} placeholders
            batch_size: Size of each batch (defaults to config.batch_size)
            
        Returns:
            Flattened list of results from all function calls
        """
        if batch_size is None:
            batch_size = self.config.batch_size
        
        all_results = []
        total_items = len(items)
        
        logger.info(f"Processing {total_items} items in batches of {batch_size}")
        
        for batch_num, i in enumerate(range(0, total_items, batch_size), start=1):
            batch = items[i:i + batch_size]
            batch_end = min(i + batch_size, total_items)
            
            logger.info(f"Processing batch {batch_num}: items {i+1} to {batch_end} of {total_items}")
            
            batch_results = []
            with ThreadPoolExecutor(max_workers=self.config.number_of_workers) as executor:
                futures = {
                    executor.submit(func, item): item
                    for item in batch
                }
                
                for future in as_completed(futures):
                    item = futures[future]
                    try:
                        result = future.result()
                        if result:
                            batch_results.extend(result)
                    except Exception as e:
                        logger.error(error_message_template.format(item=item, error=e))
            
            all_results.extend(batch_results)
            
            logger.info(f"Batch {batch_num} completed: {len(batch_results)} results")
            
            # Save data after each batch
            logger.info(f"Saving data after batch {batch_num}...")
            self.save_all_data()
            
            # Clear the current batch data to free memory
            self.all_courses.clear()
            self.all_users.clear()
            self.users_courses.clear()
        
        logger.info(f"All batches completed: {total_items} items processed, {len(all_results)} total results")
        
        return all_results
    
    def run(self):
        """Execute the full crawling workflow."""
        logger.info("=" * 60)
        logger.info("Starting HCMUT LMS Crawler")
        logger.info("=" * 60)
        
        # Check if brute force mode is enabled
        if self.config.max_user_id > 0:
            logger.info("Brute force mode enabled")
            self.run_brute_force_users()
            return
        
        # Step 1: Discover and crawl semesters
        logger.info("Step 1: Discovering semesters...")
        semesters = self.semester_crawler.discover_semesters()
        
        if not semesters:
            logger.error("No semesters found. Exiting.")
            return
        
        logger.info(f"Found {len(semesters)} semesters")
        
        # Step 2: Crawl semester pages
        logger.info("Step 2: Crawling semester pages...")
        all_course_urls = self.execute_parallel_flatten(
            self.crawl_semester_and_extract,
            semesters,
            "Error processing semester {item}: {error}"
        )
        logger.info(f"Discovered {len(all_course_urls)} course URLs from semesters")
        
        # Step 3: Crawl courses and discover users
        logger.info("Step 3: Crawling courses and discovering users...")
        all_user_urls = self.execute_parallel_flatten(
            self.crawl_course_and_extract,
            all_course_urls,
            "Error processing course {item}: {error}"
        )
        logger.info(f"Discovered {len(all_user_urls)} user URLs from courses")
        
        # Step 4: Crawl users and discover additional courses
        logger.info("Step 4: Crawling users and discovering additional courses...")
        additional_course_urls = self.execute_parallel_flatten(
            self.crawl_user_and_extract,
            all_user_urls,
            "Error processing user {item}: {error}"
        )
        logger.info(f"Discovered {len(additional_course_urls)} additional course URLs from users")
        
        # Step 5: Crawl additional courses discovered from users
        if additional_course_urls:
            logger.info("Step 5: Crawling additional courses from user profiles...")
            self.execute_parallel_flatten(
                self.crawl_course_and_extract,
                additional_course_urls,
                "Error processing additional course {item}: {error}"
            )

        # Step 6: Save all data to JSON file
        logger.info("Step 6: Saving all data to JSON file...")
        self.save_all_data()

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
        self.all_courses.append(course_info)
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
        self.all_users.append(user_info)
        
        # Filter out courses that have already been processed
        course_links = user_info.get("course_links", [])
        new_course_urls = []
        
        for course_url in course_links:
            course_id = self.course_crawler.extract_id_from_url(course_url, "id")
            if course_id and course_id not in self.processed_courses:
                new_course_urls.append(course_url)
            self.users_courses.append({
                "user_id": user_id,
                "course_id": course_id
            })
        
        return new_course_urls

    def get_user_range(self, min_user_id: int, max_user_id: int) -> List[int]:
        """Get user range from userId.txt file."""
        with open("userId.txt", "r", encoding="utf-8") as f:
            user_ids = [int(line.strip()) for line in f.readlines()]
        
        user_ids.extend(range(min_user_id, max_user_id + 1))

        user_ids.sort()

        return user_ids
    
    def run_brute_force_users(self):
        """Execute brute force user ID crawling from MIN_USER_ID to MAX_USER_ID."""
        logger.info("=" * 60)
        logger.info("Starting Brute Force User Crawling")
        logger.info(f"Crawling user IDs from {self.config.min_user_id} to {self.config.max_user_id}")
        logger.info("=" * 60)
        
        # Generate all user URLs
        user_urls = []
        
        for user_id in self.get_user_range(self.config.min_user_id, self.config.max_user_id):
            user_url = self.user_crawler.build_url(f"/user/profile.php?id={user_id}&showallcourses=1")
            user_urls.append(user_url)
        
        logger.info(f"Generated {len(user_urls)} user URLs to crawl")
        
        # Crawl all users in batches
        logger.info("Crawling users in batches...")
        additional_course_urls = self.execute_parallel_flatten_batched(
            self.crawl_user_and_extract,
            user_urls,
            "Error processing user {item}: {error}"
        )

        
        logger.info(f"Discovered {len(additional_course_urls)} course URLs from users")
        
        # Crawl discovered courses in batches
        if additional_course_urls:
            logger.info("Crawling courses discovered from users in batches...")
            self.execute_parallel_flatten_batched(
                self.crawl_course_and_extract,
                additional_course_urls,
                "Error processing course {item}: {error}"
            )
        
        # Final save (in case there's any remaining data)
        if self.all_courses or self.all_users or self.users_courses:
            self.save_all_data()
        
        logger.info("=" * 60)
        logger.info("Brute Force Crawling completed!")
        logger.info(f"Total courses processed: {len(self.processed_courses)}")
        logger.info(f"Total users processed: {len(self.processed_users)}")
        logger.info("=" * 60)
        


    def save_all_data(self):
        """Save all data to JSON files."""
        logger.info("Saving all data to JSON files...")

        # Load existing data if files exist, otherwise start with empty lists
        try:
            with open("all_courses.json", "r", encoding="utf-8") as f:
                existing_courses = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_courses = []
        
        try:
            with open("all_users.json", "r", encoding="utf-8") as f:
                existing_users = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_users = []
        
        try:
            with open("users_courses.json", "r", encoding="utf-8") as f:
                existing_users_courses = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_users_courses = []
        
        # Append new data to existing data
        existing_courses.extend(self.all_courses)
        existing_users.extend(self.all_users)
        existing_users_courses.extend(self.users_courses)
        
        # Write combined data back to files
        with open("all_courses.json", "w", encoding="utf-8") as f:
            json.dump(existing_courses, f, ensure_ascii=False, indent=4)
        with open("all_users.json", "w", encoding="utf-8") as f:
            json.dump(existing_users, f, ensure_ascii=False, indent=4)
        with open("users_courses.json", "w", encoding="utf-8") as f:
            json.dump(existing_users_courses, f, ensure_ascii=False, indent=4)


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

