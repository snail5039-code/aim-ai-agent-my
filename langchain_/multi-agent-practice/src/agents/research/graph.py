from langgraph.graph import StateGraph, START, END
from agents.research.nodes import ResearchState, research_execute_node, research_plan_node, research_summarize_node, research_reflect_node, route_research_reflect

builder = StateGraph(ResearchState)

builder.add_node("research_plan_node", research_plan_node)
builder.add_node("research_execute_node", research_execute_node)
builder.add_node("research_summarize_node", research_summarize_node)
builder.add_node("research_reflect_node", research_reflect_node)

builder.add_edge(START, "research_plan_node")
builder.add_edge("research_plan_node", "research_execute_node")
builder.add_edge("research_execute_node", "research_summarize_node")
builder.add_edge("research_summarize_node", "research_reflect_node")
builder.add_conditional_edges(
    "research_reflect_node",
    route_research_reflect,
    {
        "pass": END,
        "replan": "research_plan_node",
        "research_more": "research_execute_node",
        "resummarize": "research_summarize_node",
    }
)

research_graph = builder.compile()