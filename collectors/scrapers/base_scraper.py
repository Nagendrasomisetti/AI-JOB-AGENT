import logging
import time
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger("AIJobAgent.BaseScraper")

class BaseScraper:
    """
    A robust base scraper that initializes a configured Selenium Chrome instance
    with anti-bot evasion techniques and uniform element wait strategies.
    """
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None

    def initialize_driver(self) -> webdriver.Chrome:
        """
        Creates and returns a Chrome WebDriver instance with anti-detection flags.
        """
        logger.info("Initializing Selenium Chrome Driver...")
        options = webdriver.ChromeOptions()
        
        # Headless Configuration
        if self.headless:
            # '--headless=new' is the modern Chromium headless mode
            options.add_argument("--headless=new")
        
        # Anti-Bot Evasion Arguments
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # Turn off automation flags & automation detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set a realistic user-agent to bypass basic header inspection
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        options.add_argument(f"user-agent={user_agent}")
        
        try:
            # Automated Chrome binary download and connection management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Use CDP (Chrome DevTools Protocol) to remove navigator.webdriver flag
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                    """
                }
            )
            
            logger.info("Selenium Chrome Driver initialized successfully with evasion techniques.")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to initialize Selenium Chrome Driver: {e}")
            raise

    def wait_for_element(self, by: By, selector: str, timeout: int = 15) -> Optional[webdriver.remote.webelement.WebElement]:
        """
        Robustly waits for an element to be loaded and present in the DOM.
        """
        if not self.driver:
            raise ValueError("Driver is not initialized. Call initialize_driver() first.")
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except Exception:
            logger.debug(f"Element '{selector}' was not found within {timeout} seconds.")
            return None

    def wait_for_elements(self, by: By, selector: str, timeout: int = 10) -> List[webdriver.remote.webelement.WebElement]:
        """
        Robustly waits for at least one element to match the selector and return the list.
        """
        if not self.driver:
            raise ValueError("Driver is not initialized.")
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_all_elements_located((by, selector)))
        except Exception:
            logger.debug(f"Elements matching '{selector}' not loaded within {timeout} seconds.")
            return []

    def get_element_text_with_fallbacks(self, element, fallbacks: List[str] = None) -> str:
        """
        Attempts to read element innerText or textContent resiliently, falling back
        to secondary attributes or executing direct JavaScript if necessary.
        """
        if not element:
            return "N/A"
        try:
            # 1. Standard text properties
            text = element.get_attribute("innerText") or element.get_attribute("textContent") or element.text
            if text and text.strip():
                return text.strip()
            
            # 2. Direct JS execution fallback (bypasses selenium element state cache errors)
            if self.driver:
                text = self.driver.execute_script(
                    "return arguments[0].innerText || arguments[0].textContent || '';", 
                    element
                )
                if text and text.strip():
                    return text.strip()
        except Exception:
            pass
            
        return "N/A"

    def close_driver(self) -> None:
        """
        Safely shuts down the active browser instance and cleans up memory.
        """
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium Chrome Driver shutdown successfully.")
            except Exception as e:
                logger.warning(f"Error shutting down WebDriver: {e}")
            finally:
                self.driver = None
