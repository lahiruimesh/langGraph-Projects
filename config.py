import os
from dotenv import load_dotenv
from google import genai # 👈 අලුත් නිල SDK එක ඉම්පෝර්ට් කළා

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def init_llm():
    """අලුත්ම google-genai Client එක සක්‍රිය කර ආපසු ලබා දේ."""
    if not GOOGLE_API_KEY:
        raise ValueError("❌ Error: GOOGLE_API_KEY not found in .env file!")
        
    # අලුත් ක්‍රමයට Client එකක් ඇතුළට API Key එක පාස් කරනවා
    return genai.Client(api_key=GOOGLE_API_KEY)