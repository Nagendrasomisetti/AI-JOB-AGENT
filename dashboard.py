import streamlit as st
import sqlite3
import pandas as pd

from main import run_agent


st.set_page_config(page_title="AI Job Dashboard", layout="wide")

st.title("🚀 AI Job Agent Dashboard")

if st.button("🔄 Fetch Latest Jobs"):
    with st.spinner("Running AI Agent..."):
        new_jobs = run_agent()

    st.success(f"✅ Found {len(new_jobs)} new jobs!")

# 🔥 Load data from DB
def load_jobs():
    conn = sqlite3.connect("jobs.db")
    df = pd.read_sql_query("SELECT * FROM jobs ORDER BY score DESC", conn)
    conn.close()
    return df


df = load_jobs()
if st.button("🔄 Refresh Data"):
    df = load_jobs()


# Remove incomplete persisted jobs
if not df.empty:
    df = df[df["title"].notna() & (df["title"] != "") & (df["title"].str.upper() != "N/A")]

if df.empty:
    st.warning("No jobs found. Run your agent first.")
    st.stop()


# 🔍 Search filter
search = st.text_input("🔍 Search jobs (title, company, skills)")

if search:
    df = df[
        df["title"].str.contains(search, case=False, na=False) |
        df["company"].str.contains(search, case=False, na=False) |
        df["skills"].str.contains(search, case=False, na=False)
    ]


# 📊 Show stats
st.subheader("📊 Stats")
col1, col2 = st.columns(2)

col1.metric("Total Jobs", len(df))
col2.metric("Top Score", df["score"].max())


# 📋 Display table
st.subheader("💼 Job Listings")

# Make links clickable
def make_clickable(link):
    return f'<a href="{link}" target="_blank">Apply</a>'


df["Apply"] = df["link"].apply(make_clickable)

st.write(
    df[[
        "title",
        "company",
        "location",
        "salary",
        "score",
        "Apply"
    ]].to_html(escape=False, index=False),
    unsafe_allow_html=True
)