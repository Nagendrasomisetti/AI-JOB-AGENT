import re
import logging

logger = logging.getLogger("AIJobAgent.Scorer")

# Advanced Skill Weights Matrix
CORE_AI_SKILLS = {
    # Tier 1: Frameworks & Deep Learning (Highest Weight)
    "pytorch": 15, "tensorflow": 15, "keras": 10, "jax": 15,
    "transformers": 15, "huggingface": 12, "hugging face": 12,
    
    # Tier 2: Core Subfields
    "machine learning": 12, "ml": 10, "deep learning": 12, "dl": 10,
    "nlp": 15, "natural language processing": 15, "llm": 18, "generative ai": 15,
    "computer vision": 12, "cv": 10, "image processing": 10, "reinforcement learning": 12,
    
    # Tier 3: Supporting Tech & Engineering (Medium Weight)
    "python": 10, "scikit-learn": 10, "pandas": 8, "numpy": 8, "sql": 8,
    "docker": 10, "kubernetes": 10, "aws": 10, "gcp": 10, "mlops": 15,
    "git": 5, "linux": 5, "spark": 8, "hadoop": 5
}

def score_job(job: dict) -> float:
    """
    Calculates a dynamic suitability score for a job listing based on:
    - Job Title alignment (ML/AI engineer vs general analyst)
    - Technical skills keyword density & weights
    - Location preference (Remote/WFH bonuses)
    - Salary/Stipend valuation (extracted via robust regex)
    
    Args:
        job (dict): Clean job listing from the database/scraper.
        
    Returns:
        float: Computed suitability score.
    """
    score = 0.0

    title = (job.get("title") or "").strip().lower()
    skills = (job.get("skills") or "").strip().lower()
    salary = (job.get("salary") or "").strip()
    location = (job.get("location") or "").strip().lower()
    experience = (job.get("experience") or "").strip().lower()

    # ----------------------------------------------------
    # 1. Job Title Relevance Scoring (Max 40 points)
    # ----------------------------------------------------
    if "lead" in title or "senior" in title or "sr" in title:
        # Give a small seniority adjustment, but keep weights high for ML/AI
        if "machine learning" in title or "ml" in title:
            score += 40.0
        elif "ai" in title or "artificial intelligence" in title:
            score += 35.0
        elif "data scientist" in title:
            score += 35.0
        elif "data engineer" in title:
            score += 20.0
    else:
        # Standard levels / Internships
        if "machine learning" in title or "ml" in title:
            score += 35.0
        elif "ai" in title or "artificial intelligence" in title:
            score += 30.0
        elif "data scientist" in title:
            score += 30.0
        elif "data engineer" in title:
            score += 20.0
        elif "research" in title:
            score += 25.0
        elif "python" in title:
            score += 15.0
        elif "analyst" in title or "data analyst" in title:
            score += 10.0
        else:
            score += 5.0

    # ----------------------------------------------------
    # 2. Technical Skills Matching (Dynamic Weights)
    # ----------------------------------------------------
    matched_skills_score = 0.0
    for skill_name, weight in CORE_AI_SKILLS.items():
        # Match using word boundaries or simple occurrences
        if skill_name in skills or skill_name in title:
            matched_skills_score += weight
            
    # Cap skill contributions to prevent keyword-stuffing listings from breaking scores
    score += min(matched_skills_score, 50.0)

    # ----------------------------------------------------
    # 3. Location / Remote Preference (Max 15 points)
    # ----------------------------------------------------
    if "remote" in location or "work from home" in location or "wfh" in location:
        score += 15.0
    elif "hybrid" in location:
        score += 5.0

    # ----------------------------------------------------
    # 4. Salary / Stipend Regex Extraction & Scoring (Max 20 points)
    # ----------------------------------------------------
    salary_bonus = 0.0
    if salary and salary.upper() != "N/A" and "competitive" not in salary.lower():
        try:
            # Clean string commas and whitespace
            cleaned_salary = salary.replace(",", "").replace(" ", "")
            
            # Find all numbers in the salary string
            numbers = [int(n) for n in re.findall(r"\d+", cleaned_salary)]
            
            if numbers:
                # If a range is given, use the upper limit; otherwise the sole number
                max_value = max(numbers)
                
                # Check currency context
                if "₹" in salary or "rs" in salary.lower() or "inr" in salary.lower():
                    # Check if monthly stipend (lower values) or annual salary (higher values)
                    if "month" in salary.lower() or max_value < 100000:
                        # Monthly Stipend Scoring
                        if max_value >= 25000:
                            salary_bonus = 20.0
                        elif max_value >= 15000:
                            salary_bonus = 12.0
                        elif max_value >= 10000:
                            salary_bonus = 7.0
                    else:
                        # Annual INR Salary (Lakhs or raw numbers)
                        # e.g. "800000" (8 LPA) or "8 Lakhs"
                        if max_value >= 1500000 or (max_value < 100 and max_value >= 15):
                            salary_bonus = 20.0
                        elif max_value >= 800000 or (max_value < 100 and max_value >= 8):
                            salary_bonus = 15.0
                        elif max_value >= 500000 or (max_value < 100 and max_value >= 5):
                            salary_bonus = 10.0
                
                elif "$" in salary or "usd" in salary.lower():
                    # USD Annual Salary or hourly rates
                    if "hour" in salary.lower():
                        if max_value >= 50:
                            salary_bonus = 20.0
                        elif max_value >= 30:
                            salary_bonus = 12.0
                    else:
                        # Annual USD (e.g. 100k or 100000)
                        if max_value >= 120000 or (max_value < 1000 and max_value >= 120):
                            salary_bonus = 20.0
                        elif max_value >= 80000 or (max_value < 1000 and max_value >= 80):
                            salary_bonus = 15.0
                        elif max_value >= 50000 or (max_value < 1000 and max_value >= 50):
                            salary_bonus = 10.0
                            
        except Exception as e:
            logger.warning(f"Error parsing stipend/salary text '{salary}': {e}")
            
    score += salary_bonus

    # ----------------------------------------------------
    # 5. Experience Alignment (Max 10 points)
    # ----------------------------------------------------
    # Reward entry-level, junior, or specific training positions
    if "0-1" in experience or "1-3" in experience or "entry" in experience or "junior" in experience or "intern" in experience:
        score += 10.0
    elif "fresh" in experience or "no experience" in experience:
        score += 10.0

    return round(score, 1)