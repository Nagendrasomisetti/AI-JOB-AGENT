# DEPRECATED: This file has been replaced by tools/internshala.py in the production refactoring.
# Please import InternshalaScraper from tools.internshala instead.

import warnings
from tools.internshala import InternshalaScraper

warnings.warn(
    "tools/job_search.py is deprecated and replaced by tools/internshala.py. Please update imports.",
    DeprecationWarning,
    stacklevel=2
)

def search_jobs(query: str):
    """
    Deprecated legacy wrapper. Redirects to InternshalaScraper.
    """
    scraper = InternshalaScraper(headless=True)
    return scraper.scrape_internships(query, max_results=10)
