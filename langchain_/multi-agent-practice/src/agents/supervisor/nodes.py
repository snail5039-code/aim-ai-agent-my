from langchain.agents import create_agent
from model import llm
from agents.supervisor.prompts import supervisor_prompt, supervisor_guide_prompt
from agents.planning.tools import planning
from agents.research.tools import research
from agents.review.tools import review
from typing import TypedDict, Literal, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage, AnyMessage, AIMessage
from langgraph.graph.message import add_messages
from logger import logger

class SupervisorState(TypedDict):
    query: str
    messages: Annotated[list[AnyMessage], add_messages]
    selected_agents: list[str]
    supervisor_reason: str
    research_result: str
    planning_result: str
    review_result: str
    final_result: str


class SupervisorDecision(BaseModel):
    agents: list[Literal["research", "planning", "review"]] = Field(description="실행할 전문가 목록")
    reason: str = Field(description="전문가를 선택한 이유")

llm_with_supervisor_output = llm.with_structured_output(SupervisorDecision)

def supervisor_node(state: SupervisorState):
    query = state['query']
    messages = state.get("messages") or [HumanMessage(content=query)]
    
    result = llm_with_supervisor_output.invoke([
        SystemMessage(content=supervisor_prompt),
        *messages,
    ])

    logger.info(
        "[supervisor_node] selected_agents=%s reason=%s",
        result.agents,
        result.reason,
    )

    return {
        "selected_agents" : result.agents,
        "supervisor_reason" : result.reason
    }

def run_agents_node(state: SupervisorState):
    query = state["query"]
    selected_agents = state["selected_agents"]

    logger.info("[run_agents_node] start selected_agents=%s", selected_agents)

    if not selected_agents:
        logger.info("[run_agents_node] no agent selected, guide response")
        guide_result = llm.invoke([
            SystemMessage(content=supervisor_guide_prompt),
            HumanMessage(content=query),        
        ])
        return {
                "final_result" : guide_result.text,
                "messages": [AIMessage(content=guide_result.text)],
            }

    results = {}
    current_context = query

    for agent_name in selected_agents:
        print(f"\n[run_agents_node] 실행 에이전트: {agent_name}")
        logger.info("[run_agents_node] run agent=%s", agent_name)
        if agent_name == "research":
            research_result = research.invoke({"query": current_context})
            results["research_result"] = research_result
            current_context += f"\n\n[조사 결과]\n{research_result}"

        elif agent_name == "planning":
            planning_result = planning.invoke({"query": current_context})
            results["planning_result"] = planning_result
            current_context += f"\n\n[작성 결과]\n{planning_result}"

        elif agent_name == "review":
            review_result = review.invoke({"query": current_context})
            results["review_result"] = review_result
            current_context += f"\n\n[검토 결과]\n{review_result}"

    logger.info("[run_agents_node] final_result ready")
    results["final_result"] = results[f"{selected_agents[-1]}_result"]

    return {
            **results,
            "messages": [AIMessage(content=results["final_result"])],
        }