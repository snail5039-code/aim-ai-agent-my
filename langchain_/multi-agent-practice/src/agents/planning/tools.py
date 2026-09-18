from langchain.tools import tool
from agents.planning.graph import planning_graph

@tool
def planning(query: str) -> str:
    """조사 결과를 바탕으로 보고서를 작성한다."""
    result = planning_graph.invoke({"query" : query})
    return result["planning_result"]