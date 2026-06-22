import os
from dotenv import load_dotenv
from graph import build_graph
from notifier import send_email_alert
# Import the Neon PostgreSQL helpers used by the workflow.
from database import init_db, is_job_duplicate, save_job_to_db

load_dotenv()

def main():
    print("==================================================")
    print("CareerSpy Autonomous Agent starting up...")
    
    # 1. Initialize the cloud database and create tables if needed.
    try:
        init_db()
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    # 2. Build the LangGraph workflow.
    print("Building LangGraph agentic workflow...")
    app = build_graph()
    
    # 3. Invoke the graph with the initial state.
    # URLs are fetched inside the graph, so the list starts empty here.
    initial_state = {
        "urls": [],
        "current_url_index": 0,
        "current_raw_text": "",
        "extracted_vacancies": []
    }
    
    print("Invoking AI agents...")
    final_state = app.invoke(initial_state)
    
    # 4. Collect the full job list extracted by the graph.
    extracted_jobs = final_state.get("extracted_vacancies", [])
    print(f"Total jobs extracted by AI: {len(extracted_jobs)}")
    
    if extracted_jobs:
        print("Syncing jobs with the Neon cloud database...")
        fresh_jobs = []
        
        # 5. Keep only fresh jobs that are not already stored in Neon.
        for job in extracted_jobs:
            title = job.get("job_title")
            source = job.get("company_source")
            
            if title and source:
                if not is_job_duplicate(title, source):
                    save_job_to_db(title, source)
                    fresh_jobs.append(job)
        
        print(f"Total fresh unique jobs found: {len(fresh_jobs)}")
        
        # 6. Send email alerts only when there are new jobs.
        if fresh_jobs:
            print("Preparing email alert for fresh opportunities...")
            send_email_alert(fresh_jobs)
        else:
            print("No new vacancies found since the last run. Notification skipped.")
    else:
        print("No tech vacancies found on the crawled pages today.")
        
    print("==================================================")
    print("CareerSpy AI execution completed successfully!")

if __name__ == "__main__":
    main()