from langgraph.graph import StateGraph, START, END
from agents.supervisor.nodes import SupervisorState, supervisor_node, run_agents_node
from langgraph.checkpoint.memory import InMemorySaver


builder = StateGraph(SupervisorState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("run_agents", run_agents_node)

builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "run_agents")
builder.add_edge("run_agents", END)

supervisor_graph = builder.compile(checkpointer=InMemorySaver())