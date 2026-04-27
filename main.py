from agent.brain import AgentBrain
from utils.filter import filter_ml_jobs
from utils.deduplicate import remove_duplicates
from tools.job_search import search_jobs
from tools.wellfound_search import search_wellfound_jobs
from utils.scorer import score_job
from utils.database import init_db, clean_incomplete_jobs, save_jobs_to_db
from utils.excel_writer import save_jobs_to_excel
import logging

logging.basicConfig(level=logging.INFO)


def run_agent():
    init_db()
    clean_incomplete_jobs()

    agent = AgentBrain()
    user_input = "Find ML and AI jobs"

    try:
        plan = agent.think(user_input)
        results = agent.act(plan)

    except Exception as e:
        logging.error(f"Agent failed: {e}")
        # Fallback to manual search
        internshala_jobs = search_jobs("ML AI jobs")
        wellfound_jobs = search_wellfound_jobs("ML AI jobs")
        results = internshala_jobs + wellfound_jobs

    # Limit for speed
    results = results[:5]

    # Filter
    results = filter_ml_jobs(results)

    # Deduplicate
    results = remove_duplicates(results)

    # Remove incomplete jobs before scoring / saving
    valid_results = []
    for job in results:
        title = (job.get("title") or "").strip()
        if not title or title.upper() == "N/A":
            continue
        if not job.get("link"):
            continue
        valid_results.append(job)

    print(f"[CLEANUP] Removed {len(results) - len(valid_results)} incomplete jobs")
    results = valid_results

    # Scoring
    for job in results:
        job["score"] = score_job(job)

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    # Save to DB → returns ONLY new jobs
    new_jobs = save_jobs_to_db(results)

    save_jobs_to_excel(new_jobs)

    return new_jobs


# keep CLI support
if __name__ == "__main__":
    jobs = run_agent()
    print(f"New jobs found: {len(jobs)}")