import streamlit as st
import pandas as pd
import logging
import threading
from utils.database import get_all_jobs, init_db
from main import run_agent

# Configure logger
logger = logging.getLogger("AIJobAgent.Dashboard")

# Page config
st.set_page_config(
    page_title="Centralized AI Job Aggregation Control Center",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure database schema is migrated
init_db()

# ----------------------------------------------------
# 1. Custom CSS Styling (Premium Dark Glassmorphic Theme)
# ----------------------------------------------------
st.markdown("""
<style>
    /* Dark glassmorphic container base styling */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Title banner styling */
    .main-title {
        background: linear-gradient(135deg, #58a6ff 0%, #1f6feb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #8b949e;
        margin-bottom: 2rem;
    }

    /* Metric card wrapper */
    .metric-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 12px;
        padding: 1.25rem;
        flex: 1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #58a6ff;
    }
    
    .metric-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        color: #8b949e;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #f0f6fc;
        line-height: 1;
    }
    
    .metric-desc {
        font-size: 0.75rem;
        color: #58a6ff;
        margin-top: 0.4rem;
    }

    /* Premium styled table container */
    div[data-testid="stHtml"] table {
        width: 100%;
        border-collapse: collapse;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        overflow: hidden;
        color: #c9d1d9;
    }
    
    div[data-testid="stHtml"] th {
        background-color: #21262d !important;
        color: #58a6ff !important;
        font-weight: 600 !important;
        text-align: center !important;
        padding: 14px 10px !important;
        border-bottom: 2px solid #30363d !important;
    }
    
    div[data-testid="stHtml"] td {
        padding: 12px 10px !important;
        border-bottom: 1px solid #21262d !important;
        text-align: center;
        vertical-align: middle;
    }
    
    div[data-testid="stHtml"] tr:hover {
        background-color: rgba(88, 166, 255, 0.04) !important;
    }
    
    /* Apply Link styling */
    .apply-btn {
        display: inline-block;
        background: linear-gradient(135deg, #1f6feb 0%, #094cb5 100%);
        color: #ffffff !important;
        text-decoration: none !important;
        padding: 6px 14px;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 6px;
        transition: background 0.2s ease;
    }
    
    .apply-btn:hover {
        background: linear-gradient(135deg, #388bfd 0%, #1f6feb 100%);
        box-shadow: 0 0 8px rgba(56, 139, 253, 0.3);
    }
    
    /* Platform Badge tags */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 4px;
        text-transform: uppercase;
    }
    
    .badge-api {
        background-color: rgba(56, 139, 253, 0.15);
        color: #58a6ff;
        border: 1px solid rgba(56, 139, 253, 0.3);
    }
    
    .badge-scraper {
        background-color: rgba(227, 179, 65, 0.15);
        color: #e3b341;
        border: 1px solid rgba(227, 179, 65, 0.3);
    }
    
    .badge-score-high {
        background-color: rgba(57, 219, 109, 0.15);
        color: #39db6d;
        border: 1px solid rgba(57, 219, 109, 0.3);
        font-weight: bold;
    }
    
    .badge-score-med {
        background-color: rgba(227, 179, 65, 0.15);
        color: #e3b341;
        border: 1px solid rgba(227, 179, 65, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Main Header Presentation
# ----------------------------------------------------
st.markdown('<div class="main-title">🤖 AI Job Aggregation Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Centralized Job Intelligence Platform — Ingestion happens in the background every 24 hours. Sub-second database queries.</div>', unsafe_allow_html=True)

# Helper function to reload DB jobs cleanly
def load_data() -> pd.DataFrame:
    raw_jobs = get_all_jobs()
    if not raw_jobs:
        return pd.DataFrame()
    return pd.DataFrame(raw_jobs)

df = load_data()

# ----------------------------------------------------
# 3. Sidebar Configuration Center (Decoupled Background Trigger)
# ----------------------------------------------------
st.sidebar.markdown("### ⚙️ platform Management")
st.sidebar.markdown("Configure search parameters to trigger background daemon collection runs.")

search_intent = st.sidebar.text_input(
    "🔍 Daemon Search Query",
    value="Find ML and AI jobs",
    help="Define the query scope for the background scheduler sweeps."
)

st.sidebar.markdown("---")

# Asynchronous, decoupled background ETL execution
if st.sidebar.button("🚀 Trigger Background Ingestion Sweep", use_container_width=True):
    # Spin up run_agent in a detached background thread
    daemon_thread = threading.Thread(
        target=run_agent, 
        args=(search_intent, 5), 
        daemon=True
    )
    daemon_thread.start()
    
    st.sidebar.success("🤖 Ingestion Daemon triggered in the background!")
    st.info(
        "🤖 Ingestion Daemon started in the background! Collectors (APIs + Scrapers) are pulling data asynchronously. "
        "Your UI is fully active. Refresh the page in 1-2 minutes to display the newly discovered, scored listings."
    )

if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    df = load_data()
    st.sidebar.success("Database cache updated successfully!")

st.sidebar.markdown("### 📊 Active Collectors")
st.sidebar.info(
    "**API-based Sources:**\n"
    "- Arbeitnow (Public stream)\n"
    "- Adzuna (Developer endpoints)\n"
    "- JSearch (Aggregator RapidAPI)\n\n"
    "**Web-based Scrapers:**\n"
    "- Internshala (Selenium)\n"
    "- Wellfound (Selenium)\n"
    "- Cutshort (Selenium)"
)

# ----------------------------------------------------
# 4. Metrics & Statistics Panels
# ----------------------------------------------------
if not df.empty:
    df = df[df["title"].notna() & (df["title"] != "") & (df["title"].str.upper() != "N/A")]

if df.empty:
    st.warning("🗃️ The job database is currently empty. Trigger a background ingestion sweep from the sidebar to populate listings.")
    st.stop()

# Compute KPI stats from memory instantly
total_jobs = len(df)
top_score = df["score"].max()

# Split checks
api_count = len(df[df["source_type"] == "API"])
scraper_count = len(df[df["source_type"] == "Scraper"])
highly_relevant = len(df[df["score"] >= 50.0])

# Render metrics cards via CSS Grid
st.markdown(f"""
<div class="metric-container">
    <div class="metric-card">
        <div class="metric-title">📁 Total Jobs</div>
        <div class="metric-value">{total_jobs}</div>
        <div class="metric-desc">Sub-second reads from SQLite</div>
    </div>
    <div class="metric-card">
        <div class="metric-title">🔥 Suitability Matches</div>
        <div class="metric-value">{highly_relevant}</div>
        <div class="metric-desc">Score ≥ 50 compatibility</div>
    </div>
    <div class="metric-card">
        <div class="metric-title">⭐ Max Score</div>
        <div class="metric-value">{top_score}</div>
        <div class="metric-desc">Peak matching compatibility</div>
    </div>
    <div class="metric-card">
        <div class="metric-title">🔌 Ingestion splits</div>
        <div class="metric-value">{api_count} / {scraper_count}</div>
        <div class="metric-desc">API sources / Scrapers</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 5. Interactive Table & Search Filters
# ----------------------------------------------------
st.markdown("### 💼 Centralized Job Intelligence Grid")

col_search, col_source_type, col_platform = st.columns([2, 1, 1])

# Dynamic search boxes
search_term = col_search.text_input("🔍 Quick search jobs", placeholder="Filter by Title, Company, or Skill Tag...")
source_type_filter = col_source_type.selectbox("🔌 Ingestion Layer", ["All Sources", "API", "Scraper"])

# Populate platforms list dynamically from DB entries
available_sources = ["All Platforms"] + sorted(list(df["source"].unique()))
platform_filter = col_platform.selectbox("🌐 Platform Filter", available_sources)

# Execute filtering instantly in memory
filtered_df = df.copy()

if search_term:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_term, case=False, na=False) |
        filtered_df["company"].str.contains(search_term, case=False, na=False) |
        filtered_df["skills"].str.contains(search_term, case=False, na=False)
    ]

if source_type_filter != "All Sources":
    filtered_df = filtered_df[filtered_df["source_type"] == source_type_filter]

if platform_filter != "All Platforms":
    filtered_df = filtered_df[filtered_df["source"] == platform_filter]

# Render interactive HTML table
if filtered_df.empty:
    st.info("🔍 No listings match your filter parameters. Try expanding your search terms!")
else:
    display_df = filtered_df.copy()
    
    # 1. Format Clickable Hyperlink
    def format_link(url):
        return f'<a href="{url}" target="_blank" class="apply-btn">Apply ↗</a>'
    display_df["Apply"] = display_df["link"].apply(format_link)
    
    # 2. Format Ingestion Source Badges
    def format_source_type(stype):
        badge_class = "badge-api" if stype.upper() == "API" else "badge-scraper"
        return f'<span class="badge {badge_class}">{stype}</span>'
    display_df["Type"] = display_df["source_type"].apply(format_source_type)
    
    # 3. Format Scores into priority tags
    def format_score(score):
        badge_class = "badge-score-high" if score >= 50.0 else "badge-score-med"
        return f'<span class="badge {badge_class}">{score}</span>'
    display_df["Match Score"] = display_df["score"].apply(format_score)

    # 4. Format Timestamps nicely
    def format_timestamp(ts):
        try:
            return ts.split(".")[0].split()[0] # YYYY-MM-DD
        except:
            return str(ts)
    display_df["Fetched At"] = display_df["fetched_at"].apply(format_timestamp)

    # Reorder columns
    display_df = display_df[[
        "title",
        "company",
        "location",
        "salary",
        "skills",
        "source",
        "Type",
        "Match Score",
        "Fetched At",
        "Apply"
    ]]

    display_df.columns = [
        "Job Title",
        "Company",
        "Location",
        "Salary / Stipend",
        "Skills Required",
        "Platform",
        "Source Type",
        "Compatibility Match",
        "Fetched At",
        "Action"
    ]

    # Display standard responsive HTML
    st.write(
        display_df.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )