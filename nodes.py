import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import os
import json
from dotenv import load_dotenv
from state import CareerSpyState

load_dotenv()

# 1. Google GenAI Client එක සාදා ගැනීම (පැරණි google-generativeai එක නෙවෙයි මචං, මේක අලුත්ම එක)
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def scraper_node(state: CareerSpyState) -> CareerSpyState:
    """
    පළමු Node එක: සියලුම URLs පීරලා, BeautifulSoup පාවිච්චි කරලා 
    HTML කුණු සුද්ද කරලා Plain Text එකක් බවට පත් කරයි.
    """
    print("\n🔍 Node 1: Scraping target career pages...")
    urls = state.get("urls", [])
    all_clean_texts = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for url in urls:
        print(f"📡 Fetching: {url}")
        try:
            # 🚨 Challenge 10 විසඳුම: try-except දාලා තියෙන නිසා එක සයිට් එකක් ඩවුන් වුණත් කෝඩ් එක ක්‍රෑෂ් වෙන්නේ නැහැ
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 🧹 Challenge 5 විසඳුම: AI එකේ Tokens ඉතුරු කරන්න අනවශ්‍ය ටැග්ස් මකලා දානවා
                for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    element.decompose()
                
                clean_text = soup.get_text(separator=' ', strip=True)
                # සයිට් එකේ නමයි, අකුරු ටිකයි එකතු කරගන්නවා
                all_clean_texts.append(f"--- SOURCE URL: {url} ---\n{clean_text}\n")
            else:
                print(f"⚠️ Failed to load {url} (Status Code: {response.status_code})")
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            
    # මුළු සයිට් ලිස්ට් එකේම එකතු වුණු text ටික එකම string එකක් කරනවා
    combined_text = "\n".join(all_clean_texts)
    
    return {
        "current_raw_text": combined_text
    }

def ai_filter_node(state: CareerSpyState) -> CareerSpyState:
    """
    දෙවන Node එක: BeautifulSoup දුන් පිරිසිදු Text එක කියවා, 
    Gemini 2.5 Flash ලවා ජොබ්ස් තියෙනවාද කියා බලා Strict JSON එකක් ලබා ගනී.
    """
    print("\n🧠 Node 2: Analyzing text with Gemini 2.5 Flash...")
    raw_text = state.get("current_raw_text", "")
    
    if not raw_text.strip():
        print("📭 No text scraped to analyze.")
        return {"extracted_vacancies": []}
        
    # 📝 AI එකට දත්ත හරියටම ගන්න දෙන පට්ටම පවර්ෆුල් Prompt එක
    prompt = f"""
    You are an expert HR Data Extraction Agent. Analyze the provided scraped text from multiple career websites.
    Your task is to extract active job vacancies and internships specifically related to software engineering, QA, DevOps, data science, AI, and machine learning.
    
    For each vacancy found, extract:
    1. The job title.
    2. The exact company career page source URL where it was found (look at the 'SOURCE URL' headers in the text).
    3. A list of key technical skills mentioned.

    Scraped Content:
    {raw_text}
    """
    
    # 📐 Pydantic Scheme එකක් නැතුව වුණත් අලුත් google-genai SDK එකෙන් strict JSON ගන්න පුළුවන් ක්‍රමය මෙන්න:
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
        # Gemini 2.5 Flash කැඳවීම
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=json_schema,
                temperature=0.1 # උත්තරේ වෙනස් නොවී ස්ථිරව ලැබෙන්න 0.1ක් දෙනවා
            ),
        )
        
        # ලැබුණු JSON String එක පයිතන් List එකක් බවට හරවා ගැනීම
        vacancies = json.loads(response.text)
        print(f"🎯 Gemini found {len(vacancies)} potential job matches!")
        return {"extracted_vacancies": vacancies}
        
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return {"extracted_vacancies": []}