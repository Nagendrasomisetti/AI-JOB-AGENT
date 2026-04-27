from google import genai
import time
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def is_relevant_job(job):
    try:
        # ✅ STEP 2 — ADD DEBUG HERE (before API call)
        print("[AI CHECK]", job.get("title"))

        prompt = f"""
        You are an AI job filter.

        Decide if this job is relevant for:
        Machine Learning / AI / Data Science roles.

        Job:
        Title: {job.get("title")}
        Company: {job.get("company")}
        Skills: {job.get("skills")}

        Answer ONLY "YES" or "NO".
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        # ✅ STEP 3 — RATE LIMIT HERE (after API call)
        time.sleep(2)

        result = response.text.strip().upper()

        if "YES" in result:
            return True
        return False

    except Exception as e:
        print("[AI FILTER ERROR]", e)
        return None