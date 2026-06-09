from langgraph.graph import StateGraph, END

from state import BMIState

from nodes import (
    input_node,
    calculate_bmi_node,
    validate_bmi_node,
    validation_router,
    bmi_router,
    underweight_node,
    normal_node,
    overweight_node
)


def build_graph():
    graph = StateGraph(BMIState)

    graph.add_node("input", input_node)
    graph.add_node("validate", validate_bmi_node)
    graph.add_node("calculate_bmi", calculate_bmi_node)

    graph.add_node("underweight", underweight_node)
    graph.add_node("normal", normal_node)
    graph.add_node("overweight", overweight_node)

    graph.set_entry_point("input")

    graph.add_edge("input", "validate")

    graph.add_conditional_edges(
        "validate",
        validation_router,
        {
            "valid": "calculate_bmi",
            "invalid": "input"
        }
    )

    graph.add_conditional_edges(
        "calculate_bmi",
        bmi_router,
        {
            "underweight": "underweight",
            "normal": "normal",
            "overweight": "overweight"
        }
    )

    graph.add_edge("underweight", END)
    graph.add_edge("normal", END)
    graph.add_edge("overweight", END)

    return graph.compile()