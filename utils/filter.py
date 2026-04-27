from utils.ai_filter import is_relevant_job


def filter_ml_jobs(jobs):
    keywords = ["ml", "ai", "data", "python"]

    filtered = []
    uncertain = []

    for job in jobs:
        text = (job["title"] + " " + job["company"]).lower()

        # ✅ Clear match → keep immediately
        if any(k in text for k in keywords):
            filtered.append(job)
        else:
            uncertain.append(job)

    print(f"[INFO] Fast filtered: {len(filtered)}")
    print(f"[INFO] Uncertain jobs: {len(uncertain)}")

    # 🔥 AI only on uncertain jobs
    for job in uncertain:
        decision = is_relevant_job(job)

        if decision is True:
            filtered.append(job)
        elif decision is None:
            print("[WARNING] AI filter unavailable or failed, returning all jobs")
            return jobs

    # Safety fallback
    if not filtered:
        print("[WARNING] No jobs after filtering → returning all")
        return jobs

    return filtered