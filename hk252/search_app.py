import streamlit as st
import pandas as pd
import os

# Set page config
st.set_page_config(
    page_title="HK252 Data Search",
    page_icon="🔍",
    layout="wide"
)

# Load CSV files with lazy loading per tab
@st.cache_data
def load_courses_data():
    """Load courses CSV file"""
    base_path = os.path.dirname(__file__)
    return pd.read_csv(os.path.join(base_path, "courses_hk252.csv"))

@st.cache_data
def load_slot_data():
    """Load slot CSV file"""
    base_path = os.path.dirname(__file__)
    return pd.read_csv(os.path.join(base_path, "slot_hk252.csv"))

@st.cache_data
def load_user_course_data():
    """Load user course CSV file"""
    base_path = os.path.dirname(__file__)
    return pd.read_csv(os.path.join(base_path, "user_course_hk252.csv"))

@st.cache_data
def get_dataset_info():
    """Load dataset info from CSV, or create it if it doesn't exist"""
    base_path = os.path.dirname(__file__)
    info_path = os.path.join(base_path, "dataset_info.csv")
    
    # Check if dataset_info.csv exists
    if os.path.exists(info_path):
        # Load from CSV
        info_df = pd.read_csv(info_path)
        # Convert columns string back to list for each dataset
        dataset_info = {}
        for _, row in info_df.iterrows():
            dataset_info[row['dataset_name']] = {
                'total_records': int(row['total_records']),
                'columns': row['columns'].split(', ')
            }
        return dataset_info
    else:
        # Create dataset_info.csv by loading all datasets
        courses_df = load_courses_data()
        slot_df = load_slot_data()
        user_course_df = load_user_course_data()
        
        # Create info dictionary
        dataset_info = {
            'Course': {
                'total_records': len(courses_df),
                'columns': courses_df.columns.tolist()
            },
            'Slot': {
                'total_records': len(slot_df),
                'columns': slot_df.columns.tolist()
            },
            'User Course': {
                'total_records': len(user_course_df),
                'columns': user_course_df.columns.tolist()
            }
        }
        
        # Save to CSV
        info_data = []
        for dataset_name, info in dataset_info.items():
            info_data.append({
                'dataset_name': dataset_name,
                'total_records': info['total_records'],
                'columns': ', '.join(info['columns'])
            })
        
        info_df = pd.DataFrame(info_data)
        info_df.to_csv(info_path, index=False)
        
        return dataset_info

# Initialize session state for each tab independently
if 'course_search_query' not in st.session_state:
    st.session_state.course_search_query = ""
if 'slot_search_query' not in st.session_state:
    st.session_state.slot_search_query = ""
if 'user_search_query' not in st.session_state:
    st.session_state.user_search_query = ""

# Title
st.title("🔍 HK252 Data Search")
st.markdown("Search across courses, slots, and user-course data")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📚 Course", "📅 Slot", "👥 User Course"])

def perform_search(df, query, max_results=None):
    """Perform case-insensitive search across all columns with AND logic for multiple terms"""
    if not query:
        return pd.DataFrame(), 0
    
    # Parse multiple search terms (split by "and" or "&")
    # Remove extra whitespace and filter out empty strings
    query_lower = query.lower()
    terms = [term.strip() for term in query_lower.replace('&', 'and').split('and') if term.strip()]
    
    if not terms:
        return pd.DataFrame(), 0
    
    # Start with all True (we'll AND conditions)
    mask = pd.Series([True] * len(df))
    
    # For each term, check if it exists in ANY column of the row
    # All terms must be found (AND logic)
    for term in terms:
        term_mask = pd.Series([False] * len(df))
        # Check if term exists in any column
        for col in df.columns:
            term_mask |= df[col].astype(str).str.lower().str.contains(term, na=False, regex=False)
        # AND with previous mask
        mask &= term_mask
    
    results = df[mask].copy()
    total_matches = len(results)
    
    # Apply limit if specified
    if max_results is not None:
        results = results.head(max_results)
    
    return results, total_matches

def display_results(results, total_matches, displayed_count, query, dataset_name, df):
    """Display search results with expandable rows"""
    if displayed_count > 0:
        st.success(f"Found {total_matches} match(es). Showing {displayed_count} result(s).")
        
        # Display results with expandable rows
        for idx, row in results.iterrows():
            # Create expander title based on dataset
            if dataset_name == "Course":
                title = f"📚 {row['course_code']} - {row['name'][:80]}..." if len(str(row['name'])) > 80 else f"📚 {row['course_code']} - {row['name']}"
            elif dataset_name == "Slot":
                title = f"📅 {row['code']} - {row['name'][:80]}..." if len(str(row['name'])) > 80 else f"📅 {row['code']} - {row['name']}"
            else:  # User Course
                title = f"👥 {row['course_code']} - {row['user_name'][:60]}..." if len(str(row['user_name'])) > 60 else f"👥 {row['course_code']} - {row['user_name']}"
            
            with st.expander(title, expanded=False):
                # Display all columns in a table format
                st.markdown("**Full Details:**")
                detail_df = pd.DataFrame({
                    'Field': [col.replace('_', ' ').title() for col in df.columns],
                    'Value': [row[col] for col in df.columns]
                })
                st.table(detail_df)
        
        # Option to download results
        csv = results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"{dataset_name.lower().replace(' ', '_')}_search_results_{query.replace(' ', '_')}.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"No results found for '{query}'. Found {total_matches} total match(es).")
        if total_matches > displayed_count:
            st.info(f"💡 Tip: Increase the 'Max Results' limit to see more results (currently showing {displayed_count} of {total_matches}).")

# ========== COURSE TAB ==========
with tab1:
    # Load dataset only when this tab is accessed
    courses_df = load_courses_data()
    
    st.header("📚 Course Search")
    st.markdown("Search courses across all columns")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query_course = st.text_input(
            "Search Query",
            value=st.session_state.course_search_query,
            placeholder="Enter keywords (use 'and' or '&' for multiple terms)...",
            label_visibility="collapsed",
            key="course_search_input"
        )
    
    with col2:
        limit_options = {"50": 50, "100": 100, "200": 200, "All": None}
        limit_choice_course = st.selectbox(
            "Max Results",
            options=list(limit_options.keys()),
            index=1,  # Default to 200
            label_visibility="collapsed",
            key="course_limit"
        )
        max_results_course = limit_options[limit_choice_course]
    
    # Search button
    search_button_course = st.button("🔍 Search", type="primary", use_container_width=True, key="course_search_btn")
    
    # Update session state when search button is clicked
    if search_button_course:
        st.session_state.course_search_query = search_query_course
    
    # Perform search
    current_query_course = st.session_state.course_search_query if st.session_state.course_search_query else (search_query_course if search_button_course else "")
    
    if current_query_course:
        results_course, total_matches_course = perform_search(courses_df, current_query_course, max_results_course)
        displayed_count_course = len(results_course)
        display_results(results_course, total_matches_course, displayed_count_course, current_query_course, "Course", courses_df)
    elif search_button_course:
        st.info("Please enter a search query.")

# ========== SLOT TAB ==========
with tab2:
    # Load dataset only when this tab is accessed
    slot_df = load_slot_data()
    
    st.header("📅 Slot Search")
    st.markdown("Search course slots across all columns")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query_slot = st.text_input(
            "Search Query",
            value=st.session_state.slot_search_query,
            placeholder="Enter keywords (use 'and' or '&' for multiple terms)...",
            label_visibility="collapsed",
            key="slot_search_input"
        )
    
    with col2:
        limit_options = {"50": 50, "100": 100, "200": 200, "All": None}
        limit_choice_slot = st.selectbox(
            "Max Results",
            options=list(limit_options.keys()),
            index=1,  # Default to 200
            label_visibility="collapsed",
            key="slot_limit"
        )
        max_results_slot = limit_options[limit_choice_slot]
    
    # Search button
    search_button_slot = st.button("🔍 Search", type="primary", use_container_width=True, key="slot_search_btn")
    
    # Update session state when search button is clicked
    if search_button_slot:
        st.session_state.slot_search_query = search_query_slot
    
    # Perform search
    current_query_slot = st.session_state.slot_search_query if st.session_state.slot_search_query else (search_query_slot if search_button_slot else "")
    
    if current_query_slot:
        results_slot, total_matches_slot = perform_search(slot_df, current_query_slot, max_results_slot)
        displayed_count_slot = len(results_slot)
        display_results(results_slot, total_matches_slot, displayed_count_slot, current_query_slot, "Slot", slot_df)
    elif search_button_slot:
        st.info("Please enter a search query.")

# ========== USER COURSE TAB ==========
with tab3:
    # Load dataset only when this tab is accessed
    user_course_df = load_user_course_data()
    
    st.header("👥 User Course Search")
    st.markdown("Search user-course relationships across all columns")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query_user = st.text_input(
            "Search Query",
            value=st.session_state.user_search_query,
            placeholder="Enter keywords (use 'and' or '&' for multiple terms)...",
            label_visibility="collapsed",
            key="user_search_input"
        )
    
    with col2:
        limit_options = {"50": 50, "100": 100, "200": 200, "All": None}
        limit_choice_user = st.selectbox(
            "Max Results",
            options=list(limit_options.keys()),
            index=1,  # Default to 200
            label_visibility="collapsed",
            key="user_limit"
        )
        max_results_user = limit_options[limit_choice_user]
    
    # Search button
    search_button_user = st.button("🔍 Search", type="primary", use_container_width=True, key="user_search_btn")
    
    # Update session state when search button is clicked
    if search_button_user:
        st.session_state.user_search_query = search_query_user
    
    # Perform search
    current_query_user = st.session_state.user_search_query if st.session_state.user_search_query else (search_query_user if search_button_user else "")
    
    if current_query_user:
        results_user, total_matches_user = perform_search(user_course_df, current_query_user, max_results_user)
        displayed_count_user = len(results_user)
        display_results(results_user, total_matches_user, displayed_count_user, current_query_user, "User Course", user_course_df)
    elif search_button_user:
        st.info("Please enter a search query.")

# Display data info in sidebar (use dataset_info.csv for quick loading)
with st.sidebar:
    st.header("📊 Dataset Info")
    
    # Load dataset info from CSV (or create it if it doesn't exist)
    dataset_info = get_dataset_info()
    
    st.subheader("📚 Course")
    st.write(f"**Total Records:** {dataset_info['Course']['total_records']:,}")
    st.write(f"**Columns:** {', '.join(dataset_info['Course']['columns'])}")
    
    st.markdown("---")
    st.subheader("📅 Slot")
    st.write(f"**Total Records:** {dataset_info['Slot']['total_records']:,}")
    st.write(f"**Columns:** {', '.join(dataset_info['Slot']['columns'])}")
    
    st.markdown("---")
    st.subheader("👥 User Course")
    st.write(f"**Total Records:** {dataset_info['User Course']['total_records']:,}")
    st.write(f"**Columns:** {', '.join(dataset_info['User Course']['columns'])}")
    
    st.markdown("---")
    st.header("💡 Search Tips")
    st.markdown("""
    - Search is **case-insensitive**
    - Searches across **all columns**
    - Use partial matches (e.g., "co3015" or "bùi")
    - **Multiple terms**: Use "and" or "&" to search for multiple terms
      - Example: `co3015 and bùi` finds rows containing both "co3015" AND "bùi"
      - Example: `software & testing` finds rows containing both terms
    - Results are expandable - click to see full details
    - Each tab has **independent search** - switch tabs without losing your queries
    """)
