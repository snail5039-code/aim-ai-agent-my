from langchain.tools import tool
from agents.research.graph import research_graph

@tool
def research(query: str) -> str:
    """주제에 관한 최신 자료와 출처를 조사한다."""
    result = research_graph.invoke({"query" : query})
    return result["research_result"]