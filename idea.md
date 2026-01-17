I want to build a crawler that crawl data from these pages:

## Semester:
1. Access page "/course/" and get html from that page
2. Select "select.urlselect" and get all options tag
3. The option text will contain the structure like this
    E.g. "Học kỳ (Semester) 2/2025-2026 / Khoa Khoa học và Kỹ thuật Máy tính (Faculty of Computer Science and Engineering) / Khoa Học Máy Tính"
    "Học kỳ (Semester) 2/2025-2026": This is the semester
    "Khoa Khoa học và Kỹ thuật Máy tính (Faculty of Computer Science and Engineering)": Is the faculty
    "Khoa Học Máy Tính": is the major
4. Process the options that contain all 3 parts, skip if it not met the format
5. Get the value of the option, and continue to access the page. This page contain all the courses (concate &perpage=all to ignore paging)
6. For each valid option, get html of the link and save it as new file in "semesters" folder. The file name is the {categoryId}.html
7. Continue next section to extract courses

## Courses:
1. Query a.aalink and get html from the href link 
2. Save the html content as new file in "courses" folder, the file name is the {courseId}.html
3. Get the course name from div.coursename inner text
4. Get the teachers name from ul.teachers inner text
5. Get a.href to access teacher url (&showallcourses=1)
6. Save teacher html content to "users" folder, the file name is the {id}.html with id parsed from teacher url
7. Move next to Users to extract user

## Users:
1. From the user html content, get the following information
2. Teacher name: "page-header-headings" text()
3. Role: ".userprofile .description" text()
4. "div.profile_tree" contains multiple section tags as describing below

### User profile (sections 0)
1. Get all dt in this section and all dd in this section
2. Each dt and dd will map to a coresponding data pair
3. Normally, they are an array of 4 pairs: email, country, city, timezone


### Course profiles (sections 1)
1. Get all tag a in section 1
2. Get text as course name
3. Get href of tag a and parse "course" parameter from the href. If the course existed in the "courses" folder, you will skip it. Otherwise, getting html of the href and save html content as new file under "courses" folder, the file name is {courseId}.html


# Notice:
- All the text need to be sanitised, trim, normalize
- The code should be broken into functions for better usuability and follow OOP to support the maintenance
- Programming language: python
- use .env file to adapt configuration changes
- During the file saving, you should check if the file already existed and skip the save in that case.
- Should handle exception so it will not break if there are exceptions