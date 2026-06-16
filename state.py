from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    """LangGraph එකේ හැම පියවරකදීම මතකය රඳවා තබා ගන්නා රාමුව."""
    urls: List[str]               # ස්කෑන් කිරීමට ඉතිරිව ඇති URL ලැයිස්තුව
    current_url: str              # දැනට ස්කෑන් කරමින් පවතින URL එක
    raw_html_text: str            # සයිට් එකෙන් ඇදලා ගත්තු Raw Text එක
    extracted_vacancies: List[Dict[str, Any]] # Gemini එකෙන් හොයාගන්නා ජොබ්ස්