import os
import time
from dotenv import load_dotenv
from google import genai

from agent.parser import extract_json, validate_structure
from tools.job_search import search_jobs

load_dotenv()


class AgentBrain:
    def __init__(self):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

    # ✅ THINK METHOD
    def think(self, user_input: str, retries=5):
        prompt = f"""
You are an AI agent with access to tools.

Available tools:
1. search_jobs(query: str)

Return ONLY valid JSON.

Format:
{{
  "goal": "...",
  "steps": [
    {{
      "action": "search_jobs",
      "input": "..."
    }}
  ]
}}

User Input:
{user_input}
"""

        models = ["gemini-2.5-flash", "gemini-2.0-flash"]

        for attempt in range(retries):
            for model_name in models:
                try:
                    print(f"[TRY] Attempt {attempt+1} using {model_name}")

                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )

                    raw_text = response.text

                    data = extract_json(raw_text)
                    validate_structure(data)

                    return data

                except Exception as e:
                    print(f"[ERROR] {model_name} failed:", e)

            time.sleep(2)

        raise Exception("All retries failed. API overloaded.")

    # ✅ ACT METHOD
    def act(self, plan: dict):
        results = []

        for step in plan["steps"]:
            action = step["action"]
            input_data = step["input"]

            if action == "search_jobs":
                jobs = search_jobs(input_data)
                results.extend(jobs)
            else:
                print(f"[WARNING] Unknown action: {action}")

        return results