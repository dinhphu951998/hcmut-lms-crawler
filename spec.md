# HCMUT LMS Crawler Specification

## 1. Overview
This project is a Python-based crawler designed to archive data from the HCMUT LMS (e-learning) system. It traverses Semesters, Courses, and User profiles, saving the raw HTML content of these pages into structured directories. The extracted data from these HTML files will be processed in a separate pipeline (future scope), though the crawler uses intermediate extraction for navigation.

## 2. Configuration
The application is configured via a `.env` file in the root directory.

### Environment Variables
| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `BASE_URL` | The root URL of the LMS. | `https://lms.hcmut.edu.vn` |
| `COOKIE` | Authentication cookie string (MoodleSession, etc.). | `MoodleSession=...` |
| `NUMBER_OF_WORKERS` | Number of concurrent crawling threads/processes. | `1` |
| `OUTPUT_DIR` | (Optional) Base path for output folders. | `./` |

## 3. Architecture & Design

### 3.1 Technology Stack
*   **Language**: Python
*   **Networking**: `requests` (for HTTP), `beautifulsoup4` (for HTML parsing/link extraction).
*   **Concurrency**: `concurrent.futures` (ThreadPoolExecutor) for handling `NUMBER_OF_WORKERS`.

### 3.2 Object-Oriented Design
The codebase will be modular, following OOP principles:
*   **`Config`**: Handles environment variable loading and validation.
*   **`HtmlSaver`**: Handles file system operations (checking existence, saving files).
*   **`LmsCrawler` (Base Class)**: Shared logic for HTTP requests, error handling, and text normalization.
*   **`SemesterCrawler`**: Logic for parsing the initial course category selection and processing semester pages.
*   **`CourseCrawler`**: Logic for processing course pages and extracting teacher links.
*   **`UserCrawler`**: Logic for processing user profile pages and discovering additional courses.

### 3.3 Data Flow & Traversal strategy
The crawler operates as a graph traversal engine:
1.  **Entry Point**: Access the global course list page (`/course/`).
2.  **Semester Discovery**:
    *   Parse `select.urlselect` options.
    *   Filter options matching the regex structure: `Semester / Faculty / Major`.
    *   **Action**: Download Semester HTML -> `semesters/{categoryId}.html`.
3.  **Course Discovery (via Semester)**:
    *   Parse links (`a.aalink`) inside the Semester HTML.
    *   **Action**: Download Course HTML -> `courses/{courseId}.html`.
4.  **User Discovery (via Course)**:
    *   Parse teacher links (`ul.teachers a`) inside Course HTML.
    *   **Action**: Download User HTML -> `users/{userId}.html`.
5.  **Recursive Course Discovery (via User)**:
    *   Parse "Course profiles" (`section` inside `div.profile_tree`) in User HTML.
    *   **Action**: Check if course exists; if not, add to Course queue to download.

## 4. Functional Requirements

### 4.1 Semester Module
*   **Input**: Base URL `/course/`.
*   **Logic**:
    *   Select all `<option>` tags from `select.urlselect`.
    *   **Validation**: Option text must match format `"{Semester} / {Faculty} / {Major}"`.
    *   **Extraction**:
        *   Semester: e.g., "Học kỳ (Semester) 2/2025-2026"
        *   Faculty: e.g., "Khoa Khoa học và Kỹ thuật Máy tính..."
        *   Major: e.g., "Khoa Học Máy Tính"
    *   **Execution**: Navigate to the option's value (URL), append `&perpage=all` to bypass pagination.
    *   **Output**: Save HTML to `semesters/{categoryId}.html`.

### 4.2 Course Module
*   **Input**: URL from Semester list or User profile.
*   **Logic**:
    *   Access course URL.
    *   **Extraction**:
        *   Course Name: `div.coursename` text.
        *   Teachers: `ul.teachers` text.
        *   Teacher Links: `a` tags inside `ul.teachers`.
    *   **Execution**:
        *   Save Course HTML.
        *   Queue discovered Teacher URLs for `UserCrawler`.
    *   **Output**: Save HTML to `courses/{courseId}.html`.

### 4.3 User Module
*   **Input**: URL from Course teacher list.
*   **Logic**:
    *   Access user URL (ensure `&showallcourses=1` if applicable/available, or parse from profile).
    *   **Extraction**:
        *   Teacher Name: `page-header-headings` text.
        *   Role: `.userprofile .description` text.
        *   Profile Details: `div.profile_tree` (Section 0 - `dt`/`dd` pairs).
        *   Course Links: `div.profile_tree` (Section 1 - `a` tags).
    *   **Execution**:
        *   Save User HTML.
        *   Queue discovered Course URLs for `CourseCrawler` (check existence before queuing).
    *   **Output**: Save HTML to `users/{userId}.html`.

## 5. Non-Functional Requirements
*   **Idempotency**: Before downloading any file, check if it already exists in the target folder. If it exists, skip the network request and saving.
*   **Sanitization**: All extracted text for logging or logic must be trimmed and normalized (remove excessive whitespace).
*   **Error Handling**:
    *   Network failures should be logged but should not crash the entire crawl (retry or skip).
    *   Invalid HTML structures should be logged as warnings.

