# HCMUT LMS Crawler

A Python-based crawler designed to archive data from the HCMUT LMS (e-learning) system. It traverses Semesters, Courses, and User profiles, saving the raw HTML content into structured directories.

## Features

- **Multi-threaded crawling** with configurable worker count
- **Idempotent operations** - skips already downloaded files
- **Graph traversal strategy** - discovers courses and users recursively
- **Structured output** - organized into `semesters/`, `courses/`, and `users/` directories
- **Error handling** - robust retry logic and comprehensive logging

## Installation

1. Clone the repository or download the source code
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

4. Edit `.env` and configure your settings:
   - `BASE_URL`: The root URL of the LMS (default: `https://lms.hcmut.edu.vn`)
   - `COOKIE`: Your authentication cookie (MoodleSession)
   - `NUMBER_OF_WORKERS`: Number of concurrent threads (default: 1)
   - `OUTPUT_DIR`: Base path for output folders (default: `./`)

## Getting Your Cookie

1. Log in to the HCMUT LMS in your browser
2. Open Developer Tools (F12)
3. Go to the Network tab
4. Refresh the page
5. Click on any request and find the `Cookie` header
6. Copy the entire cookie string (including `MoodleSession=...`)
7. Paste it into your `.env` file

## Usage

Run the crawler:

```bash
python main.py
```

The crawler will:
1. Discover all semesters from the course list page
2. Crawl each semester and extract course links
3. Crawl each course and extract teacher/user links
4. Crawl each user profile and discover additional courses
5. Save all HTML files to the appropriate directories

## Output Structure

```
./
├── semesters/
│   ├── {categoryId}.html
│   └── ...
├── courses/
│   ├── {courseId}.html
│   └── ...
└── users/
    ├── {userId}.html
    └── ...
```

## Architecture

The project uses Object-Oriented Design with the following modules:

- **`config.py`**: Configuration and environment variable handling
- **`html_saver.py`**: File system operations
- **`lms_crawler.py`**: Base crawler class with shared logic
- **`semester_crawler.py`**: Semester page crawling logic
- **`course_crawler.py`**: Course page crawling logic
- **`user_crawler.py`**: User profile crawling logic
- **`main.py`**: Main orchestration script

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- python-dotenv

## Notes

- All operations are idempotent - running the crawler multiple times will skip already downloaded files
- The crawler respects the LMS structure and follows links systematically
- Errors are logged but don't stop the entire crawl
- Text is normalized (trimmed, whitespace cleaned) for consistent processing

## License

This project is for educational purposes only.

