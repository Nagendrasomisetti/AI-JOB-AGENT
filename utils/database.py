import sqlite3

def init_db():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        salary TEXT,
        type TEXT,
        experience TEXT,
        skills TEXT,
        link TEXT UNIQUE,
        source TEXT,
        score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    # Add index for faster duplicate checks
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_link ON jobs (link)')
    conn.commit()
    conn.close()


def clean_incomplete_jobs():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE title IS NULL OR trim(title) = '' OR upper(trim(title)) = 'N/A'")
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted:
        print(f"[DB CLEANUP] Removed {deleted} incomplete jobs")


def save_jobs_to_db(jobs):

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    new_jobs = []

    for job in jobs:
        try:
            cursor.execute("""
            INSERT INTO jobs (title, company, location, salary, type, experience, skills, link, source, score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.get("title"),
                job.get("company"),
                job.get("location"),
                job.get("salary"),
                job.get("type"),
                job.get("experience"),
                job.get("skills"),
                job.get("link"),
                job.get("source"),
                job.get("score")
            ))

            # ✅ Only NEW jobs added
            new_jobs.append(job)

        except sqlite3.IntegrityError:
            # duplicate → ignore
            pass

    conn.commit()
    conn.close()

    print(f"[DB] New jobs inserted: {len(new_jobs)}")

    return new_jobs