from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
import time


def get_element_text(element, driver=None):
    try:
        text = element.get_attribute("innerText") or element.get_attribute("textContent") or element.text
        if text:
            return text.strip()
        if driver is not None:
            text = driver.execute_script('return arguments[0].innerText || arguments[0].textContent || "";', element)
            return (text or "").strip()
        return ""
    except:
        return ""


def search_jobs(query: str):
    print(f"[TOOL] Searching Internshala for: {query}")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    jobs = []
    seen_links = set()

    search_url = f"https://internshala.com/internships/keywords-{query.replace(' ', '%20')}"
    driver.get(search_url)
    time.sleep(5)

    print("Page title:", driver.title)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.container-fluid.individual_internship.view_detail_button")
    print("Job cards found on page:", len(cards))

    for i, card in enumerate(cards[:20]):
        try:
            print(f"\n--- Processing job {i+1} ---")

            link = card.get_attribute("data-href") or ""
            if link and link.startswith("/"):
                link = urljoin("https://internshala.com", link)

            if not link or "internship/detail" not in link:
                print("Skipping card without valid detail link")
                continue

            if link in seen_links:
                print("Skipping duplicate link")
                continue

            seen_links.add(link)

            title = "N/A"
            try:
                title_el = card.find_element(By.CSS_SELECTOR, "h2.job-internship-name a.job-title-href")
                title = get_element_text(title_el, driver) or "N/A"
            except:
                pass

            company = "N/A"
            try:
                company_el = card.find_element(By.CSS_SELECTOR, "p.company-name")
                company = get_element_text(company_el, driver) or "N/A"
            except:
                pass

            location = "N/A"
            try:
                location_el = card.find_element(By.CSS_SELECTOR, "div.row-1-item.locations")
                location = get_element_text(location_el, driver) or "N/A"
            except:
                pass

            if title in ("N/A", "") and link:
                print("Attempting title fallback from detail page")
                driver.execute_script("window.open(arguments[0]);", link)
                driver.switch_to.window(driver.window_handles[-1])
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    detail_title_el = driver.find_element(By.CSS_SELECTOR, "h1, h2, h3")
                    detail_title = get_element_text(detail_title_el)
                    if detail_title:
                        title = detail_title
                except:
                    pass
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            job = {
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

            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[-1])

            details = extract_job_details_selenium(driver, wait)
            job.update(details)

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            jobs.append(job)

        except Exception as e:
            print("[WARNING] Skipping card:", e)

    driver.quit()

    return jobs


def extract_job_details_selenium(driver, wait):
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        skills = "N/A"
        try:
            skill_elements = driver.find_elements(By.CSS_SELECTOR, ".round_tabs, .internship_other_details li, .skills_list span")
            skills = ", ".join([s.text for s in skill_elements if s.text])
        except:
            pass

        salary = "N/A"
        try:
            salary = driver.find_element(By.CSS_SELECTOR, ".stipend, .internship_detail_item .stipend, .internship_other_details").text
        except:
            pass

        experience = "N/A"
        try:
            exp_elements = driver.find_elements(By.CSS_SELECTOR, ".other_detail_item, .internship_detail_item, .internship_other_details li")
            if exp_elements:
                experience = exp_elements[0].text
        except:
            pass

        print("→ Extracted details:", skills, salary, experience)

        return {
            "skills": skills,
            "salary": salary,
            "experience": experience
        }

    except Exception as e:
        print("[DETAIL ERROR]", e)
        return {}
