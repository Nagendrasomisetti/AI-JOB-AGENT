# DEPRECATED: This file has been replaced by tools/wellfound.py in the production refactoring.
# Please import WellfoundScraper from tools.wellfound instead.

import warnings
from tools.wellfound import WellfoundScraper

warnings.warn(
    "tools/wellfound_search.py is deprecated and replaced by tools/wellfound.py. Please update imports.",
    DeprecationWarning,
    stacklevel=2
)

def search_wellfound_jobs(query: str):
    """
    Deprecated legacy wrapper. Redirects to WellfoundScraper.
    """
    scraper = WellfoundScraper(headless=True)
    return scraper.scrape_jobs(query, max_results=10)