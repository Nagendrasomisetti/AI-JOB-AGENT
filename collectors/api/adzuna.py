import os
import logging
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from collectors.base_collector import BaseCollector

logger = logging.getLogger("AIJobAgent.Adzuna")
load_dotenv()

class AdzunaCollector(BaseCollector):
    """
    API Collector implementation for Adzuna.
    Queries the Adzuna jobs REST search API. Incorporates credential safety mock fallbacks.
    """
    def __init__(self):
        super().__init__(name="Adzuna", source_type="API")
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        self.country = os.getenv("ADZUNA_COUNTRY", "in") # Default to 'in' (India) or 'us' / 'gb'

    def collect(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Queries the Adzuna API for the given search term. Falls back to mock data if credentials are not set.
        """
        # If developer credentials are missing, execute the mock fallback automatically
        if not self.app_id or not self.app_key:
            logger.warning("[CREDENTIAL WARNING] ADZUNA_APP_ID or ADZUNA_APP_KEY is not configured in .env.")
            logger.info("Executing safe credential fallback: generating mock Adzuna technology listings...")
            return self._generate_mock_jobs(query, limit)

        logger.info(f"Starting active Adzuna API search for: '{query}' (Country: {self.country})")
        jobs: List[Dict[str, Any]] = []

        # Adzuna Search Endpoint (Page 1)
        api_url = f"https://api.adzuna.com/v1/api/jobs/{self.country}/search/1"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": limit,
            "what": query,
            "content-type": "application/json"
        }

        try:
            response = requests.get(api_url, params=params, timeout=15)
            response.raise_for_status()
            
            payload = response.json()
            results = payload.get("results", [])
            
            logger.info(f"Successfully retrieved {len(results)} jobs from Adzuna API.")

            for item in results:
                title = item.get("title", "N/A").replace("<strong>", "").replace("</strong>", "") # Strip Adzuna bold tags
                
                # Fetch nested dictionary values safely
                company_dict = item.get("company") or {}
                company = company_dict.get("display_name", "N/A")
                
                location_dict = item.get("location") or {}
                location = location_dict.get("display_name", "N/A")
                
                # Format Salary ranges if available
                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                salary_text = "N/A"
                if salary_min and salary_max:
                    salary_text = f"₹ {int(salary_min):,} - {int(salary_max):,} /year"
                elif salary_min:
                    salary_text = f"₹ {int(salary_min):,} /year"

                link = item.get("redirect_url", "")
                
                # Category tags serves as skill representations
                category_dict = item.get("category") or {}
                skills = category_dict.get("label", "Technology")

                standardized_job = {
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": location.strip(),
                    "salary": salary_text,
                    "type": "Full-time" if "contract" not in str(item.get("contract_type")).lower() else "Contract",
                    "experience": "N/A",
                    "skills": skills,
                    "link": link,
                    "source": self.name,
                    "source_type": self.source_type
                }
                
                jobs.append(standardized_job)

        except Exception as e:
            logger.error(f"Adzuna API query failed: {e}")
            logger.info("Falling back to safe mock generator due to query exception...")
            return self._generate_mock_jobs(query, limit)

        return jobs

    def _generate_mock_jobs(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Generates clean mock data to keep the system fully functional without active API credentials.
        """
        mock_templates = [
            {
                "title": "Machine Learning Research Associate",
                "company": "DeepMind Partner Labs",
                "location": "Bangalore / Remote",
                "salary": "₹ 15,00,000 - 22,00,000 /year",
                "skills": "PyTorch, JAX, Deep Learning, Transformer Models",
            },
            {
                "title": "NLP Software Engineer",
                "company": "Cognitive AI Solutions",
                "location": "Hyderabad / Hybrid",
                "salary": "₹ 12,00,000 - 18,00,000 /year",
                "skills": "Python, HuggingFace, LLMs, LangChain, API Ingestion",
            },
            {
                "title": "Data Scientist - Predictive Analytics",
                "company": "Quantum FinTech Systems",
                "location": "Mumbai",
                "salary": "₹ 18,00,000 - 26,00,000 /year",
                "skills": "scikit-learn, SQL, Pandas, Predictive Modeling, git",
            }
        ]

        logger.info(f"Synthesizing mock Adzuna listings for search query '{query}'...")
        jobs: List[Dict[str, Any]] = []
        
        # Multiply mock entries safely to match limit bounds
        for idx in range(limit):
            template = mock_templates[idx % len(mock_templates)]
            jobs.append({
                "title": f"{template['title']} (Mock)",
                "company": template["company"],
                "location": template["location"],
                "salary": template["salary"],
                "type": "Full-time",
                "experience": "1-3 years",
                "skills": template["skills"],
                "link": f"https://mock-adzuna.com/jobs/mock-id-{idx}-{query.replace(' ', '-')}",
                "source": self.name,
                "source_type": self.source_type
            })
            
        return jobs
