import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from tools.base_scraper import BaseScraper

logger = logging.getLogger("AIJobAgent.Internshala")

class InternshalaScraper(BaseScraper):
    """
    Scraper implementation for Internshala.com.
    Crawls job listings, extracts summary info, and visits deep detail links for full data extraction.
    """
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)

    def scrape_internships(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Queries Internshala for the given job search keyword and scrapes detailed job listings.
        """
        logger.info(f"Starting Internshala scrape for query: '{query}'")
        
        try:
            self.initialize_driver()
        except Exception as e:
            logger.error(f"Could not start webdriver for Internshala: {e}")
            return []

        jobs: List[Dict[str, Any]] = []
        seen_links = set()

        try:
            # Construct URL - replacing spaces with url encoding
            formatted_query = query.replace(" ", "%20")
            search_url = f"https://internshala.com/internships/keywords-{formatted_query}"
            
            logger.info(f"Navigating to search page: {search_url}")
            self.driver.get(search_url)
            
            # Allow dynamic JavaScript grid to load
            time.sleep(5)
            
            logger.info(f"Page loaded: '{self.driver.title}'")

            # Try a couple of known selectors for listing cards
            card_selectors = [
                "div.container-fluid.individual_internship.view_detail_button",
                "div.individual_internship"
            ]
            
            cards = []
            for selector in card_selectors:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    logger.info(f"Found {len(cards)} listings matching card selector '{selector}'")
                    break
            
            if not cards:
                logger.warning("No job cards found on the page. Website layout may have changed.")
                return []

            # Limit card processing to prevent long delays
            for idx, card in enumerate(cards[:max_results]):
                try:
                    logger.info(f"Scraping job card {idx+1}/{min(len(cards), max_results)}")
                    
                    # 1. Extract application detail link
                    link = card.get_attribute("data-href") or ""
                    if link and link.startswith("/"):
                        link = urljoin("https://internshala.com", link)
                    
                    if not link or "internship/detail" not in link:
                        # Fallback: check if there's a link tag inside the header
                        try:
                            link_el = card.find_element(By.CSS_SELECTOR, "h3.heading_4_5 a, h2.job-internship-name a")
                            link = link_el.get_attribute("href") or ""
                        except:
                            pass

                    if not link:
                        logger.debug("Skipping listing card: No valid URL found.")
                        continue

                    if link in seen_links:
                        logger.debug(f"Skipping duplicate listing URL: {link}")
                        continue
                    
                    seen_links.add(link)

                    # 2. Extract summary properties with element selector fallbacks
                    title = self._extract_field(card, [
                        "h3.heading_4_5 a", 
                        "h2.job-internship-name a.job-title-href", 
                        "div.profile a"
                    ])
                    
                    company = self._extract_field(card, [
                        "p.company-name", 
                        "div.company_name a", 
                        "a.company_and_premium"
                    ])
                    
                    location = self._extract_field(card, [
                        "div.row-1-item.locations", 
                        "p.locations span", 
                        "a.location_link"
                    ])

                    # Create default entry skeleton
                    job_entry = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": "N/A",
                        "type": "Internship",
                        "experience": "N/A",
                        "skills": "N/A",
                        "link": link,
                        "source": "Internshala"
                    }

                    # 3. Open detailed page in new tab for deep field extraction
                    logger.info(f"Opening deep listing link in secondary tab: {link}")
                    original_window = self.driver.current_window_handle
                    
                    self.driver.execute_script("window.open(arguments[0]);", link)
                    
                    # Wait for secondary handle to open and switch
                    time.sleep(1) 
                    all_windows = self.driver.window_handles
                    self.driver.switch_to.window(all_windows[-1])
                    
                    try:
                        # Scrape deep details
                        details = self._scrape_detailed_page()
                        job_entry.update(details)
                    finally:
                        # CRITICAL: Always close child tab and switch back to prevent leaking memory
                        self.driver.close()
                        self.driver.switch_to.window(original_window)

                    jobs.append(job_entry)
                    logger.info(f"Successfully scraped: '{title}' at '{company}'")
                    
                except Exception as card_error:
                    logger.error(f"Error occurred while processing card {idx+1}: {card_error}")
                    continue

        except Exception as e:
            logger.error(f"An unexpected error occurred during Internshala crawling: {e}")
        finally:
            self.close_driver()
            
        logger.info(f"Completed Internshala scraping. Total listings collected: {len(jobs)}")
        return jobs

    def _extract_field(self, parent_element, selectors: List[str]) -> str:
        """
        Checks a sequence of selectors and returns the cleaned text of the first one found.
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

    def _scrape_detailed_page(self) -> Dict[str, str]:
        """
        Extracts deep fields (skills, salary, experience) from a single active listing page.
        """
        # Ensure page body has rendered before proceeding
        self.wait_for_element(By.TAG_NAME, "body", timeout=10)

        # 1. Scrape Required Skills
        skills = "N/A"
        skills_selectors = [
            ".round_tabs", 
            ".skills_list span", 
            ".internship_other_details li", 
            "div.skills_heading + div.round_tabs_container span"
        ]
        for selector in skills_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                extracted_skills = [e.text.strip() for e in elements if e.text.strip()]
                if extracted_skills:
                    skills = ", ".join(extracted_skills)
                    break
            except:
                continue

        # 2. Scrape Salary/Stipend
        salary = "N/A"
        salary_selectors = [
            ".stipend", 
            ".internship_detail_item .stipend", 
            ".stipend_container", 
            "span.stipend"
        ]
        for selector in salary_selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, selector)
                salary_text = self.get_element_text_with_fallbacks(el)
                if salary_text and salary_text != "N/A":
                    salary = salary_text
                    break
            except:
                continue

        # 3. Scrape Experience Requirements
        experience = "N/A"
        experience_selectors = [
            ".experience_container",
            ".other_detail_item_row .other_detail_item:nth-child(2)",
            ".internship_detail_item",
            ".internship_other_details li"
        ]
        for selector in experience_selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, selector)
                exp_text = self.get_element_text_with_fallbacks(el)
                if exp_text and exp_text != "N/A" and "years" in exp_text.lower():
                    experience = exp_text
                    break
            except:
                continue

        return {
            "skills": skills,
            "salary": salary,
            "experience": experience
        }
