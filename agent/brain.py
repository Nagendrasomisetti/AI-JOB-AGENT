import os
import time
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Try importing the GenAI SDK, fallback safely if missing
try:
    from google import genai
except ImportError:
    genai = None

from agent.parser import extract_json, validate_structure
from tools.internshala import InternshalaScraper
from tools.wellfound import WellfoundScraper

logger = logging.getLogger("AIJobAgent.Brain")
load_dotenv()

class AgentBrain:
    """
    The orchestrating brain of the AI Job Agent.
    Responsible for interpreting natural language intent into structured tool execution plans
    and executing those plans safely with fallbacks.
    """
    def __init__(self):
        self.client = None
        api_key = os.getenv("GEMINI_API_KEY")
        
        if genai is None:
            logger.warning("Google GenAI SDK is unavailable. Running in rule-based fallback mode.")
        elif not api_key:
            logger.warning("GEMINI_API_KEY environment variable is not configured. Running in rule-based fallback mode.")
        else:
            try:
                self.client = genai.Client(api_key=api_key)
                logger.info("GenAI client initialized successfully for Agent Planning.")
            except Exception as e:
                logger.error(f"Failed to initialize GenAI client: {e}")
                self.client = None

    def think(self, user_input: str, retries: int = 3) -> Dict[str, Any]:
        """
        Interprets user search intent into a structured execution plan.
        Falls back to a default deterministic plan if Gemini is offline.
        """
        # If API keys are missing, jump straight to the deterministic rule-based plan
        if self.client is None:
            logger.info("API Client offline. Generating safe deterministic default plan...")
            return self._generate_default_plan(user_input)

        prompt = f"""
        You are an advanced AI planning agent designed to aggregate jobs from multiple sources.
        Your goal is to parse the user's request and map it to tool invocations.

        Available scrapers (tools):
        1. search_internshala: Best for internships and entry-level positions in India/Remote. (Takes 'query' string input).
        2. search_wellfound: Best for startup jobs, remote work, and international/domestic positions. (Takes 'query' string input).

        Generate a structured plan containing:
        - goal: What the user is trying to accomplish.
        - steps: A JSON list of tools to invoke. Each step must contain 'action' (the tool name) and 'input' (the search query).

        Return ONLY a raw valid JSON object. Do not include markdown codeblocks or explanations.
        
        Example JSON output:
        {{
          "goal": "Retrieve Machine Learning internships",
          "steps": [
            {{
              "action": "search_internshala",
              "input": "machine learning"
            }},
            {{
              "action": "search_wellfound",
              "input": "machine learning"
            }}
          ]
        }}

        User Request:
        "{user_input}"
        """

        # Try a cascading list of model targets to avoid temporary rate limits
        model_tiers = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

        for attempt in range(retries):
            for model_name in model_tiers:
                try:
                    logger.info(f"Generating search plan (Attempt {attempt+1}/{retries} using {model_name})...")
                    
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )

                    raw_text = response.text or ""
                    logger.debug(f"Raw planner response: {raw_text}")

                    # Extractor & Schema Validator check
                    plan_data = extract_json(raw_text)
                    validate_structure(plan_data)

                    logger.info(f"Orchestrated plan successfully generated: '{plan_data['goal']}'")
                    return plan_data

                except Exception as e:
                    logger.warning(f"Plan generation failed on '{model_name}': {e}")
                    continue
            
            # Simple cooling sleep between cycles
            time.sleep(2)

        logger.error("All AI planning tiers failed or timed out. Falling back to default plan.")
        return self._generate_default_plan(user_input)

    def _generate_default_plan(self, user_input: str) -> Dict[str, Any]:
        """
        Creates a default fallback plan that targets both scraper platforms using derived terms.
        """
        # Deduce a simplified query term from user input
        cleaned = user_input.lower()
        query = "machine learning"
        
        if "data" in cleaned:
            query = "data science"
        elif "ai" in cleaned:
            query = "artificial intelligence"
        elif "python" in cleaned:
            query = "python developer"

        logger.info(f"Created fallback plan: Scrape both platforms using query term '{query}'")
        return {
            "goal": f"Fallback manual query: Search ML/AI jobs for '{query}'",
            "steps": [
                {"action": "search_internshala", "input": query},
                {"action": "search_wellfound", "input": query}
            ]
        }

    def act(self, plan: Dict[str, Any], max_jobs_per_source: int = 10) -> List[Dict[str, Any]]:
        """
        Executes the generated execution steps, instantiating scrapers, and aggregates results.
        """
        all_results: List[Dict[str, Any]] = []
        steps = plan.get("steps", [])

        logger.info(f"Executing {len(steps)} plan step(s)...")

        for idx, step in enumerate(steps):
            action = step.get("action")
            query_input = step.get("input")

            logger.info(f"Step {idx+1}/{len(steps)}: Running '{action}' with input: '{query_input}'")

            try:
                if action == "search_internshala":
                    scraper = InternshalaScraper(headless=True)
                    jobs = scraper.scrape_internships(query=query_input, max_results=max_jobs_per_source)
                    all_results.extend(jobs)
                    
                elif action == "search_wellfound":
                    scraper = WellfoundScraper(headless=True)
                    jobs = scraper.scrape_jobs(query=query_input, max_results=max_jobs_per_source)
                    all_results.extend(jobs)
                    
                else:
                    logger.warning(f"Skipping execution: Unknown scraper action key '{action}'")

            except Exception as e:
                logger.error(f"Execution failure on step '{action}': {e}")
                continue

        logger.info(f"Agent execution completed. Total raw listings aggregated: {len(all_results)}")
        return all_results