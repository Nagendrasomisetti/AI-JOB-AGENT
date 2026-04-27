import pandas as pd
import datetime


def save_jobs_to_excel(jobs):
    if not jobs:
        print("[INFO] No jobs to save")
        return

    df = pd.DataFrame(jobs)

    # 🔥 Ensure column order (important for readability)
    columns = [
        "title",
        "company",
        "location",
        "salary",
        "type",
        "experience",
        "skills",
        "link",
        "source",
        "score"
    ]

    # Only keep available columns safely
    df = df[[col for col in columns if col in df.columns]]

    filename = f"jobs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    df.to_excel(filename, index=False)

    print(f"[SUCCESS] Saved {len(jobs)} jobs to {filename}")