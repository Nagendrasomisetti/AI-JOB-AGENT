import logging
from typing import List, Dict, Any, Tuple
from utils.ai_filter import is_relevant_job

logger = logging.getLogger("AIJobAgent.Filter")

# Deterministic keywords for instant matching/skipping
POSITIVE_TITLE_KEYWORDS = [
    "machine learning", "ml", "ai", "artificial intelligence", 
    "data scientist", "data science", "deep learning", "nlp", 
    "computer vision", "pytorch", "tensorflow", "llm", "neural network",
    "reinforcement learning", "model engineer", "data engineer"
]

NEGATIVE_TITLE_KEYWORDS = [
    "sales", "marketing", "digital marketing", "seo", "content", 
    "writer", "graphic designer", "ui/ux", "designer", "hr", 
    "recruiter", "talent acquisition", "frontend", "front-end",
    "business development", "bde", "finance", "accounting", "admin", 
    "customer support", "support engineer", "operations manager"
]

def filter_ml_jobs(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Executes a hybrid filtering system:
    1. Instantly discards listings containing negative keywords.
    2. Instantly approves listings containing clear positive keywords.
    3. Delegates uncertain boundary listings to the Gemini LLM.
    
    Args:
        jobs (List[Dict]): Raw scraped listings.
        
    Returns:
        List[Dict]: Approved list of highly relevant listings.
    """
    if not jobs:
        logger.info("Filter layer received an empty job list.")
        return []

    logger.info(f"Filtering layer starting. Input size: {len(jobs)} jobs")

    approved: List[Dict[str, Any]] = []
    rejected_count = 0
    uncertain: List[Dict[str, Any]] = []

    # Step 1 & 2: Local Deterministic Keywords Filtering
    for job in jobs:
        title = (job.get("title") or "").strip().lower()
        company = (job.get("company") or "").strip().lower()
        skills = (job.get("skills") or "").strip().lower()
        
        # Concat details for comprehensive matching
        full_text = f"{title} {company} {skills}"

        # A. Instant rejection on negative keywords
        if any(neg in title for neg in NEGATIVE_TITLE_KEYWORDS):
            logger.debug(f"Deterministic Drop (Negative Keyword): '{job.get('title')}' at '{job.get('company')}'")
            rejected_count += 1
            continue

        # B. Instant approval on positive title keywords
        if any(pos in title for pos in POSITIVE_TITLE_KEYWORDS):
            logger.debug(f"Deterministic Pass (Positive Keyword): '{job.get('title')}' at '{job.get('company')}'")
            approved.append(job)
            continue

        # C. Everything else goes to the AI boundary filter
        uncertain.append(job)

    logger.info(f"Deterministic phase complete: {len(approved)} approved, {rejected_count} rejected, {len(uncertain)} routed to AI.")

    # Step 3: AI-Assisted Filtering of Uncertain Listings
    ai_approved_count = 0
    ai_rejected_count = 0
    
    for job in uncertain:
        logger.info(f"Routing uncertain listing to AI evaluation: '{job.get('title')}' at '{job.get('company')}'")
        decision = is_relevant_job(job)
        
        if decision is True:
            approved.append(job)
            ai_approved_count += 1
        elif decision is False:
            ai_rejected_count += 1
        else:
            # LLM Failure Fallback: treat as approved to avoid false negatives
            logger.warning(f"AI filter failed for '{job.get('title')}'. Falling back to safe inclusion.")
            approved.append(job)
            ai_approved_count += 1

    logger.info(f"AI filter phase complete: {ai_approved_count} approved, {ai_rejected_count} rejected.")
    
    # Absolute safety fallback: if everything got filtered out, return input list to let user review
    if not approved:
        logger.warning("All listings were filtered out! Returning original scraped list as a safety fallback.")
        return jobs

    logger.info(f"Filtering complete. Final relevant jobs: {len(approved)}/{len(jobs)}")
    return approved