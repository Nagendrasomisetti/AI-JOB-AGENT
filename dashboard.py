import streamlit as st
import pandas as pd
import logging
from main import run_agent
from utils.database import get_all_jobs, init_db

# Configure logger
logger = logging.getLogger("AIJobAgent.Dashboard")

# Page config
st.set_page_config(
    page_title="Autonomous AI Job Agent Control Center",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema if not present
init_db()

# ----------------------------------------------------
# 1. Custom CSS Styling (Premium Dark/Glassmorphic Aesthetics)
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
    
    .badge-internshala {
        background-color: rgba(56, 139, 253, 0.15);
        color: #58a6ff;
        border: 1px solid rgba(56, 139, 253, 0.3);
    }
    
    .badge-wellfound {
        background-color: rgba(243, 85, 37, 0.15);
        color: #f35525;
        border: 1px solid rgba(243, 85, 37, 0.3);
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
st.markdown('<div class="main-title">🤖 Autonomous AI Job Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">An advanced multi-source crawler, intelligent filtering, and compatibility scoring control center.</div>', unsafe_allow_html=True)

# Helper function to reload DB jobs cleanly
def load_data() -> pd.DataFrame:
    raw_jobs = get_all_jobs()
    if not raw_jobs:
        return pd.DataFrame()
    return pd.DataFrame(raw_jobs)

df = load_data()

# ----------------------------------------------------
# 3. Sidebar Configuration Center
# ----------------------------------------------------
st.sidebar.markdown("### ⚙️ Agent Control Panel")
st.sidebar.markdown("Configure search intent parameters for the autonomous agent planning phase.")

# Custom query inputs
search_intent = st.sidebar.text_input(
    "🔍 AI Agent Search Query",
    value="Find ML and AI jobs",
    help="Describe your career goals. The AI Agent will read this request, compile a plan, choose the appropriate platforms, and run search commands."
)

st.sidebar.markdown("---")

# Run agent trigger button
if st.sidebar.button("🚀 Execute Autonomous Run", use_container_width=True):
    with st.spinner("AI Agent thinking & formulating execution plan..."):
        # Setup status container to simulate live logs
        status_box = st.info("🤖 Agent launching. Setting up SQLite schemas and Chrome driver lifecycle...")
        
        try:
            # Trigger pipeline asynchronously/synchronously within a clean Streamlit spin
            new_jobs = run_agent(query=search_intent)
            
            # Update status message with complete information
            if new_jobs:
                st.sidebar.success(f"✅ Success! Discovered {len(new_jobs)} brand new opportunities!")
                status_box.success(f"🎉 Agent run complete! Scraping execution plan succeeded, and {len(new_jobs)} new listings were persisted & styled to Excel.")
            else:
                st.sidebar.info("ℹ️ Done! Scrape ran, but no brand-new listings were found (everything was deduplicated).")
                status_box.info("ℹ️ Scrape run complete. All scraped opportunities were already present in your historical database.")
                
            # Reload dataframe
            df = load_data()
            
        except Exception as err:
            st.sidebar.error(f"❌ Execution failed: {err}")
            status_box.error(f"❌ Critical Pipeline Failure: {err}")

st.sidebar.markdown("### 📊 Platform Info")
st.sidebar.info(
    "Currently scraping:\n"
    "- **Internshala** (Entry/Internships)\n"
    "- **Wellfound** (Startup/Full-time)"
)

# ----------------------------------------------------
# 4. Metrics & Statistics Panels
# ----------------------------------------------------
if not df.empty:
    # Perform standard data sanitization on load
    df = df[df["title"].notna() & (df["title"] != "") & (df["title"].str.upper() != "N/A")]

if df.empty:
    st.warning("🗃️ The job database is currently empty. Define a query in the left sidebar and click **Execute Autonomous Run** to discover opportunities!")
    st.stop()

# Compute KPI stats
total_jobs = len(df)
top_score = df["score"].max()
avg_score = df["score"].mean()

# High relevance threshold (score >= 50)
highly_relevant = len(df[df["score"] >= 50.0])
internshala_count = len(df[df["source"] == "Internshala"])
wellfound_count = len(df[df["source"] == "Wellfound"])

# Render metrics cards via CSS Grid
st.markdown(f"""
<div class="metric-container">
    <div class="metric-card">
        <div class="metric-title">📁 Total Persisted</div>
        <div class="metric-value">{total_jobs}</div>
        <div class="metric-desc">Jobs in SQLite storage</div>
    </div>
    <div class="metric-card">
        <div class="metric-title">🔥 Match Index</div>
        <div class="metric-value">{highly_relevant}</div>
        <div class="metric-desc">Score ≥ 50 compatibility</div>
    </div>
    <div class="metric-card">
        <div class="metric-title">⭐ Top Score</div>
        <div class="metric-value">{top_score}</div>
        <div class="metric-desc">Maximum suitability score</div>
    </div>
    <div class="metric-card">
        <div class="metric-title">🌐 Platform Splits</div>
        <div class="metric-value">{internshala_count} / {wellfound_count}</div>
        <div class="metric-desc">Internshala / Wellfound</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 5. Search, Filter & Presentation Grid
# ----------------------------------------------------
st.markdown("### 💼 Discovered Career Opportunities")

col_search, col_source = st.columns([3, 1])

# Search bar
search_term = col_search.text_input("🔍 Quick Filter Listings", placeholder="Filter by Title, Company, or Skill Tag...")

# Source filter
source_filter = col_source.selectbox("🌐 Platform Filter", ["All Platforms", "Internshala", "Wellfound"])

# Filter dataframe
filtered_df = df.copy()

if search_term:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_term, case=False, na=False) |
        filtered_df["company"].str.contains(search_term, case=False, na=False) |
        filtered_df["skills"].str.contains(search_term, case=False, na=False)
    ]

if source_filter != "All Platforms":
    filtered_df = filtered_df[filtered_df["source"] == source_filter]

# Render interactive list
if filtered_df.empty:
    st.info("🔍 No listings match your filter parameters. Try expanding your search queries!")
else:
    # Format and present HTML elements dynamically
    display_df = filtered_df.copy()
    
    # 1. Format Link
    def format_link(url):
        return f'<a href="{url}" target="_blank" class="apply-btn">Apply ↗</a>'
    display_df["Apply"] = display_df["link"].apply(format_link)
    
    # 2. Format Source Platform Badges
    def format_source(src):
        badge_class = "badge-internshala" if src.lower() == "internshala" else "badge-wellfound"
        return f'<span class="badge {badge_class}">{src}</span>'
    display_df["Source"] = display_df["source"].apply(format_source)
    
    # 3. Format Scores into colored priority tags
    def format_score(score):
        badge_class = "badge-score-high" if score >= 50.0 else "badge-score-med"
        return f'<span class="badge {badge_class}">{score}</span>'
    display_df["Match Score"] = display_df["score"].apply(format_score)

    # Reorder display frame columns for neat presentation
    display_df = display_df[[
        "title",
        "company",
        "location",
        "salary",
        "skills",
        "Source",
        "Match Score",
        "Apply"
    ]]

    display_df.columns = [
        "Job Title",
        "Company",
        "Location",
        "Salary / Stipend",
        "Skills Required",
        "Source Platform",
        "Compatibility Match",
        "Action"
    ]

    # Render Styled Table
    st.write(
        display_df.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )