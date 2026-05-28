import logging

from utils.filter import filter_ml_jobs
from utils.deduplicate import remove_duplicates
from utils.scorer import score_job
from utils.database import init_db, clean_incomplete_jobs, save_jobs_to_db
from utils.excel_writer import save_jobs_to_excel

# Setup orchestrator logging
logger = logging.getLogger("AIJobAgent.Main")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def run_agent(query: str = "Find ML and AI jobs", limit_per_source: int = 10) -> list:
    """
    Executes the entire end-to-end Job Aggregation Platform Ingestion Pipeline.
    Triggered by CLI or the 24h Background Ingestion Scheduler.
    
    Args:
        query (str): The search query or job description intent.
        limit_per_source (int): Maximum listings to pull per platform.
        
    Returns:
        list: A list of newly discovered, filtered, and scored jobs inserted in this run.
    """
    # Dynamic imports to ensure Vercel can load main.py without importing Selenium/WebDriver
    from collectors.apis.arbeitnow_api import ArbeitnowCollector
    from collectors.apis.adzuna_api import AdzunaCollector
    from collectors.apis.jsearch_api import JSearchCollector
    from collectors.scrapers.internshala_scraper import InternshalaScraper
    from collectors.scrapers.wellfound_scraper import WellfoundScraper
    from collectors.scrapers.cutshort_scraper import CutshortScraper
    from collectors.scrapers.indeed_scraper import IndeedScraper

    logger.info("=" * 60)
    logger.info(f"STARTING CENTRAL ETL INGESTION RUN FOR QUERY: '{query}'")
    logger.info("=" * 60)

    # 1. Initialize persistent storage & perform schema migration checks
    init_db()
    clean_incomplete_jobs()

    collectors = [
        ArbeitnowCollector(),
        AdzunaCollector(),
        JSearchCollector(),
        InternshalaScraper(headless=True), # Internshala does not use anti-bot shields and works in headless mode
        WellfoundScraper(headless=False), # Wellfound requires headful mode to pass Cloudflare screens
        CutshortScraper(headless=False),   # Cutshort requires headful mode to load dynamic SPAs cleanly
        IndeedScraper(headless=False)      # Indeed requires headful mode to pass security screens
    ]

    raw_results = []

    # 3. Dynamic Aggregation Phase (Polymorphic iteration)
    for collector in collectors:
        try:
            logger.info(f"Triggering Collector: '{collector.name}' ({collector.source_type})...")
            platform_jobs = collector.collect(query, limit=limit_per_source)
            raw_results.extend(platform_jobs)
            logger.info(f"Collector '{collector.name}' successfully yielded {len(platform_jobs)} listings.")
        except Exception as col_err:
            logger.error(f"Collector '{collector.name}' encountered a isolated failure: {col_err}")
            # Continue executing other collectors safely
            continue

    if not raw_results:
        logger.warning("Pipeline collected 0 raw jobs from all combined sources. Ingestion terminated early.")
        return []

    # 4. Clean raw output: Discard obvious corrupt elements
    logger.info(f"Processing scraped outputs. Raw count: {len(raw_results)}")
    valid_results = []
    for job in raw_results:
        title = (job.get("title") or "").strip()
        link = (job.get("link") or "").strip()
        company = (job.get("company") or "").strip()
        
        if not title or title.upper() == "N/A" or not link or not company or company.upper() == "N/A":
            continue
        valid_results.append(job)

    logger.info(f"Integrity sweep: kept {len(valid_results)}/{len(raw_results)} fully formed listings.")
    results = valid_results

    # 5. Filter Layer: Fast keyword pre-filtering + AI evaluation
    results = filter_ml_jobs(results)

    # 6. Deduplicate Layer: In-memory duplicate removal
    results = remove_duplicates(results)

    # 7. Scoring Layer: Apply suitability algorithm
    logger.info("Computing algorithmic scores and ranking opportunities...")
    for job in results:
        job["score"] = score_job(job)

    # Sort listings descending by score (highest scores first)
    results = sorted(results, key=lambda x: x.get("score", 0.0), reverse=True)

    # 8. Database Persistence: Returns ONLY brand new jobs that do not already exist in DB
    new_jobs = save_jobs_to_db(results)

    # 9. Report Export Layer: Save newly discovered listings to structured styled Excel
    if new_jobs:
        save_jobs_to_excel(new_jobs)
    else:
        logger.info("No new listings found in this run; skipping Excel spreadsheet export.")

    logger.info(f"CENTRAL ETL INGESTION RUN COMPLETE. New jobs discovered and saved: {len(new_jobs)}")
    logger.info("=" * 60)
    
    return new_jobs


# CLI Support
if __name__ == "__main__":
    import sys
    search_term = "Find ML and AI jobs"
    if len(sys.argv) > 1:
        search_term = " ".join(sys.argv[1:])
        
    jobs = run_agent(search_term, limit_per_source=5)
    print(f"\n[CLI Summary] New jobs added: {len(jobs)}")


# ====================================================
# WSGI Serverless Function Entrypoint for Vercel
# ====================================================
def handler(environ, start_response):
    """
    Standard WSGI entrypoint automatically recognized by Vercel's Python runtime.
    Serves the job aggregation listings in JSON format.
    """
    import json
    from utils.database import get_all_jobs, init_db

    # Initialize the database schema and add columns if they don't exist
    init_db()

    status = '200 OK'
    headers = [
        ('Content-type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type')
    ]
    
    # Handle preflight options request
    if environ.get('REQUEST_METHOD') == 'OPTIONS':
        start_response('204 No Content', headers)
        return [b'']

    try:
        jobs = get_all_jobs()
        response_body = json.dumps({
            "status": "success",
            "count": len(jobs),
            "jobs": jobs
        }, default=str)
    except Exception as e:
        status = '500 Internal Server Error'
        response_body = json.dumps({
            "status": "error",
            "message": str(e)
        })

    start_response(status, headers)
    return [response_body.encode('utf-8')]


# Explicit top-level variable assignments strictly recognized by Vercel's builder
app = handler
application = handler