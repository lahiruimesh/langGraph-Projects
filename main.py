from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from state import AgentState
from nodes import scraper_node, ai_filter_node
from graph import route_next_url

# 1. සිතියම (Graph Architecture) නිර්මාණය කරමු
workflow = StateGraph(AgentState)

# 2. Nodes ටික එකතු කරමු
# AI එක කාර්ය බහුල වෙලා 503 හෝ Rate Limit ආවොත් බේරෙන්න ප්ලෑන් එකක් හදමු
ai_retry_policy = RetryPolicy(
    max_attempts=3,          # 💡 stop_after_attempt වෙනුවට (උපරිම 3 වතාවක් ට්‍රයි කරයි)
    initial_interval=2.0,    # 💡 wait_min වෙනුවට (පළමු පාර වැරදුණොත් තත්පර 2ක් බලයි)
    max_interval=10.0,       # 💡 wait_max වෙනුවට (උපරිම තත්පර 10ක් දක්වා ඉඳලා ට්‍රයි කරයි)
    backoff_factor=2.0       # වටෙන් වටේට පොඩි වෙලාවක් වැඩි කරමින් ට්‍රයි කරන්න (Exponential Backoff)
)
# Nodes එකතු කරද්දී අර පොලිසිය ඇතුළත් කරමු
workflow.add_node("scraper_agent", scraper_node)

# 💡 FIX: AI එකට විතරක් Retry Policy එකක් මෙහෙම බැන්දාම සර්වර් බිසී වුණත් ඔටෝ ට්‍රයි කරනවා
workflow.add_node("ai_analyst", ai_filter_node, retry=ai_retry_policy)

# 3. පාරවල් (Edges) සම්බන්ධ කරමු
workflow.add_edge(START, "scraper_agent")        # ආරම්භයේ සිට කෙලින්ම Scraper වෙත
workflow.add_edge("scraper_agent", "ai_analyst")  # Scrape කළ පසු AI වෙත

# 4. Conditional Edge (කැරකෙන පාර) එකතු කරමු
workflow.add_conditional_edges(
    "ai_analyst",
    route_next_url,
    {
        "continue": "scraper_agent", # තව URL තිබේ නම් නැවත Scraper වෙත යන්න (Loop)
        "end": END                   # URL ඉවර නම් වැඩේ අවසන් කරන්න
    }
)

# 5. Graph එක සම්පූර්ණ (Compile) කරමු
career_spy_app = workflow.compile()

# 🚀 ටෙස්ට් කරලා බලන්න Run කරන කොටස
if __name__ == "__main__":
    print("🚀 Starting CareerSpy AI Modular Agent...")
    
    # ඔයාට කැමති ටෙස්ට් URL 2ක් හෝ 3ක් මෙතනට දෙන්න මචං
    test_input = {
        "urls": [
            "https://cmlinsight.com/careers", 
            "https://kaizens.co.uk/careers"
        ]
    }
    
    # සිස්ටම් එක Invoke කරමු
    final_state = career_spy_app.invoke(test_input)
    
    print("\n================ 📊 FINAL EXTRACTION REPORT ================")
    import json
    # final_state එක ඇතුළේ තියෙන ජොබ්ස් ටික ලස්සනට පෙන්වමු
    print(json.dumps(final_state.get("extracted_vacancies", []), indent=2))
    print("============================================================")