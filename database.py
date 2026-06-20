import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Neon Cloud DB Connection String
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Neon PostgreSQL DB එකට ආරක්ෂිතව කනෙක්ට් වන ෆන්ක්ෂන් එක"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """සර්වර් එකේ මුලින්ම Table එක ක්‍රියේට් කරන එක (SQLite වල AUTOINCREMENT වෙනුවට SERIAL)"""
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
    print("✨ Neon PostgreSQL Database Initialized Successfully!")

def is_job_duplicate(job_title, company_source):
    """පරණ ජොබ් එකක්දැයි Neon DB එකෙන් ලයිව් චෙක් කිරීම (SQLite '?' වෙනුවට '%s')"""
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
    """අලුත් ජොබ් එකක් Neon DB එකට සේව් කිරීම (ආරක්ෂිත ක්‍රමය)"""
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
        print(f"💾 Successfully logged to Neon: {job_title}") # ලොග් එකක් දැම්මා මචං
    except Exception as e:
        print(f"❌ Error saving to Neon DB: {e}")
        if conn:
            conn.rollback()
    finally:
        # 💡 කනෙක්ෂන් එකක් තිබුණොත් පමණක් ක්ලෝස් කිරීමට සේෆ්ටි චෙක් එකක් දැම්මා
        if cursor:
            cursor.close()
        if conn:
            conn.close()