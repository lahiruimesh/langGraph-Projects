from langgraph.graph import StateGraph, END

from state import QuoteState
from nodes import (
    input_node,
    generate_quote_node,
    output_node
)

def build_graph():
    graph = StateGraph(QuoteState)

    graph.add_node("input", input_node)
    graph.add_node("generate_quote", generate_quote_node)
    graph.add_node("output", output_node)

    graph.set_entry_point("input")

    graph.add_edge("input", "generate_quote")
    graph.add_edge("generate_quote", "output")
    graph.add_edge("output", END)

    return graph.compile()