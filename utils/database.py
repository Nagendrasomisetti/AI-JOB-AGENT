import sqlite3
import logging
import os
from typing import List, Dict, Any

# Configure structured logging
logger = logging.getLogger("AIJobAgent.Database")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs.db")

def get_connection() -> sqlite3.Connection:
    """
    Creates and returns a thread-safe SQLite connection.
    Configured with a longer busy timeout to handle concurrent dashboard reads and daemon writes.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initializes the SQLite schema with optimized indexes.
    This creates the table structure, ensuring link uniqueness to prevent duplicates.
    Includes automated, non-destructive migration checks for pre-existing legacy schemas.
    """
    logger.info("Initializing database schema...")
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # 1. Create base jobs table (fully expanded production schema)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                salary TEXT,
                type TEXT,
                experience TEXT,
                skills TEXT,
                link TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'Scraper',
                score REAL DEFAULT 0.0,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 2. Add speed index for link verification to avoid full table scans
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_link ON jobs (link)')
            
            # 3. Dynamic Column Migration Check (Upgrade pre-existing legacy tables)
            cursor.execute("PRAGMA table_info(jobs)")
            columns = [row["name"] for row in cursor.fetchall()]
            
            # Legacy column upgrades
            if "created_at" not in columns:
                logger.info("Upgrading database schema: adding missing 'created_at' column...")
                cursor.execute("ALTER TABLE jobs ADD COLUMN created_at TIMESTAMP")
                cursor.execute("UPDATE jobs SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
                
            if "fetched_at" not in columns:
                logger.info("Upgrading database schema: adding missing 'fetched_at' column...")
                cursor.execute("ALTER TABLE jobs ADD COLUMN fetched_at TIMESTAMP")
                cursor.execute("UPDATE jobs SET fetched_at = CURRENT_TIMESTAMP WHERE fetched_at IS NULL")
                
            if "source_type" not in columns:
                logger.info("Upgrading database schema: adding missing 'source_type' column...")
                cursor.execute("ALTER TABLE jobs ADD COLUMN source_type TEXT DEFAULT 'Scraper'")
            
            conn.commit()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def clean_incomplete_jobs() -> int:
    """
    Cleans out incomplete, corrupt, or garbage listings from the database.
    Returns:
        int: Number of rows deleted.
    """
    query = """
    DELETE FROM jobs 
    WHERE title IS NULL 
       OR trim(title) = '' 
       OR upper(trim(title)) = 'N/A'
       OR link IS NULL
       OR trim(link) = ''
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            deleted_count = cursor.rowcount
            conn.commit()
            if deleted_count > 0:
                logger.info(f"Database cleanup complete: Removed {deleted_count} corrupt or empty listings.")
            return deleted_count
    except sqlite3.Error as e:
        logger.error(f"Error occurred during incomplete job cleanup: {e}")
        return 0


def save_jobs_to_db(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Persists new jobs in a transaction-safe manner. Ignores duplicates based on the UNIQUE link constraint.
    Explicitly injects CURRENT_TIMESTAMP into the query to comply with SQLite constraints.
    
    Args:
        jobs (List[Dict]): List of extracted jobs from collectors.
        
    Returns:
        List[Dict]: A list of ONLY the newly inserted jobs during this execution run.
    """
    if not jobs:
        logger.info("No jobs provided to save.")
        return []

    inserted_jobs = []
    logger.info(f"Attempting to persist {len(jobs)} jobs in database...")
    
    # Explicitly pass CURRENT_TIMESTAMP for fetched_at & created_at to avoid SQLite ALTER TABLE expression limits
    query = """
    INSERT INTO jobs (title, company, location, salary, type, experience, skills, link, source, source_type, score, created_at, fetched_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            for job in jobs:
                # Basic schema safety cleaning on inputs
                title = (job.get("title") or "").strip()
                company = (job.get("company") or "").strip()
                link = (job.get("link") or "").strip()
                
                # Check for absolute requirements
                if not title or title.upper() == "N/A" or not link or not company or company.upper() == "N/A":
                    continue
                
                # Default created_at to current timestamp if not supplied
                created_at = job.get("created_at") or None
                
                try:
                    cursor.execute(query, (
                        title,
                        company,
                        job.get("location", "N/A"),
                        job.get("salary", "N/A"),
                        job.get("type", "Full-time"),
                        job.get("experience", "N/A"),
                        job.get("skills", "N/A"),
                        link,
                        job.get("source", "Unknown"),
                        job.get("source_type", "Scraper"),
                        float(job.get("score", 0.0)),
                        created_at
                    ))
                    # If execution succeeded, it's a new job!
                    inserted_jobs.append(job)
                except sqlite3.IntegrityError:
                    # SQLite UNIQUE constraint failed: this job has already been scraped in a historical run
                    continue
                except sqlite3.Error as inner_err:
                    logger.warning(f"Failed to insert single job link '{link}': {inner_err}")
            
            conn.commit()
        
        logger.info(f"Database sync complete. Persisted {len(inserted_jobs)} brand new jobs.")
        return inserted_jobs

    except sqlite3.Error as e:
        logger.error(f"Critical database transaction failure: {e}")
        return []


def get_all_jobs() -> List[Dict[str, Any]]:
    """
    Fetches all jobs from the database ordered by score descending.
    
    Returns:
        List[Dict]: List of dict representation of all persisted jobs.
    """
    query = "SELECT * FROM jobs ORDER BY score DESC, fetched_at DESC"
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch jobs from database: {e}")
        return []