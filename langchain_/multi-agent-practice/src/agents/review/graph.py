from langgraph.graph import StateGraph, START, END
from agents.review.nodes import ReviewState, review_generate_node, review_evaluate_node, review_optimize_node, should_continue_review 

builder = StateGraph(ReviewState)

builder.add_node("review_generate_node", review_generate_node)
builder.add_node("review_evaluate_node", review_evaluate_node)
builder.add_node("review_optimize_node", review_optimize_node)

builder.add_edge(START, "review_generate_node")
builder.add_edge("review_generate_node", "review_evaluate_node")
builder.add_conditional_edges(
    "review_evaluate_node",
    should_continue_review,
    {"end": END, "fail": "review_optimize_node"},
)
builder.add_edge("review_optimize_node", "review_generate_node")

review_graph = builder.compile()