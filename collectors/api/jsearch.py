import os
import logging
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from collectors.base_collector import BaseCollector

logger = logging.getLogger("AIJobAgent.JSearch")
load_dotenv()

class JSearchCollector(BaseCollector):
    """
    API Collector implementation for JSearch.
    Queries the JSearch RapidAPI endpoint to pull aggregated listings across major boards.
    Includes credential safety mock fallbacks.
    """
    def __init__(self):
        super().__init__(name="JSearch", source_type="API")
        self.api_key = os.getenv("JSEARCH_API_KEY")
        self.host = "jsearch.p.rapidapi.com"

    def collect(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Queries the JSearch RapidAPI endpoint for the given search term.
        Falls back to mock data if credentials are not configured.
        """
        # If RapidAPI key is missing, trigger mock fallback
        if not self.api_key:
            logger.warning("[CREDENTIAL WARNING] JSEARCH_API_KEY is not configured in .env.")
            logger.info("Executing safe credential fallback: generating mock JSearch technology listings...")
            return self._generate_mock_jobs(query, limit)

        logger.info(f"Starting active JSearch RapidAPI search for: '{query}'")
        jobs: List[Dict[str, Any]] = []
        
        api_url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.host
        }
        params = {
            "query": query,
            "page": "1",
            "num_pages": "1"
        }

        try:
            response = requests.get(api_url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            payload = response.json()
            results = payload.get("data", [])
            
            logger.info(f"Successfully retrieved {len(results)} jobs from JSearch API.")

            for item in results[:limit]:
                title = item.get("job_title", "N/A")
                company = item.get("employer_name", "N/A")
                
                # Compose location string safely
                city = item.get("job_city")
                country = item.get("job_country")
                location = "N/A"
                if city and country:
                    location = f"{city}, {country}"
                elif country:
                    location = country
                elif city:
                    location = city

                # Parse salary details
                salary_min = item.get("job_min_salary")
                salary_max = item.get("job_max_salary")
                currency = item.get("job_salary_currency", "$")
                salary_text = "N/A"
                if salary_min and salary_max:
                    salary_text = f"{currency} {int(salary_min):,} - {int(salary_max):,} /year"
                elif salary_min:
                    salary_text = f"{currency} {int(salary_min):,} /year"

                link = item.get("job_apply_link", "")
                
                # Fetch skills list if available
                required_skills = item.get("job_required_skills")
                skills = "N/A"
                if required_skills and isinstance(required_skills, list):
                    skills = ", ".join(required_skills)

                standardized_job = {
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": location.strip(),
                    "salary": salary_text,
                    "type": item.get("job_employment_type", "Full-time").replace("_", " ").title(),
                    "experience": "N/A",
                    "skills": skills,
                    "link": link,
                    "source": self.name,
                    "source_type": self.source_type
                }
                
                jobs.append(standardized_job)

        except Exception as e:
            logger.error(f"JSearch API query failed: {e}")
            logger.info("Falling back to safe mock generator due to query exception...")
            return self._generate_mock_jobs(query, limit)

        return jobs

    def _generate_mock_jobs(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Generates clean mock data to keep the system fully functional without active API credentials.
        """
        mock_templates = [
            {
                "title": "MLOps Engineer (Hiring globally)",
                "company": "Scalable AI Platforms",
                "location": "San Francisco, US / Remote",
                "salary": "$ 110,000 - 150,000 /year",
                "skills": "MLOps, Docker, Kubernetes, AWS, PyTorch, git",
            },
            {
                "title": "LLM Solutions Architect",
                "company": "Apex Neural Labs",
                "location": "London, UK / Hybrid",
                "salary": "$ 130,000 - 170,000 /year",
                "skills": "Transformers, OpenAI, LangChain, Vector Databases, Python",
            },
            {
                "title": "Senior AI Infrastructure Engineer",
                "company": "HyperScale Cloud Systems",
                "location": "Remote, US",
                "salary": "$ 140,000 - 190,000 /year",
                "skills": "Linux, MLOps, CUDA, TensorFlow, PyTorch, Spark",
            }
        ]

        logger.info(f"Synthesizing mock JSearch listings for search query '{query}'...")
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
                "experience": "3+ years",
                "skills": template["skills"],
                "link": f"https://mock-jsearch.com/jobs/mock-id-{idx}-{query.replace(' ', '-')}",
                "source": self.name,
                "source_type": self.source_type
            })
            
        return jobs
