from typing import TypedDict, List, Dict, Any

class CareerSpyState(TypedDict):
    """
    Shared state passed between LangGraph nodes.
    """
    urls: List[str]                       # URLs to scan.
    current_url_index: int                # Index of the URL currently being scanned.
    current_raw_text: str                 # Plain text extracted by BeautifulSoup.
    extracted_vacancies: List[Dict[str, Any]]  # Jobs extracted by Gemini AI.