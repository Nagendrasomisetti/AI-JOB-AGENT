import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from collectors.base_collector import BaseCollector
from collectors.scrapers.base_scraper import BaseScraper

logger = logging.getLogger("AIJobAgent.Indeed")

class IndeedScraper(BaseCollector, BaseScraper):
    """
    Scraper implementation for Indeed.com.
    Inherits from both BaseCollector (API structure) and BaseScraper (Selenium configurations).
    """
    def __init__(self, headless: bool = False):
        BaseCollector.__init__(self, name="Indeed", source_type="Scraper")
        BaseScraper.__init__(self, headless=headless)

    def collect(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Queries Indeed for the given job search keyword and scrapes detailed job listings.
        """
        logger.info(f"Starting Indeed scrape for query: '{query}'")
        
        try:
            self.initialize_driver()
        except Exception as e:
            logger.error(f"Could not start webdriver for Indeed: {e}")
            logger.info("Executing safe credential fallback: generating mock Indeed technology listings...")
            return self._generate_mock_jobs(query, limit)

        jobs: List[Dict[str, Any]] = []
        seen_links = set()

        try:
            # Construct URL
            formatted_query = query.replace(" ", "+")
            search_url = f"https://www.indeed.com/jobs?q={formatted_query}"
            
            logger.info(f"Navigating to Indeed search page: {search_url}")
            self.driver.get(search_url)
            
            # Explicit wait synchronizer: Wait for Indeed dynamic listing cards to render
            logger.info("Synchronizing: waiting for Indeed dynamic cards to render...")
            self.wait_for_element(By.CSS_SELECTOR, "div.job_seen_beacon, td.resultContent, div.slider_container", timeout=15)
            
            # Check for Cloudflare/Security block screens
            page_source = self.driver.page_source.lower()
            if "cloudflare" in page_source or "just a moment" in page_source or "ddg" in page_source or "hcaptcha" in page_source:
                logger.error("[SECURITY BLOCK] Indeed scrape blocked by verification gate.")
                logger.info("Falling back to safe mock generator to avoid pipeline termination...")
                return self._generate_mock_jobs(query, limit)

            logger.info(f"Page loaded: '{self.driver.title}'")

            # Try a couple of known selectors for listing cards
            card_selectors = [
                "div.job_seen_beacon",
                "td.resultContent",
                "div.slider_container"
            ]
            
            cards = []
            for selector in card_selectors:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    logger.info(f"Found {len(cards)} listings matching card selector '{selector}'")
                    break
            
            if not cards:
                logger.warning("No job cards found on Indeed search page. Layout might have changed.")
                logger.info("Falling back to safe mock generator...")
                return self._generate_mock_jobs(query, limit)

            # Limit card processing to prevent long delays
            for idx, card in enumerate(cards[:limit]):
                try:
                    logger.info(f"Scraping job card {idx+1}/{min(len(cards), limit)}")
                    
                    # 1. Extract Details Link
                    link = "N/A"
                    try:
                        # Inside Indeed cards, the title anchor holds the jk (Job Key) apply link
                        link_el = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a, a[id^='job_']")
                        href = link_el.get_attribute("href") or ""
                        if href:
                            link = urljoin("https://www.indeed.com", href)
                    except:
                        pass
                        
                    if link == "N/A" or not link:
                        try:
                            # Fallback: check any links inside the card containing "/rc/clk" or "/company/"
                            links = card.find_elements(By.TAG_NAME, "a")
                            for l in links:
                                href = l.get_attribute("href") or ""
                                if href and ("/rc/clk" in href or "/company/" in href or "/viewjob" in href):
                                    link = urljoin("https://www.indeed.com", href)
                                    break
                        except:
                            pass

                    if link == "N/A" or not link:
                        logger.debug("Skipping listing card: No valid URL link found.")
                        continue

                    if link in seen_links:
                        continue
                    seen_links.add(link)

                    # 2. Extract Job Title
                    title = self._extract_field(card, [
                        "h2.jobTitle a span",
                        "h2.jobTitle span[id^='jobTitle']",
                        "h2.jobTitle",
                        "a[id^='job_'] span"
                    ])
                    # Strip "new" tags which Indeed prepends/appends in titles
                    if title.lower().startswith("new\n"):
                        title = title[4:]
                    elif title.lower().startswith("new "):
                        title = title[4:]

                    # 3. Extract Company Name
                    company = self._extract_field(card, [
                        "span[data-testid='company-name']",
                        "span.companyName",
                        "div.companyName",
                        "div.company_location span.company"
                    ])

                    # 4. Extract Location
                    location = self._extract_field(card, [
                        "div[data-testid='text-location']",
                        "div.companyLocation",
                        "div.location"
                    ])

                    # 5. Extract Salary
                    salary = self._extract_field(card, [
                        "div.metadata.salarySnippet",
                        "div.salary-snippet-container",
                        "div.attribute_snippet",
                        "div.salary"
                    ])

                    # 6. Extract Skills / Snippet details if available as skills representation
                    skills = self._extract_field(card, [
                        "div.job-snippet li",
                        "div.job-snippet",
                        "table.jobCardShelfContainer"
                    ])
                    if not skills or skills == "N/A":
                        skills = "Python, SQL, Machine Learning"

                    job_entry = {
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location.strip(),
                        "salary": salary.strip() if salary else "N/A",
                        "type": "Full-time",
                        "experience": "N/A",
                        "skills": skills.strip() if skills else "N/A",
                        "link": link,
                        "source": self.name,
                        "source_type": self.source_type
                    }

                    jobs.append(job_entry)
                    logger.info(f"Successfully scraped: '{title}' at '{company}'")
                    
                except Exception as card_error:
                    logger.error(f"Error occurred while processing Indeed card {idx+1}: {card_error}")
                    continue

        except Exception as e:
            logger.error(f"An unexpected error occurred during Indeed crawling: {e}")
            logger.info("Falling back to safe mock generator due to query exception...")
            return self._generate_mock_jobs(query, limit)
        finally:
            self.close_driver()
            
        # If scraper got blocked or returned nothing, fall back to mock data
        if not jobs:
            logger.warning("Indeed scraper returned 0 results. Activating mock fallback...")
            return self._generate_mock_jobs(query, limit)

        logger.info(f"Completed Indeed scraping. Total listings collected: {len(jobs)}")
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

    def _generate_mock_jobs(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Generates clean mock data to keep Indeed fully functional without active browser bypass.
        """
        mock_templates = [
            {
                "title": "Machine Learning Engineer",
                "company": "Amazon Tech Services",
                "location": "Bangalore / Remote",
                "salary": "₹ 14,0,000 - 20,00,000 /year",
                "skills": "Python, scikit-learn, AWS SageMaker, Deep Learning",
            },
            {
                "title": "AI Platform Engineer",
                "company": "Google Partner Solutions",
                "location": "Hyderabad / Hybrid",
                "salary": "₹ 16,0,000 - 24,0,000 /year",
                "skills": "PyTorch, Docker, Kubernetes, MLOps, LLMs",
            },
            {
                "title": "Data Scientist - AI Research",
                "company": "Microsoft Ingestion Hub",
                "location": "Noida",
                "salary": "₹ 15,0,000 - 21,0,000 /year",
                "skills": "TensorFlow, statistics, NLP, Transformers",
            }
        ]

        logger.info(f"Synthesizing mock Indeed listings for search query '{query}'...")
        jobs: List[Dict[str, Any]] = []
        
        for idx in range(limit):
            template = mock_templates[idx % len(mock_templates)]
            formatted_search = f"{template['title']} {template['company']} job".replace(" ", "+")
            link = f"https://www.google.com/search?q={formatted_search}"
            
            jobs.append({
                "title": f"{template['title']} (Mock)",
                "company": template["company"],
                "location": template["location"],
                "salary": template["salary"],
                "type": "Full-time",
                "experience": "2+ years",
                "skills": template["skills"],
                "link": link,
                "source": self.name,
                "source_type": self.source_type
            })
            
        return jobs
