from state import AgentState
from langgraph.graph import END

def route_next_url(state: AgentState) -> str:
    """URL ලැයිස්තුව පරීක්ෂා කර ඊළඟ පියවර තීරණය කරයි (Looping Edge)."""
    print("--- 🛣️ EDGE: Routing Evaluation ---")
    
    # ස්කෑන් කරපු URL එක ලැයිස්තුවෙන් අයින් කරමු
    urls_list = state["urls"]
    current_scanned = state.get("current_url")
    
    if current_scanned in urls_list:
        urls_list.remove(current_scanned)
        
    # තවත් URL ඉතිරි වී ඇත්නම් නැවත Scraper වෙත යවන්න, නැතහොත් අවසන් කරන්න
    if len(urls_list) > 0:
        print(f"Remaining URLs to scan: {len(urls_list)}. Looping back...")
        return "continue"
        
    print("🏁 All URLs evaluated successfully. Exiting Graph.")
    return "end"