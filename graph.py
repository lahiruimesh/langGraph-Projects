from langgraph.graph import StateGraph, END
from state import CareerSpyState
from nodes import scraper_node, ai_filter_node

def build_graph():
    """
    ඔයා යෝජනා කළ පරිදි මුළු LangGraph Workflow එකම 
    වෙන් කර හුදෙකලාව බිල්ඩ් කරන ප්‍රධාන Function එක.
    """
    # 1. අපේ State එක සමඟ Graph එක Initialize කර ගැනීම
    workflow = StateGraph(CareerSpyState)
    
    # 2. අපේ Nodes දෙක Graph එකට ඇතුළත් කිරීම
    workflow.add_node("scraper_agent", scraper_node)
    workflow.add_node("ai_analyst_agent", ai_filter_node)
    
    # 3. Graph එක ඇතුළේ දත්ත ගලාගෙන යන පාරවල් (Edges) සකස් කිරීම
    workflow.set_entry_point("scraper_agent")             # මුලින්ම යන්නේ Scraper එකට
    workflow.add_edge("scraper_agent", "ai_analyst_agent") # එතනින් කෙලින්ම AI එකට
    workflow.add_edge("ai_analyst_agent", END)            # AI එකෙන් පස්සේ Graph එක ඉවරයි
    
    # 4. Graph එක Compile කරලා ක්‍රියාත්මක කළ හැකි App එකක් විදිහට Return කිරීම
    return workflow.compile()