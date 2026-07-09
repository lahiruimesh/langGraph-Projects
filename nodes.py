from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import os
import json
import gspread
import time  # 💡 Retry logic එකට time සෙට් කළා මචං
from dotenv import load_dotenv
from state import CareerSpyState
from search_utils import get_google_search_urls  # Import the Google search helper.

load_dotenv()

# Google GenAI client.
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def fetch_urls_node(state: CareerSpyState) -> CareerSpyState:
    """
    First node: combine URLs from the Google Sheet and live Google Search results
    into a unique list.
    """
    print("\n==================================================")
    print("Fetching target URLs from multiple sources...")
    combined_urls = []
    
    # 1. Read existing links from the Google Sheet.
    try:
        gc = gspread.service_account(filename="credentials.json")
        sheet = gc.open_by_key("1PhWmYoRpxE7Cs-8BzE1FEkcxml3aiwuymRLSSRf9UMI").sheet1
        sheet_urls = sheet.col_values(1)[1:]  # Skip the header row.
        print(f"Found {len(sheet_urls)} URLs inside the Google Sheet.")
        combined_urls.extend(sheet_urls)
    except Exception as e:
        print(f"❌ Error fetching URLs from Google Sheet: {e}")

    # 2. Fetch fresh links from live Google Search via Serper.
    search_urls = get_google_search_urls()
    combined_urls.extend(search_urls)
    
    # 3. Deduplicate the combined list.
    unique_urls = list(set(combined_urls))
    
    print(f"Total unique URLs to scan today: {len(unique_urls)}")
    print("==================================================")
    
    return {"urls": unique_urls}

def scraper_node(state: CareerSpyState) -> CareerSpyState:
    """
    Second node: use Playwright to render JavaScript-heavy pages, then clean the
    HTML with BeautifulSoup and combine the text into a single string.
    """
    print("\nNode 2: Scraping target career pages using Playwright...")
    urls = state.get("urls", [])
    all_clean_texts = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for url in urls:
            print(f"Playwright opening: {url}")
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
                    print(f"Successfully rendered and scraped {url}")
                else:
                    print(f"Warning: scraped text from {url} is too short.")
                    
            except Exception as e:
                print(f"❌ Playwright failed to scrape {url}: {e}")
                
        browser.close()
        
    combined_text = "\n".join(all_clean_texts)
    return {
        "current_raw_text": combined_text
    }

def ai_filter_node(state: CareerSpyState) -> CareerSpyState:
    """
    Third node: send the full text to Gemini in a single request and extract only
    strictly relevant internship opportunities. Includes strong error-handling and retries.
    """
    print("\nNode 3: Analyzing text in one request with Gemini...")
    raw_text = state.get("current_raw_text", "")
    
    if not raw_text.strip():
        print("No scraped text available for analysis.")
        return {"extracted_vacancies": []}
        
    prompt = f"""
    You are an expert HR Data Extraction Agent specializing in the Technology and Software Engineering sectors. 
    Analyze the provided scraped content enclosed in <source_site> tags.
    
    CRITICAL INSTRUCTION: Your ONLY task is to extract job openings that are strictly for IT/Software Industry "Interns", "Internships", or "Trainees".
    
    STRICT FILTERING RULES:
    1. The position MUST be a learning/entry-level role (e.g., Intern, Trainee) AND MUST belong strictly to the Information Technology (IT) / Software Engineering domain.
    
    2. ALLOWED TECH DOMAINS (EXTRACT THESE):
       - Software Engineering / Web Development (Fullstack, Backend, Frontend, React, .NET, Python, Node, PHP, Laravel, Java, etc.)
       - AI / Machine Learning / Data Science / Data Analytics / Data Engineer
       
    3. STRICTLY FORBIDDEN DOMAINS (DO NOT EXTRACT THESE):
       - Completely ignore non-tech roles even if they have "Intern" or "Trainee" in the title.
       - Strictly FORBIDDEN: Finance, Accounting, Management Trainee, Human Resources (HR), Marketing, Sales, Business Development, Logistics, Procurement, Administrative, Secretarial, Operations, Industrial Engineering, or Mechanical roles. (e.g., Do NOT extract "Finance Intern", "Marketing Intern", or "Management Trainee").

    4. Ensure the 'company_source' field matches the EXACT 'url' attribute specified in the corresponding <source_site> tag where the vacancy was found.
    
    5. If a website contains zero valid IT/Tech intern or trainee positions, do NOT extract anything from that site.

    ⚠️ JSON INTEGRITY RULES:
    - Ensure ALL output strings are safe for standard JSON parsing.
    - Remove any unescaped double quotes, control characters, or trailing commas within objects.

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
    
    # 💡 Smart Retry Loop (503 සර්වර් ඩවුන් හෝ Delimiter බග් එකක් ආවොත් බේරෙන්න)
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
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
            
            # 💡 Clean JSON String (පයිතන් වලට කියවන්න බැරි වෙන අමුතු කොටස් පිරිසිදු කිරීම)
            clean_response_text = response.text.strip()
            
            # පයිතන් JSON ලෝඩර් එකට ඔරොත්තු දෙන විදිහට parsing කිරීම
            vacancies = json.loads(clean_response_text)
            print(f"✅ Gemini processed everything successfully on attempt {attempt + 1} and found {len(vacancies)} valid internships!")
            return {"extracted_vacancies": vacancies}
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Attempt {attempt + 1}/{max_retries} failed with error: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("❌ All Gemini extraction attempts failed.")
                return {"extracted_vacancies": []}