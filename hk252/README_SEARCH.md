# Course Search Web App

A simple Streamlit web application to search courses in the `courses_hk252.csv` file.

## Features

- 🔍 Search across all columns (case-insensitive, contains match)
- 📊 Expandable rows - click to see full course details
- 📥 Download search results as CSV
- 🎯 Limit results: 50, 100, 200, or All
- 💡 Sample search buttons in sidebar

## Installation

1. Install required packages:
```bash
pip install -r ../requirements.txt
```

Or install directly:
```bash
pip install streamlit pandas
```

## Running the App

Navigate to the `hk252` directory and run:

```bash
streamlit run search_app.py
```

The app will open in your default web browser at `http://localhost:8501`

## Usage

1. Enter your search query in the search box (e.g., "co3015", "bùi hoài thắng", "software")
2. Select the maximum number of results to display (50/100/200/All)
3. Click the "🔍 Search" button
4. Click on any result to expand and see full details
5. Download results as CSV if needed

## Search Behavior

- **Case-insensitive**: "CO3015" matches "co3015"
- **Contains match**: "co" matches "co3015", "co3069", etc.
- **All columns**: Searches across ID, Name, Teachers, Course Code, Semester, Program Code, and Program
