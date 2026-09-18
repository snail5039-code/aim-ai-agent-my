from langgraph.graph import StateGraph, START, END
from agents.planning.nodes import (
    PlanningState,
    planning_create_plan_node,
    planning_assign_workers_node,
    planning_worker_node,
    planning_merge_node,
    planning_reflect_node,
    route_planning_reflect
)

builder = StateGraph(PlanningState)

builder.add_node("planning_create_plan_node", planning_create_plan_node)
builder.add_node("planning_worker_node", planning_worker_node)
builder.add_node("planning_merge_node", planning_merge_node)
builder.add_node("planning_reflect_node", planning_reflect_node)

builder.add_edge(START, "planning_create_plan_node")
builder.add_conditional_edges(
    "planning_create_plan_node",
    planning_assign_workers_node,
    ["planning_worker_node"]
)
builder.add_edge("planning_worker_node", "planning_merge_node")
builder.add_edge("planning_merge_node", "planning_reflect_node")
builder.add_conditional_edges(
    "planning_reflect_node",
    route_planning_reflect,
    {
        "pass" : END,
        "revise" : "planning_merge_node"
    }
)

planning_graph = builder.compile()