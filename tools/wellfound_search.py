from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time


def get_element_text(element):
    try:
        text = element.get_attribute("textContent") or element.text
        return text.strip()
    except:
        return ""


def search_wellfound_jobs(query: str):
    print(f"[TOOL] Searching Wellfound for: {query}")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # 🔥 Search URL with query
    driver.get(f"https://wellfound.com/jobs?q={query.replace(' ', '+')}")

    time.sleep(6)

    jobs = []

    cards = driver.find_elements(By.CSS_SELECTOR, "div.job-listing")

    print("Wellfound jobs found:", len(cards))

    for card in cards[:10]:
        try:
            title = "N/A"
            company = "N/A"
            location = "N/A"
            link = "N/A"

            try:
                title_el = card.find_element(By.CSS_SELECTOR, "h2")
                title = get_element_text(title_el) or "N/A"
            except:
                pass

            try:
                company_el = card.find_element(By.CSS_SELECTOR, "h3")
                company = get_element_text(company_el) or "N/A"
            except:
                pass

            try:
                location_el = card.find_element(By.CSS_SELECTOR, ".location")
                location = get_element_text(location_el) or "N/A"
            except:
                pass

            try:
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href") or "N/A"
            except:
                pass

            if link == "N/A":
                continue

            job = {
                "title": title,
                "company": company,
                "location": location,
                "salary": "N/A",
                "type": "Full-time",
                "experience": "N/A",
                "skills": "N/A",
                "link": link,
                "source": "Wellfound"
            }

            jobs.append(job)

        except Exception as e:
            print("[WARNING]", e)

    driver.quit()

    return jobs