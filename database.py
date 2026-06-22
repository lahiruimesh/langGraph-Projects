import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Neon cloud database connection string.
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Create a PostgreSQL connection for the Neon database."""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Create the job history table if it does not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_history (
            id SERIAL PRIMARY KEY,
            job_title TEXT NOT NULL,
            company_source TEXT NOT NULL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    print("Neon PostgreSQL database initialized successfully!")

def is_job_duplicate(job_title, company_source):
    """Check whether a job already exists in the Neon database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM job_history WHERE job_title = %s AND company_source = %s", 
        (job_title, company_source)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def save_job_to_db(job_title, company_source):
    """Save a new job to the Neon database."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO job_history (job_title, company_source) VALUES (%s, %s)",
            (job_title, company_source)
        )
        conn.commit()
        print(f"Successfully logged to Neon: {job_title}")
    except Exception as e:
        print(f"❌ Error saving to Neon DB: {e}")
        if conn:
            conn.rollback()
    finally:
        # Close resources only when they were created successfully.
        if cursor:
            cursor.close()
        if conn:
            conn.close()