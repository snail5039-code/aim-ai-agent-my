from langchain.tools import tool
from agents.review.graph import review_graph

@tool
def review(query: str) -> str:
    """보고서를 검토하고 수정 사항이나 승인 여부를 반환한다."""
    result = review_graph.invoke({"query" : query})
    return result["review_result"]