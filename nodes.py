import requests
from bs4 import BeautifulSoup
import json
import re
from state import AgentState
from config import init_llm

# 💡 අලුත් google-genai Client එක ඉනිට් කරගනිමු
llm_node = init_llm()

def scraper_node(state: AgentState) -> dict:
    """ලැයිස්තුවේ ඇති ඊළඟ URL එක කියවා එහි ඇති අකුරු (Text) පමණක් ලබා ගනී."""
    print("\n--- 🕵️‍♂️ NODE: Scraping Career Page ---")
    
    remaining_urls = state["urls"]
    if not remaining_urls:
        return {"current_url": "", "raw_html_text": ""}
        
    target_url = remaining_urls[0]
    
    # වැරදිලා ලින්ක් එක වටේ බ්‍රැකට්ස් ආවොත් ඒවා පිරිසිදු කරමු
    target_url = target_url.strip("[]() ")
    if "](" in target_url:
        target_url = target_url.split("](")[0]
        
    print(f"Targeting Domain: {target_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # 💡 වෙබ් සයිට් එක සාමාන්‍ය පරිදි requests මඟින් ඩවුන්ලෝඩ් කරගනී
        response = requests.get(target_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # අනවශ්‍ය HTML ටැග්ස් අයින් කරමු
            for element in soup(["script", "style", "nav", "footer"]):
                element.decompose()
            
            clean_text = soup.get_text(separator=' ', strip=True)
            return {
                "current_url": target_url, 
                "raw_html_text": clean_text[:4000] # මුල් අකුරු 4000 පමණක් ගනී
            }
        else:
            print(f"⚠️ Failed to load page. Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Scraping Failed for {target_url}: {e}")
        
    return {"current_url": target_url, "raw_html_text": ""}


def ai_filter_node(state: AgentState) -> dict:
    """Gemini AI මඟින් වෙබ් අකුරු විශ්ලේෂණය කර ජොබ්ස් වෙන් කර ගනී."""
    print("--- 🧠 NODE: AI Analyzing Content via Gemini ---")
    
    raw_text = state.get("raw_html_text", "")
    current_company = state.get("current_url", "Unknown Company")
    
    if not raw_text:
        return {"extracted_vacancies": state.get("extracted_vacancies", [])}

    system_prompt = (
        "You are an expert HR Data Extraction Agent. Analyze the provided web text.\n"
        "Identify if there are active vacancies for 'Intern', 'AI', 'Machine Learning'.\n"
        "Return the output STRICTLY as a valid JSON array of objects. Do not include markdown formatting like ```json.\n"
        "If nothing matches, return an empty array [].\n\n"
        "Format:\n"
        "[\n"
        "  {\n"
        "    \"job_title\": \"Exact position name\",\n"
        "    \"skills\": [\"skill1\", \"skill2\"]\n"
        "  }\n"
        "]"
    )

    current_jobs = state.get("extracted_vacancies", [])
    
    try:
        # 💡 FIX: අලුත් SDK එකේ විදිහට models.generate_content හරහා කෝල් කරයි
        response = llm_node.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_prompt}\n\nWeb Content:\n{raw_text}"
        )
        
        # Markdown backticks සහ json ටැග්ස් පිරිසිදු කරමු
        clean_json = re.sub(r'^```json\s*|```$', '', response.text.strip(), flags=re.IGNORECASE)
        
        parsed_result = json.loads(clean_json)
        for job in parsed_result:
            job["company_source"] = current_company
            current_jobs.append(job)
            print(f"🎯 MATCH FOUND: {job['job_title']} at {current_company}")
            
    except Exception as e:
        print(f"❌ AI Extraction Error: {e}")
        
    return {"extracted_vacancies": current_jobs}