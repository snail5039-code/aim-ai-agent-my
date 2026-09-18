from model import search_llm, llm
from agents.research.prompts import research_plan_prompt, research_summarize_prompt, research_execute_prompt, research_reflect_prompt
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from logger import logger

class ResearchState(TypedDict):
    query: str
    research_plan: str
    research_raw: str
    research_result: str
    research_feedback: str
    research_iteration: int
    research_router: str

class ResearchReflection(BaseModel):
    research_router: Literal["pass", "replan", "research_more", "resummarize"] = Field(description="검토 후 이동할 다음 경로")
    research_feedback: str = Field(description="다음 단계에 반영할 구체적인 피드백")

reflector = llm.with_structured_output(ResearchReflection)

MAX_RESEARCH_ITERATIONS = 2

def research_plan_node(state: ResearchState):
    query = state['query']
    result = llm.invoke([
        SystemMessage(content=research_plan_prompt),
        HumanMessage(content=query),
    ])
    print("[research_plan_node] 조사 계획 수립 완료")
    logger.info("[research_plan_node] 조사 계획 수립 완료")
    return {"research_plan" : result.text}

def research_execute_node(state: ResearchState):
    query = state['query']
    result_plan = state['research_plan']

    result = search_llm.invoke([
        SystemMessage(content=research_execute_prompt),
        HumanMessage(content=f"""
        사용자 요청 : {query}
        조사 계획 : {result_plan}
        """),
    ])
    print("[research_execute_node] 검색 조사 완료")
    logger.info("[research_execute_node] 검색 조사 완료")
    return {"research_raw" : result.text}

def research_summarize_node(state: ResearchState):
    query = state['query']
    result_plan = state['research_plan']
    research_raw = state["research_raw"]

    result = search_llm.invoke([
        SystemMessage(content=research_summarize_prompt),
        HumanMessage(content=f"""
        사용자 요청 : {query}
        조사 계획 : {result_plan}
        조사 결과 : {research_raw}
        """),
    ])
    print("[research_summarize_node] 조사 결과 정리 완료\n")
    logger.info("[research_summarize_node] 조사 결과 정리 완료\n")
    return {"research_result" : result.text}    

def research_reflect_node(state: ResearchState):
    query = state["query"]
    research_plan = state["research_plan"]
    research_raw = state["research_raw"]
    research_result = state["research_result"]

    result = reflector.invoke([
        SystemMessage(content=research_reflect_prompt),
        HumanMessage(content=f"""
        사용자 요청:
        {query}
        조사 계획:
        {research_plan}
        조사 원자료:
        {research_raw}
        최종 요약:
        {research_result}
        """),
    ])

    print("[research_reflect_node] 조사 결과 검토 완료")
    logger.info("[research_reflect_node] 조사 결과 검토 완료")
    return {
        "research_router": result.research_router,
        "research_feedback": result.research_feedback,
        "research_iteration": state.get("research_iteration", 0) + 1,
    }

def route_research_reflect(state: ResearchState):
    if state.get("research_iteration", 0) >= MAX_RESEARCH_ITERATIONS:
        print("[route_research_reflect] 최대 반복 도달, 조사 종료")
        logger.info("[route_research_reflect] max iterations, pass")
        return "pass"        

    research_router = state["research_router"]

    print(f"[route_research_reflect] 다음 경로: {research_router}")
    logger.info("[route_research_reflect] route=%s", research_router)
    return research_router
