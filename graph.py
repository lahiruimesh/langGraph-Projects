from langgraph.graph import StateGraph, END

from state import BMIState
from nodes import (
    input_node,
    calculate_bmi_node,
    result_node
)


def build_graph():
    graph = StateGraph(BMIState)

    graph.add_node("input", input_node)
    graph.add_node("calculate_bmi", calculate_bmi_node)
    graph.add_node("result", result_node)

    graph.set_entry_point("input")

    graph.add_edge("input", "calculate_bmi")
    graph.add_edge("calculate_bmi", "result")
    graph.add_edge("result", END)

    return graph.compile()