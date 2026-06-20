import os
from dotenv import load_dotenv
from graph import build_graph
from notifier import send_email_alert
# 💡 SQLite වෙනුවට අපේ අලුත් Neon PostgreSQL ෆන්ක්ෂන්ස් ඉම්පෝර්ට් කරගත්තා මචං
from database import init_db, is_job_duplicate, save_job_to_db

load_dotenv()

def main():
    print("==================================================")
    print("🚀 CareerSpy Autonomous Agent Starting up...")
    
    # 1. 🌐 Cloud Database එක ලයිව්ම Initialize කිරීම (Table එක නැත්නම් හදනවා)
    try:
        init_db()
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    # 2. 🏗️ LangGraph Workflow එක Build කර ගැනීම
    print("🏗️ Building LangGraph Agentic Workflow...")
    app = build_graph()
    
    # 3. 🧠 මුලින්ම දෙන State එක (Initial State) සමඟ Graph එක Invoke කරනවා
    # 💡 සර්ච් සහ ශීට් ලින්ක්ස් ඔක්කොම LangGraph එක ඇතුළෙන්ම Fetch වෙන නිසා මෙතන හිස්ව තියන්නේ මචං
    initial_state = {
        "urls": [],
        "current_url_index": 0,
        "current_raw_text": "",
        "extracted_vacancies": []
    }
    
    print("🚀 Invoking AI Agents...")
    final_state = app.invoke(initial_state)
    
    # 4. Graph එකෙන් Extract කරගත්තු මුළු ජොබ්ස් ලැයිස්තුව ගන්නවා
    extracted_jobs = final_state.get("extracted_vacancies", [])
    print(f"📊 Total jobs extracted by AI: {len(extracted_jobs)}")
    
    if extracted_jobs:
        print("💾 Syncing jobs with Neon Cloud Database...")
        fresh_jobs = []
        
        # 5. 🎯 Neon DB එකෙන් ලයිව් චෙක් කරලා Duplicate නැති 'Fresh' ඒවා විතරක් පෙරලා ගැනීම
        for job in extracted_jobs:
            title = job.get("job_title")
            source = job.get("company_source")
            
            if title and source:
                # Neon DB එකෙන් ලයිව්ම ඩුප්ලිකේට් ද බලනවා මචං
                if not is_job_duplicate(title, source):
                    save_job_to_db(title, source)
                    fresh_jobs.append(job)
        
        print(f"✨ Total FRESH unique jobs found: {len(fresh_jobs)}")
        
        # 6. අලුත් ජොබ්ස් තියෙනවා නම් විතරක් Email එකක් බ්ලාස්ට් කරනවා
        if fresh_jobs:
            print("📧 Preparing Email Blast for fresh opportunities...")
            send_email_alert(fresh_jobs)
        else:
            print("🔒 No new/fresh vacancies found since the last run. Notification skipped.")
    else:
        print("📭 No tech vacancies found on the crawled pages today.")
        
    print("==================================================")
    print("🏁 CareerSpy AI Execution Completed Successfully!")

if __name__ == "__main__":
    main()