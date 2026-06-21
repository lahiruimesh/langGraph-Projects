from langgraph.graph import StateGraph, END
from state import CareerSpyState
from nodes import scraper_node, ai_filter_node, fetch_urls_node

def build_graph():
    """
    Build the full LangGraph workflow in a single place.
    """
    # 1. Initialize the graph with the shared state definition.
    workflow = StateGraph(CareerSpyState)
    
    # 2. Register the nodes used by the workflow.
    workflow.add_node("fetch_urls_agent", fetch_urls_node)
    workflow.add_node("scraper_agent", scraper_node)
    workflow.add_node("ai_analyst_agent", ai_filter_node)
    
    # 3. Define the execution flow between nodes.
    workflow.set_entry_point("fetch_urls_agent")          # Start with the URL fetcher.
    workflow.add_edge("fetch_urls_agent", "scraper_agent") # Then scrape the pages.
    workflow.add_edge("scraper_agent", "ai_analyst_agent") # Then analyze the content.
    workflow.add_edge("ai_analyst_agent", END)            # End after analysis.
    
    # 4. Compile the graph into an executable app.
    return workflow.compile()