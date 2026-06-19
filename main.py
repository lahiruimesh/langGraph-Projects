from graph import build_graph
from database import fetch_target_urls, save_and_sync_vacancies
from notifier import send_email_alert

def main():
    print("==================================================")
    # 1. Google Sheet එකෙන් Target URLs ලැයිස්තුව ඇදලා ගන්නවා
    target_urls = fetch_target_urls()
    
    if not target_urls:
        print("🛑 No target URLs found in the Google Sheet. Exiting...")
        return
        
    print(f"📋 Found {len(target_urls)} target URLs to monitor.")
    
    # 2. ඔයා කිව්වා වගේම වෙනම ෆයිල් එකකින් Graph එක ගන්නවා
    print("🏗️ Building LangGraph Agentic Workflow...")
    app = build_graph()
    
    # 3. මුලින්ම දෙන State එක (Initial State) සමඟ Graph එක Invoke කරනවා
    initial_state = {
        "urls": target_urls,
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
        # 5. SQLite + Google Sheet සමඟ Sync කරලා, Duplicate නැති 'Fresh' ඒවා විතරක් ගන්නවා
        fresh_jobs = save_and_sync_vacancies(extracted_jobs)
        
        # 6. අලුත් ජොබ්ස් තියෙනවා නම් විතරක් Email එකක් බ්ලාස්ට් කරනවා
        if fresh_jobs:
            send_email_alert(fresh_jobs)
        else:
            print("🔒 No new/fresh vacancies found since the last run. Notification skipped.")
    else:
        print("📭 No tech vacancies found on the crawled pages today.")
        
    print("==================================================")
    print("🏁 CareerSpy AI Execution Completed Successfully!")

if __name__ == "__main__":
    main()