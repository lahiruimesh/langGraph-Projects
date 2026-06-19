from typing import TypedDict, List, Dict, Any

class CareerSpyState(TypedDict):
    """
    LangGraph එක ඇතුළත දත්ත රඳවා තබා ගන්නා සහ Nodes අතර 
    දත්ත හුවමාරු කරගන්නා ප්‍රධාන State එක.
    """
    urls: List[str]                       # ස්කෑන් කිරීමට ඇති මුළු URL ලැයිස්තුව
    current_url_index: int                # දැනට ස්කෑන් වන URL එකේ දර්ශකය (Index)
    current_raw_text: str                 # BeautifulSoup මඟින් සුද්ද කරගත් Plain Text එක
    extracted_vacancies: List[Dict[str, Any]]  # Gemini AI එකෙන් වෙන් කරගත් ජොබ්ස් ලැයිස්තුව