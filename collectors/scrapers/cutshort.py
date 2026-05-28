import logging
import time
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from collectors.base_collector import BaseCollector
from collectors.scrapers.base_scraper import BaseScraper

logger = logging.getLogger("AIJobAgent.Cutshort")

class CutshortScraper(BaseCollector, BaseScraper):
    """
    Scraper implementation for Cutshort.io.
    Inherits from both BaseCollector (API structure) and BaseScraper (Selenium configurations).
    """
    def __init__(self, headless: bool = True):
        BaseCollector.__init__(self, name="Cutshort", source_type="Scraper")
        BaseScraper.__init__(self, headless=headless)

    def collect(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Queries Cutshort.io for the given job search keyword and scrapes listings.
        """
        logger.info(f"Starting Cutshort scrape for query: '{query}'")
        
        try:
            self.initialize_driver()
        except Exception as e:
            logger.error(f"Could not start webdriver for Cutshort: {e}")
            return []

        jobs: List[Dict[str, Any]] = []
        seen_links = set()

        try:
            # Cutshort Search URL
            formatted_query = query.replace(" ", "%20")
            search_url = f"https://cutshort.io/jobs?q={formatted_query}"
            
            logger.info(f"Navigating to Cutshort search page: {search_url}")
            self.driver.get(search_url)
            
            # Let the dynamic Single Page App hydrate its state
            time.sleep(6)
            
            logger.info(f"Page loaded: '{self.driver.title}'")

            # Execute scroll loops to load dynamic card frames
            scroll_attempts = 2
            for scroll_idx in range(scroll_attempts):
                logger.info(f"Scrolling Cutshort grid {scroll_idx+1}/{scroll_attempts}...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

            # Responsive CSS selectors targeting custom Webpack-hashed startup cards
            card_selectors = [
                "div[class*='job-card']",
                "div[class*='JobCard']",
                "div.job-card",
                "div.job-card-wrapper",
                "div[class*='card-body']"
            ]

            cards = []
            for selector in card_selectors:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    logger.info(f"Found {len(cards)} listings matching selector: '{selector}'")
                    break

            if not cards:
                # Absolute fallback selection for interactive lists
                cards = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='listing'], div[class*='Job']")
                logger.info(f"Found {len(cards)} broad fallback listings.")

            if not cards:
                logger.warning("Cutshort scraper collected 0 listings. Check if security block or schema changes happened.")
                return []

            for idx, card in enumerate(cards[:limit]):
                try:
                    # 1. Extract Details Link
                    link = "N/A"
                    link_selectors = ["a[href*='/job/']", "a", "a[class*='apply']"]
                    for sel in link_selectors:
                        try:
                            el = card.find_element(By.CSS_SELECTOR, sel)
                            href = el.get_attribute("href") or ""
                            if href and "/job/" in href:
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

                    # 2. Extract Title, Company, Location, and Skills
                    title = self._extract_text(card, [
                        "h3", 
                        "h2", 
                        "div[class*='job-title']", 
                        "span[class*='title']",
                        "h3[class*='title']"
                    ])
                    
                    company = self._extract_text(card, [
                        "div[class*='company-name']", 
                        "span[class*='company']", 
                        "a[class*='company']",
                        "h4"
                    ])
                    
                    location = self._extract_text(card, [
                        "div[class*='location']", 
                        "span[class*='location']", 
                        "div[class*='location-text']",
                        ".location"
                    ])
                    
                    skills = self._extract_text(card, [
                        "div[class*='tag']", 
                        "div[class*='skill']", 
                        "span[class*='skill']",
                        ".tags"
                    ])

                    salary = self._extract_text(card, [
                        "div[class*='compensation']",
                        "span[class*='salary']",
                        ".salary",
                        "div[class*='salary']"
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
                    logger.error(f"Error occurred while processing Cutshort card {idx+1}: {card_error}")
                    continue

        except Exception as e:
            logger.error(f"An unexpected error occurred during Cutshort scraping: {e}")
        finally:
            self.close_driver()

        logger.info(f"Completed Cutshort scraping. Total listings collected: {len(jobs)}")
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
