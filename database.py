import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Any

# =====================================================================
# 1. SQLITE LOCAL DATABASE MANAGEMENT
# =====================================================================

def init_db():
    """
    Local SQLite database එක initialize කර 'vacancies' table එක සාදයි.
    """
    conn = sqlite3.connect("career_spy.db")
    cursor = conn.cursor()
    # Challenge 3 විසඳුම: job_title සහ company_source එකතු කර UNIQUE constraint එකක් දමා ඇත.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            company_source TEXT,
            skills TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(job_title, company_source)
        )
    """)
    conn.commit()
    conn.close()

def is_duplicate(job_title: str, company_source: str) -> bool:
    """
    ජොබ් එකක් දැනටමත් database එකේ තියෙනවාද කියා පරීක්ෂා කරයි.
    """
    conn = sqlite3.connect("career_spy.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM vacancies WHERE job_title = ? AND company_source = ?", 
        (job_title, company_source)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def insert_vacancy(job_title: str, company_source: str, skills: List[str]):
    """
    අලුත් ජොබ් එකක් local database එකට ඇතුළත් කරයි.
    """
    conn = sqlite3.connect("career_spy.db")
    cursor = conn.cursor()
    try:
        skills_str = ", ".join(skills)
        cursor.execute(
            "INSERT INTO vacancies (job_title, company_source, skills) VALUES (?, ?, ?)",
            (job_title, company_source, skills_str)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # UNIQUE constraint එක නිසා duplicate ඒවා වැදුණොත් ignore කරයි
        pass
    finally:
        conn.close()


# =====================================================================
# 2. GOOGLE SHEETS API INTEGRATION
# =====================================================================

def get_gspread_client():
    """
    credentials.json පාවිච්චි කරලා Google Sheets සමඟ සම්බන්ධ වේ.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    # credentials.json ෆයිල් එක ඔයාගේ root folder එකේ තිබිය යුතුයි මචං
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)

def fetch_target_urls() -> List[str]:
    """
    Challenge 6 විසඳුම: Google Sheet එකේ 'Target_URLs' ටැබ් එකෙන් 
    ස්කෑන් කළ යුතු වෙබ් අඩවි ලැයිස්තුව කියවයි.
    """
    print("📋 Fetching target URLs from Google Sheet...")
    try:
        gc = get_gspread_client()
        # ඔයාගේ Google Sheet එකේ නම මෙතන දාන්න (උදා: CareerSpy_Dashboard)
        sh = gc.open("CareerSpy_Dashboard") 
        worksheet = sh.worksheet("Target_URLs")
        
        # පළමු column එකේ තියෙන ඔක්කොම URLs ටික ගන්නවා (Header එක අතහැර)
        urls = worksheet.col_values(1)[1:] 
        # හිස් ලයින් තියෙනවා නම් අයින් කරනවා
        return [url.strip() for url in urls if url.strip()]
    except Exception as e:
        print(f"❌ Error fetching URLs from Google Sheet: {e}")
        return []

def save_and_sync_vacancies(extracted_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Gemini දුන් ජොබ්ස් වලින් Duplicate නැති 'Fresh' ජොබ්ස් විතරක් 
    Local DB එකට සහ Google Sheet එකේ 'Sheet1' ටැබ් එකට ලියයි.
    """
    print("💾 Syncing jobs with SQLite and Google Sheets...")
    init_db() # DB එක නැත්නම් initialize කරනවා
    
    fresh_jobs = []
    
    try:
        gc = get_gspread_client()
        sh = gc.open("CareerSpy_Dashboard")
        worksheet = sh.worksheet("Sheet1") # ජොබ්ස් ලොග් වෙන ප්‍රධාන ටැබ් එක
        
        for job in extracted_jobs:
            title = job.get("job_title", "").strip()
            source = job.get("company_source", "").strip()
            skills = job.get("skills", [])
            
            # 🛡️ Local DB එකෙන් Duplicate ද කියා චෙක් කිරීම
            if not is_duplicate(title, source):
                # 1. Local DB එකට දානවා
                insert_vacancy(title, source, skills)
                
                # 2. Google Sheet එකට අලුත් පේළියක් විදිහට Append කරනවා
                skills_str = ", ".join(skills)
                worksheet.append_row([title, source, skills_str])
                
                print(f"✨ New Job Found & Logged: {title} at {source}")
                
                # Notification යවන්න ඕන නිසා fresh_jobs ලිස්ට් එකට එකතු කරනවා
                fresh_jobs.append(job)
                
        return fresh_jobs
        
    except Exception as e:
        print(f"❌ Error syncing with Google Sheets: {e}")
        return fresh_jobs