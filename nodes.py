from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import os
import json
import gspread
from dotenv import load_dotenv
from state import CareerSpyState
from search_utils import get_google_search_urls  # 🌐 සර්ච් ටූල් එක ඉම්පෝර්ට් කළා මචං

load_dotenv()

# Google GenAI Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def fetch_urls_node(state: CareerSpyState) -> CareerSpyState:
    """
    පළමු Node එක: Google Sheet එකේ තියෙන URLs සහ ලයිව් Google Search එකෙන්
    හම්බවෙන URLs දෙකම එකතු කර Unique ලිස්ට් එකක් සාදයි.
    """
    print("\n==================================================")
    print("📋 Fetching Target URLs From Multi-Sources...")
    combined_urls = []
    
    # 1. Google Sheet එකෙන් පරණ ලින්ක්ස් කියවීම
    try:
        # 💡 උඹේ Sheet ID එක මෙතනට දාන්න මචං
        gc = gspread.service_account(filename="credentials.json")
        sheet = gc.open_by_key("1PhWmYoRpxE7Cs-8BzE1FEkcxml3aiwuymRLSSRf9UMI").sheet1
        sheet_urls = sheet.col_values(1)[1:]  # Header එක ඇර ඉතිරි ටික
        print(f"📊 Found {len(sheet_urls)} URLs inside Google Sheet.")
        combined_urls.extend(sheet_urls)
    except Exception as e:
        print(f"❌ Error fetching URLs from Google Sheet: {e}")

    # 2. Serper API එකෙන් ලයිව් ගූගල් සර්ච් කර අලුත් ලින්ක්ස් ගැනීම
    search_urls = get_google_search_urls()
    combined_urls.extend(search_urls)
    
    # 3. Smart Deduplication (ලින්ක්ස් ඩියුප්ලිකේට් වීම වැළැක්වීම)
    unique_urls = list(set(combined_urls))
    
    print(f"🚀 Total Unique URLs to scan today: {len(unique_urls)}")
    print("==================================================")
    
    return {"urls": unique_urls}

def scraper_node(state: CareerSpyState) -> CareerSpyState:
    """
    දෙවන Node එක: Playwright (Headless Browser) පාවිච්චි කර JavaScript රන් වනකන් 
    ඉදලා, BeautifulSoup මඟින් HTML සුද්ද කර එකම String එකකට ගොනු කරයි.
    """
    print("\n🔍 Node 2: Scraping target career pages using Playwright...")
    urls = state.get("urls", [])
    all_clean_texts = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for url in urls:
            print(f"🌐 Playwright opening: {url}")
            try:
                page.goto(url, timeout=20000, wait_until="load")
                page.wait_for_timeout(3000) 
                
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    element.decompose()
                
                clean_text = soup.get_text(separator=' ', strip=True)
                
                if len(clean_text.strip()) > 100:
                    site_data = f"<source_site url='{url}'>\n{clean_text}\n</source_site>\n"
                    all_clean_texts.append(site_data)
                    print(f"✅ Successfully rendered & scraped {url}")
                else:
                    print(f"⚠️ Warning: Scraped text from {url} is too short.")
                    
            except Exception as e:
                print(f"❌ Playwright failed to scrape {url}: {e}")
                
        browser.close()
        
    combined_text = "\n".join(all_clean_texts)
    return {
        "current_raw_text": combined_text
    }

def ai_filter_node(state: CareerSpyState) -> CareerSpyState:
    """
    තෙවන Node එක: මුළු Text එකම එකම එක Request එකකින් Gemini වෙත යවා,
    Strictly Internships විතරක්ම පෙරලා ගනී.
    """
    print("\n🧠 Node 3: Analyzing text in ONE single request with Gemini...")
    raw_text = state.get("current_raw_text", "")
    
    if not raw_text.strip():
        print("📭 No text scraped to analyze.")
        return {"extracted_vacancies": []}
        
    prompt = f"""
    You are an expert HR Data Extraction Agent. Analyze the provided scraped content enclosed in <source_site> tags.
    
    CRITICAL INSTRUCTION: Your ONLY task is to extract job openings that are strictly for "Interns", "Internships", or "Trainees".
    
    STRICT FILTERING RULES:
    1. The position MUST be a learning/entry-level role (e.g., Intern,Trainee).
    2. Ensure the 'company_source' field matches the EXACT 'url' attribute specified in the corresponding <source_site> tag where the vacancy was found.
    3. If a website contains zero intern or trainee positions, do NOT extract anything from that site.

    Scraped Content:
    {raw_text}
    """
    
    json_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "job_title": {"type": "STRING"},
                "company_source": {"type": "STRING"},
                "skills": {"type": "ARRAY", "items": {"type": "STRING"}}
            },
            "required": ["job_title", "company_source", "skills"]
        }
    }
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # 💡 Free limit ස්ටේබල් වෙන්න Lite වෙනුවට Standard Flash එක දැම්මා මචං
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=json_schema,
                temperature=0.0
            ),
        )
        
        vacancies = json.loads(response.text)
        print(f"🎯 Gemini processed everything in 1 call and found {len(vacancies)} valid Internships!")
        return {"extracted_vacancies": vacancies}
        
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return {"extracted_vacancies": []}