import requests
import json
import os

def get_google_search_urls():
    """Use the Serper API to search Google for the latest internship jobs in Sri Lanka."""
    print("Launching a live Google search for new opportunities...")
    
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("SERPER_API_KEY not found in environment variables. Skipping search.")
        return []

    url = "https://google.serper.dev/search"
    
    # Search for the latest internship-related keywords.
    payload = json.dumps({
        "q": "software engineer intern jobs Sri Lanka 2026",
        "gl": "lk",  # Prioritize Sri Lanka.
        "num": 15    # Fetch the top 15 search results.
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
                    # Skip generic root links and LinkedIn feed pages.
                    if link and not any(x in link for x in ["linkedin.com/feed", "google.com"]):
                        discovered_urls.append(link)
            
            print(f"Scout tool found {len(discovered_urls)} potential URLs from Google!")
            return discovered_urls
        else:
            print(f"Serper API error: status {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception during Google search: {e}")
        return []