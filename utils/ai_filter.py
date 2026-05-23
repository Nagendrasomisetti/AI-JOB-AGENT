import os
import time
import logging
from dotenv import load_dotenv

# Try importing the GenAI SDK, fallback safely if missing
try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger("AIJobAgent.AIFilter")
load_dotenv()

# Initialize Client safely
client = None
api_key = os.getenv("GEMINI_API_KEY")

if genai is None:
    logger.warning("Google GenAI SDK is not installed. AI Job Filter will fallback to permissive inclusion.")
elif not api_key:
    logger.warning("GEMINI_API_KEY environment variable is missing. AI Job Filter will fallback to permissive inclusion.")
else:
    try:
        client = genai.Client(api_key=api_key)
        logger.info("GenAI client initialized successfully for AI Filtering.")
    except Exception as e:
        logger.error(f"Failed to instantiate GenAI Client: {e}")
        client = None


def is_relevant_job(job: dict) -> bool:
    """
    Asks the Gemini model to perform a binary relevance assessment on a job listing.
    
    Args:
        job (dict): Job dictionary containing title, company, and skills.
        
    Returns:
        bool: True if relevant, False if irrelevant, None if LLM call fails.
    """
    if client is None:
        logger.debug("GenAI client not initialized; skipping AI evaluation.")
        return None

    title = job.get("title", "N/A")
    company = job.get("company", "N/A")
    skills = job.get("skills", "N/A")

    prompt = f"""
    You are an expert AI Job Recruiter. 
    Decide if the following job listing is relevant for a career in:
    Machine Learning, Artificial Intelligence, Data Science, or MLOps roles.

    Job Information:
    - Title: {title}
    - Company: {company}
    - Required Skills: {skills}

    Evaluate:
    - Does this job target building, training, analyzing, or deploying models, data pipelines, or AI integrations?
    - Answer ONLY "YES" or "NO". Do not include any punctuation, conversational filler, or explanations.
    """

    try:
        logger.info(f"[AI Evaluate] Checking relevance for: '{title}' at '{company}'")
        
        # Call gemini-2.5-flash for rapid, cost-effective inference
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        # Standard API rate limit delay to avoid spamming the developer key
        time.sleep(1.5)

        raw_result = response.text or ""
        result = raw_result.strip().upper()

        logger.debug(f"[AI Evaluate] Model response for '{title}': '{result}'")

        if "YES" in result:
            return True
        elif "NO" in result:
            return False
        else:
            logger.warning(f"Unexpected response format from model: '{raw_result}'. Defaulting to None.")
            return None

    except Exception as e:
        logger.error(f"Gemini API invocation failed during relevance evaluation: {e}")
        return None