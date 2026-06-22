import requests
import json
import os

def get_google_search_urls():
    """Use the Serper API to search Google for the latest global and local AI/ML internships."""
    print("Launching a live Google search for new opportunities...")
    
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("SERPER_API_KEY not found in environment variables. Skipping search.")
        return []

    url = "https://google.serper.dev/search"
    
    search_queries = [
        "AI ML Engineer Intern remote worldwide 2026",
        "Machine Learning Intern remote global jobs",
        "Software Engineer Intern AI remote hybrid Sri Lanka"
    ]

    # Collect all URLs discovered from each search query.
    all_discovered_urls = []

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    # Execute searches for each keyword sequentially.
    for query in search_queries:
        print(f"Searching Google for: '{query}'")
        
        payload = json.dumps({
            "q": query,       
            "num": 20         # Fetch top 20 results globally.
        })
        
        try:
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                results = response.json()
                
                if "organic" in results:
                    for item in results["organic"]:
                        link = item.get("link")
                        if link:
                            # Skip generic root links and LinkedIn feed pages.
                            if not any(x in link for x in ["linkedin.com/feed", "google.com"]):
                                all_discovered_urls.append(link)
            else:
                print(f"❌ Serper API error for query '{query}': status {response.status_code}")
        except Exception as e:
            print(f"❌ Exception during Google search for query '{query}': {e}")

    # Deduplicate URLs found across multiple search queries.
    unique_urls = list(set(all_discovered_urls))
    
    print(f"Scout tool completely finished! Found {len(unique_urls)} TOTAL unique URLs from Google.")
    return unique_urls