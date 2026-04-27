def remove_duplicates(jobs):
    seen = set()
    unique_jobs = []

    for job in jobs:
        identifier = job["title"] + job["company"] + job["link"]

        if identifier not in seen:
            seen.add(identifier)
            unique_jobs.append(job)

    return unique_jobs