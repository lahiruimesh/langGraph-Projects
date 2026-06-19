from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import os
import json
from dotenv import load_dotenv
from state import CareerSpyState

load_dotenv()

# 1. Google GenAI Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def scraper_node(state: CareerSpyState) -> CareerSpyState:
    """
    පළමු Node එක: Playwright (Headless Browser) පාවිච්චි කර JavaScript රන් වනකන් 
    ඉදලා, BeautifulSoup මඟින් HTML සුද්ද කර එකම String එකකට ගොනු කරයි.
    """
    print("\n🔍 Node 1: Scraping target career pages using Playwright...")
    urls = state.get("urls", [])
    all_clean_texts = []
    
    # 🔄 Playwright සන්දර්භය ආරම්භ කිරීම
    with sync_playwright() as p:
        # headless=True නිසා බැක්ග්‍රවුන්ඩ් එකේ හොරෙන්ම බ්‍රවුසර් එක රන් වෙන්නේ මචං
        browser = p.chromium.launch(headless=True)
        # සැබෑ මනුස්සයෙක් වගේ පේන්න User Agent එකක් දානවා (Anti-bot block නොවෙන්න)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for url in urls:
            print(f"🌐 Playwright opening: {url}")
            try:
                # සයිට් එකට යනවා (තත්පර 20ක Timeout එකක් සමඟ)
                page.goto(url, timeout=20000, wait_until="load")
                
                # 💡 JS Heavy සයිට් වලට තත්පර 3ක් ඉන්න දෙනවා ජොබ්ස් ටික screen එකට අදිනකන්
                page.wait_for_timeout(3000) 
                
                # සම්පූර්ණයෙන්ම Render වුණු HTML එක ගන්නවා
                html_content = page.content()
                
                # BeautifulSoup පාවිච්චි කරලා කුණු සුද්ද කිරීම
                soup = BeautifulSoup(html_content, 'html.parser')
                for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    element.decompose()
                
                clean_text = soup.get_text(separator=' ', strip=True)
                
                # Gemini එකට සයිට් වෙන් කරලා අඳුනගන්න Tags දමා එකතු කිරීම
                if len(clean_text.strip()) > 100:
                    site_data = f"<source_site url='{url}'>\n{clean_text}\n</source_site>\n"
                    all_clean_texts.append(site_data)
                    print(f"✅ Successfully rendered & scraped {url}")
                else:
                    print(f"⚠️ Warning: Scraped text from {url} is too short.")
                    
            except Exception as e:
                print(f"❌ Playwright failed to scrape {url}: {e}")
                
        browser.close() # වැඩේ ඉවර වුණාම බ්‍රවුසර් එක වහනවා
        
    combined_text = "\n".join(all_clean_texts)
    return {
        "current_raw_text": combined_text
    }

def ai_filter_node(state: CareerSpyState) -> CareerSpyState:
    """
    දෙවන Node එක: මුළු Text එකම එකම එක Request එකකින් Gemini 2.5 Flash වෙත යවා,
    Strictly Internships විතරක්ම පෙරලා ගනී.
    """
    print("\n🧠 Node 2: Analyzing text in ONE single request with Gemini 2.5 Flash...")
    raw_text = state.get("current_raw_text", "")
    
    if not raw_text.strip():
        print("📭 No text scraped to analyze.")
        return {"extracted_vacancies": []}
        
    prompt = f"""
    You are an expert HR Data Extraction Agent. Analyze the provided scraped content enclosed in <source_site> tags.
    
    CRITICAL INSTRUCTION: Your ONLY task is to extract job openings that are strictly for "Interns", "Internships", or "Trainees".
    
    STRICT FILTERING RULES:
    1. The position MUST be a learning/entry-level role (e.g., Intern, Software Intern, Trainee, Management Trainee).
    2. Do NOT extract permanent, full-time, mid-level, associate, or senior positions. For example, roles like "Senior IFS Software Engineer", "Associate Consultant", "Machine Learning Engineer", or "Software Engineer" are strictly FORBIDDEN.
    3. Ensure the 'company_source' field matches the EXACT 'url' attribute specified in the corresponding <source_site> tag where the vacancy was found.
    4. If a website contains zero intern or trainee positions, do NOT extract anything from that site.

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
            model='gemini-2.5-flash-lite',
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