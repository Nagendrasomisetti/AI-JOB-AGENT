import logging
from agent.brain import AgentBrain
from tools.internshala import InternshalaScraper
from tools.wellfound import WellfoundScraper
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


def run_agent(query: str = "Find ML and AI jobs") -> list:
    """
    Executes the entire end-to-end Autonomous Job Agent Pipeline.
    
    Args:
        query (str): The search query or job description intent.
        
    Returns:
        list: A list of newly discovered, filtered, and scored jobs inserted in this run.
    """
    logger.info("=" * 60)
    logger.info(f"STARTING AI JOB AGENT PIPELINE RUN FOR QUERY: '{query}'")
    logger.info("=" * 60)

    # 1. Initialize persistent storage & perform index sweeps
    init_db()
    clean_incomplete_jobs()

    # 2. Planning phase: Ask the agent to think
    agent = AgentBrain()
    results = []

    try:
        plan = agent.think(query)
        # Execute the generated plan (limit to 10 listings per scraper for speed and safety)
        results = agent.act(plan, max_jobs_per_source=10)
    except Exception as plan_err:
        logger.error(f"Agent planning or execution encountered an error: {plan_err}")
        logger.info("Initiating structural fallback: Executing direct scraper crawlers...")
        
        # Safe Fallback: Direct crawl without Gemini planning
        try:
            internshala_scraper = InternshalaScraper(headless=True)
            internshala_jobs = internshala_scraper.scrape_internships("machine learning", max_results=5)
            
            wellfound_scraper = WellfoundScraper(headless=True)
            wellfound_jobs = wellfound_scraper.scrape_jobs("machine learning", max_results=5)
            
            results = internshala_jobs + wellfound_jobs
        except Exception as fallback_err:
            logger.critical(f"Direct scraper fallback also failed: {fallback_err}")
            results = []

    if not results:
        logger.warning("Pipeline collected 0 raw jobs. Terminating pipeline execution early.")
        return []

    # 3. Clean raw output: Discard obvious corrupt elements
    logger.info(f"Processing scraped outputs. Raw count: {len(results)}")
    valid_results = []
    for job in results:
        title = (job.get("title") or "").strip()
        link = (job.get("link") or "").strip()
        company = (job.get("company") or "").strip()
        
        if not title or title.upper() == "N/A" or not link or not company or company.upper() == "N/A":
            continue
        valid_results.append(job)

    logger.info(f"Integrity sweep: kept {len(valid_results)}/{len(results)} fully formed listings.")
    results = valid_results

    # 4. Filter Layer: Fast keyword pre-filtering + AI evaluation
    results = filter_ml_jobs(results)

    # 5. Deduplicate Layer: In-memory duplicate removal
    results = remove_duplicates(results)

    # 6. Scoring Layer: Apply suitability algorithm
    logger.info("Computing algorithmic scores and ranking opportunities...")
    for job in results:
        job["score"] = score_job(job)

    # Sort listings descending by score (highest scores first)
    results = sorted(results, key=lambda x: x.get("score", 0.0), reverse=True)

    # 7. Database Persistence: Returns ONLY brand new jobs that do not already exist in DB
    new_jobs = save_jobs_to_db(results)

    # 8. Report Export Layer: Save newly discovered listings to structured styled Excel
    if new_jobs:
        save_jobs_to_excel(new_jobs)
    else:
        logger.info("No new listings found in this run; skipping Excel spreadsheet export.")

    logger.info(f"PIPELINE RUN COMPLETE. New jobs discovered and saved: {len(new_jobs)}")
    logger.info("=" * 60)
    
    return new_jobs


# CLI Support
if __name__ == "__main__":
    import sys
    search_term = "Find ML and AI jobs"
    if len(sys.argv) > 1:
        search_term = " ".join(sys.argv[1:])
        
    jobs = run_agent(search_term)
    print(f"\n[CLI Summary] New jobs added: {len(jobs)}")