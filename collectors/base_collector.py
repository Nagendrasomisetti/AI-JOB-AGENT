from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseCollector(ABC):
    """
    Unified abstract interface for all data collectors (REST APIs and Web Scrapers).
    Ensures that every downstream platform implements standard lifecycle methods and categorization attributes.
    """
    
    def __init__(self, name: str, source_type: str):
        """
        Args:
            name (str): The platform source key (e.g., 'Arbeitnow', 'Internshala').
            source_type (str): Classification layer ('API' or 'Scraper').
        """
        self.name = name
        self.source_type = source_type

    @abstractmethod
    def collect(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Executes raw job data collection for a specific query search term.
        
        Args:
            query (str): Search term / query intent.
            limit (int): Cap on raw job collection to prevent resource exhaustion.
            
        Returns:
            List[Dict]: Standardized raw job entry dicts.
            Standardized fields in returned dicts should include:
            - title (str)
            - company (str)
            - location (str)
            - salary (str)
            - type (str)
            - experience (str)
            - skills (str)
            - link (str, unique URL)
            - source (str, platform name)
            - source_type (str, 'API' or 'Scraper')
        """
        pass
