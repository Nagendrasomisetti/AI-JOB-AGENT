import logging
import requests
from typing import List, Dict, Any
from collectors.base_collector import BaseCollector

logger = logging.getLogger("AIJobAgent.Arbeitnow")

class ArbeitnowCollector(BaseCollector):
    """
    API Collector implementation for Arbeitnow.com.
    Pulls structured JSON job data from the public job board REST API.
    """
    def __init__(self):
        super().__init__(name="Arbeitnow", source_type="API")

    def collect(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Pulls jobs from the Arbeitnow public API, filtering by search keywords.
        """
        logger.info(f"Starting Arbeitnow REST API search for query term: '{query}'")
        jobs: List[Dict[str, Any]] = []
        
        api_url = "https://www.arbeitnow.com/api/job-board-api"
        
        try:
            # Execute HTTP GET request
            response = requests.get(api_url, timeout=15)
            response.raise_for_status()
            
            payload = response.json()
            raw_listings = payload.get("data", [])
            
            logger.info(f"Retrieved {len(raw_listings)} listings from Arbeitnow stream.")
            
            # Simple keyword tracking for filtering the broad stream
            search_keywords = [k.strip().lower() for k in query.split() if len(k.strip()) > 1]
            if "ml" in search_keywords:
                search_keywords.append("machine learning")
            if "ai" in search_keywords:
                search_keywords.append("artificial intelligence")
                
            for raw_job in raw_listings:
                if len(jobs) >= limit:
                    break
                    
                title = raw_job.get("title", "N/A")
                company = raw_job.get("company_name", "N/A")
                location = raw_job.get("location", "N/A")
                tags = raw_job.get("tags", [])
                job_types = raw_job.get("job_types", [])
                url = raw_job.get("url", "")
                
                # Check for query keyword match inside title or tags
                match_text = f"{title} {company} {' '.join(tags)}".lower()
                
                # Filter broad stream by keyword presence
                if search_keywords and not any(kw in match_text for kw in search_keywords):
                    continue

                # Map to the platform's standardized dictionary layout
                standardized_job = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "salary": "N/A",  # Arbeitnow API does not explicitly separate salary digits
                    "type": ", ".join(job_types) if job_types else "Full-time",
                    "experience": "N/A",
                    "skills": ", ".join(tags) if tags else "N/A",
                    "link": url,
                    "source": self.name,
                    "source_type": self.source_type
                }
                
                jobs.append(standardized_job)
                logger.info(f"Matched and standardized: '{title}' at '{company}'")
                
        except Exception as e:
            logger.error(f"Arbeitnow REST API collection encountered an error: {e}")
            
        logger.info(f"Arbeitnow collection complete. Gathered {len(jobs)} matches.")
        return jobs
