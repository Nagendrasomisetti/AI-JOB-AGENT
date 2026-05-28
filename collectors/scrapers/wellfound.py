import logging
import time
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from collectors.base_collector import BaseCollector
from collectors.scrapers.base_scraper import BaseScraper

logger = logging.getLogger("AIJobAgent.Wellfound")

class WellfoundScraper(BaseCollector, BaseScraper):
    """
    Scraper implementation for Wellfound.com (formerly AngelList).
    Inherits from both BaseCollector (API structure) and BaseScraper (Selenium configurations).
    """
    def __init__(self, headless: bool = True):
        BaseCollector.__init__(self, name="Wellfound", source_type="Scraper")
        BaseScraper.__init__(self, headless=headless)

    def collect(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Queries Wellfound for the given job search keyword and scrapes listings.
        """
        logger.info(f"Starting Wellfound scrape for query: '{query}'")
        
        try:
            self.initialize_driver()
        except Exception as e:
            logger.error(f"Could not start webdriver for Wellfound: {e}")
            return []

        jobs: List[Dict[str, Any]] = []
        seen_links = set()

        try:
            # Wellfound job query URL
            formatted_query = query.replace(" ", "+")
            search_url = f"https://wellfound.com/jobs?q={formatted_query}"
            
            logger.info(f"Navigating to Wellfound search page: {search_url}")
            self.driver.get(search_url)
            
            # Let the initial page state settle
            time.sleep(6)

            # Check if we got caught by Cloudflare protection
            page_source = self.driver.page_source.lower()
            if "cloudflare" in page_source or "just a moment" in page_source or "enable javascript" in page_source:
                logger.error("[CLOUDFLARE BLOCK] Wellfound scrape blocked by security gate. Evasion required.")
                logger.warning("Please consider running with headless=False or configure proxy settings to bypass.")
                return []

            logger.info(f"Page loaded: '{self.driver.title}'")

            # Perform dynamic scrolls to load virtualized elements
            scroll_attempts = 3
            for scroll_idx in range(scroll_attempts):
                logger.info(f"Executing dynamic scroll check {scroll_idx+1}/{scroll_attempts}...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

            # Known CSS selectors for Wellfound listing blocks
            card_selectors = [
                "div.job-listing",
                "div.styles_result__",
                "div.styles_component__",
                "div[data-testid='JobListing']",
                ".styles_jobListing__"
            ]

            cards = []
            for selector in card_selectors:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    logger.info(f"Found {len(cards)} listings matching selector: '{selector}'")
                    break
            
            # If standard selectors fail, try finding any interactive listing wrappers
            if not cards:
                logger.warning("No listings found matching specific Wellfound patterns. Attempting broad selection...")
                cards = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='job-listing'], div[class*='listing']")
                logger.info(f"Found {len(cards)} fallback listings.")

            if not cards:
                logger.warning("Wellfound scraper collected 0 listings. Check if security block or selector changes happened.")
                return []

            for idx, card in enumerate(cards[:limit]):
                try:
                    # 1. Extract Details link
                    link = "N/A"
                    link_selectors = ["a", "a[href*='/jobs/']", "a[class*='apply']"]
                    for sel in link_selectors:
                        try:
                            el = card.find_element(By.CSS_SELECTOR, sel)
                            href = el.get_attribute("href") or ""
                            if href and "/jobs" in href:
                                link = href
                                break
                        except:
                            continue

                    if link == "N/A":
                        try:
                            link = card.find_element(By.TAG_NAME, "a").get_attribute("href") or "N/A"
                        except:
                            pass

                    if link == "N/A" or not link:
                        logger.debug("Skipping listing card: No valid URL link found.")
                        continue

                    if link in seen_links:
                        continue
                    seen_links.add(link)

                    # 2. Extract Title, Company, Location, and Skills with selector safety fallbacks
                    title = self._extract_text(card, [
                        "h2", 
                        "h4", 
                        "div[class*='job-title']", 
                        ".styles_title__",
                        "h3[class*='title']"
                    ])
                    
                    company = self._extract_text(card, [
                        "h3", 
                        "span[class*='company']", 
                        ".styles_companyName__",
                        "h2[class*='company']"
                    ])
                    
                    location = self._extract_text(card, [
                        ".location", 
                        "span[class*='location']", 
                        ".styles_location__",
                        "div[class*='location']"
                    ])
                    
                    skills = self._extract_text(card, [
                        ".skills", 
                        ".tags", 
                        "div[class*='tag']", 
                        "div[class*='skill']"
                    ])

                    salary = self._extract_text(card, [
                        ".salary",
                        "span[class*='salary']",
                        ".styles_compensation__",
                        "div[class*='compensation']"
                    ])

                    job_entry = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": salary,
                        "type": "Full-time",
                        "experience": "N/A",
                        "skills": skills,
                        "link": link,
                        "source": self.name,
                        "source_type": self.source_type
                    }

                    jobs.append(job_entry)
                    logger.info(f"Successfully scraped: '{title}' at '{company}'")

                except Exception as card_error:
                    logger.error(f"Error occurred while processing Wellfound card {idx+1}: {card_error}")
                    continue

        except Exception as e:
            logger.error(f"An unexpected error occurred during Wellfound scraping: {e}")
        finally:
            self.close_driver()

        logger.info(f"Completed Wellfound scraping. Total listings collected: {len(jobs)}")
        return jobs

    def _extract_text(self, parent_element, selectors: List[str]) -> str:
        """
        Extracts clean text using selector lists. Returns 'N/A' if none match.
        """
        for selector in selectors:
            try:
                el = parent_element.find_element(By.CSS_SELECTOR, selector)
                text = self.get_element_text_with_fallbacks(el)
                if text and text != "N/A":
                    return text
            except:
                continue
        return "N/A"
