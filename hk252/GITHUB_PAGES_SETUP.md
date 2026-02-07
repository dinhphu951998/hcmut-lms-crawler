# GitHub Pages Setup Guide

This guide will help you host the search app on GitHub Pages as a static site.

## Prerequisites

- A GitHub account
- Your repository pushed to GitHub
- CSV files: `courses_hk252.csv`, `slot_hk252.csv`, `user_course_hk252.csv`, `dataset_info.csv`

## Setup Steps

### Option 1: Host from `hk252` folder (Recommended)

1. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Click **Settings** → **Pages**
   - Under "Source", select **Deploy from a branch**
   - Select branch: **main** (or your default branch)
   - Select folder: **/hk252**
   - Click **Save**

2. **Access your site:**
   - Your site will be available at: `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/hk252/`
   - Example: `https://username.github.io/hcmut-lms-crawler/hk252/`

### Option 2: Host from root (Alternative)

If you want the site at the root URL:

1. Move `index.html` to the repository root
2. Update CSV file paths in `index.html`:
   - Change `'courses_hk252.csv'` → `'hk252/courses_hk252.csv'`
   - Change `'slot_hk252.csv'` → `'hk252/slot_hk252.csv'`
   - Change `'user_course_hk252.csv'` → `'hk252/user_course_hk252.csv'`
   - Change `'dataset_info.csv'` → `'hk252/dataset_info.csv'`
3. Enable GitHub Pages from root folder

## File Structure

Your repository should have this structure:

```
hcmut-lms-crawler/
├── hk252/
│   ├── index.html              # Main HTML file
│   ├── courses_hk252.csv        # Course data
│   ├── slot_hk252.csv          # Slot data
│   ├── user_course_hk252.csv   # User course data
│   ├── dataset_info.csv         # Dataset metadata
│   └── README_SEARCH.md        # Documentation
└── ...
```

## Important Notes

1. **CSV Files Must Be Accessible:**
   - Make sure all CSV files are committed to the repository
   - They should be in the same directory as `index.html`

2. **File Size Limits:**
   - GitHub Pages has a 1GB repository size limit
   - Individual files should be under 100MB
   - Your CSV files should be fine, but check if `user_course_hk252.csv` is very large

3. **CORS Issues:**
   - GitHub Pages serves files with proper CORS headers
   - The PapaParse library handles CSV parsing client-side

4. **Performance:**
   - Large CSV files may take time to load
   - Data loads lazily (only when you search in each tab)
   - Consider compressing CSV files if they're very large

## Testing Locally

Before deploying, test locally:

1. **Using Python HTTP server:**
   ```bash
   cd hk252
   python -m http.server 8000
   ```
   Then open `http://localhost:8000` in your browser

2. **Using VS Code Live Server:**
   - Install "Live Server" extension
   - Right-click `index.html` → "Open with Live Server"

## Troubleshooting

### CSV files not loading
- Check browser console for errors
- Verify CSV file paths are correct
- Ensure CSV files are committed to the repository

### Search not working
- Check browser console for JavaScript errors
- Verify PapaParse library is loading (check Network tab)
- Make sure CSV files are valid CSV format

### Page not updating
- GitHub Pages can take a few minutes to update
- Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)
- Check GitHub Pages build status in Settings → Pages

## Custom Domain (Optional)

If you want to use a custom domain:

1. Add a `CNAME` file in your repository root with your domain
2. Configure DNS settings as GitHub instructs
3. Update GitHub Pages settings to use custom domain

## Features

The static version includes:
- ✅ All three tabs (Course, Slot, User Course)
- ✅ Case-insensitive search
- ✅ Multiple search terms with AND logic (`term1 and term2`)
- ✅ Expandable result rows
- ✅ CSV download functionality
- ✅ Results limit selector (50/100/200/All)
- ✅ Lazy loading (datasets load only when searched)
- ✅ Responsive design

Enjoy your hosted search app! 🎉
