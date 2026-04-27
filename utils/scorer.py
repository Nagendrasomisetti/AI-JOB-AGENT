def score_job(job):
    score = 0

    title = job.get("title", "").lower()
    skills = job.get("skills", "").lower()
    salary = job.get("salary", "")
    location = job.get("location", "").lower()

    # 🔥 1. Title scoring
    if "machine learning" in title or "ml" in title:
        score += 30
    elif "data scientist" in title:
        score += 25
    elif "ai" in title:
        score += 25
    elif "data" in title:
        score += 15
    else:
        score += 5

    # 🔥 2. Skills scoring (MOST IMPORTANT)
    important_skills = ["python", "machine learning", "deep learning", "nlp", "tensorflow", "pytorch"]

    for skill in important_skills:
        if skill in skills:
            score += 10

    # 🔥 3. Salary scoring
    try:
        if "₹" in salary:
            amount = int("".join(filter(str.isdigit, salary)))
            if amount >= 20000:
                score += 20
            elif amount >= 10000:
                score += 10
    except:
        pass

    # 🔥 4. Location bonus
    if "remote" in location:
        score += 10

    return score