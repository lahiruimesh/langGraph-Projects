import requests
import json
import os

def get_google_search_urls():
    """Serper.ai API එක පාවිච්චි කරලා ලංකාවේ අලුත්ම Intern Jobs Google Search කරනවා මචං"""
    print("🌐 Agent is launching a live Google Search for new opportunities...")
    
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("⚠️ SERPER_API_KEY not found in environment variables. Skipping search.")
        return []

    url = "https://google.serper.dev/search"
    
    # 💡 AI එකට ඕන අලුත්ම සර්ච් කීවර්ඩ් එක
    payload = json.dumps({
        "q": "software engineer intern jobs Sri Lanka 2026",
        "gl": "lk",  # Priority to Sri Lanka
        "num": 15    # Top 15 Search Results ඇදලා ගන්නවා මචං
    })
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            results = response.json()
            discovered_urls = []
            
            if "organic" in results:
                for item in results["organic"]:
                    link = item.get("link")
                    # 🛡️ අනවශ්‍ය LinkedIn main feeds හෝ generic root සයිට් අයින් කරනවා
                    if link and not any(x in link for x in ["linkedin.com/feed", "google.com"]):
                        discovered_urls.append(link)
            
            print(f"✨ Scout Tool found {len(discovered_urls)} potential URLs from Google!")
            return discovered_urls
        else:
            print(f"❌ Serper API Error: Status {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Exception during Google Search: {e}")
        return []