import operator
from model import llm
from typing import TypedDict, Annotated, Literal
from pydantic import BaseModel, Field
from langgraph.types import Send
from agents.planning.prompts import planning_create_plan_prompt, planning_merge_prompt, planning_worker_prompt, planning_reflect_prompt
from logger import logger
from langchain_core.messages import HumanMessage, SystemMessage

class PlanningState(TypedDict):
    query: str
    tasks: list
    results: Annotated[list, operator.add]
    planning_result: str
    planning_feedback: str
    planning_router: str
    planning_iteration: int

class WorkerState(TypedDict):
    query: str
    task_id: int
    title: str
    description: str

class AnalysisTask(BaseModel):
    title: str = Field(description="분석 항목 제목")
    description: str = Field(description="분석할 내용")


class AnalysisPlan(BaseModel):
    tasks: list[AnalysisTask] = Field(description="보고서 작성에 필요한 분석 작업")

class PlanningReflection(BaseModel):
    planning_router: Literal["pass", "revise"] = Field(description="검토 후 이동할 다음 경로")
    planning_feedback: str = Field(description="다음 병합 단계에 반영할 구체적인 피드백")

reflector = llm.with_structured_output(PlanningReflection)

MAX_PLANNING_ITERATIONS = 2


def planning_create_plan_node(state: PlanningState):
    """사용자 요청을 분석하여 필요한 작업을 계획한다."""
    planner = llm.with_structured_output(AnalysisPlan)
    plan = planner.invoke(
        planning_create_plan_prompt.format(query=state["query"])
    )
    logger.info("[planning_create_plan_node] tasks=%s", len(plan.tasks))
    return {"tasks": plan.tasks}


def planning_assign_workers_node(state: PlanningState):
    """계획된 작업마다 Worker를 생성한다."""
    workers = [
        Send(
            "planning_worker_node",
            {
                "query": state["query"],
                "task_id": task_id,
                "title": task.title,
                "description": task.description,
            },
        )
        for task_id, task in enumerate(state["tasks"])
    ]

    logger.info("[planning_assign_workers_node] workers=%s", len(workers))
    return workers


def planning_worker_node(state: WorkerState):
    result = llm.invoke(
        planning_worker_prompt.format(
            query=state["query"],
            title=state["title"],
            description=state["description"]
        )
    )
    print(f"[planning_worker_node] '{state['title']}' 완료")
    logger.info("[planning_worker_node] '%s' 완료", state["title"])
    return {
        "results": [{
            "task_id": state["task_id"],
            "title": state["title"],
            "content": result.text,
        }]
    }


def planning_merge_node(state: PlanningState):
    sorted_results = sorted(state["results"], key=lambda item: item["task_id"])
    all_results = "\n\n".join(
        f"### {item['title']}\n{item['content']}" for item in sorted_results
    )
    planning_feedback = state.get("planning_feedback", "")

    result = llm.invoke(
        planning_merge_prompt.format(
            query=state["query"],
            all_results=all_results,
            planning_feedback=planning_feedback
        )
    )
    logger.info("[planning_merge_node] 최종 보고서 병합 완료")
    return {"planning_result": result.text}

def planning_reflect_node(state: PlanningState):
    query = state["query"]
    tasks = state["tasks"]
    results = state["results"]
    planning_result = state["planning_result"]

    result = reflector.invoke([
        SystemMessage(content=planning_reflect_prompt),
        HumanMessage(content=f"""
        사용자 요청:
        {query}
        작업 목록:
        {tasks}
        worker 작성 결과:
        {results}
        최종 보고서:
        {planning_result}
        """),
    ])

    print("[planning_reflect_node] 기획 결과 검토 완료")
    logger.info("[planning_reflect_node] 기획 결과 검토 완료")
    return {
        "planning_router": result.planning_router,
        "planning_feedback": result.planning_feedback,
        "planning_iteration": state.get("planning_iteration", 0) + 1,
    }

def route_planning_reflect(state: PlanningState):
    if state.get("planning_iteration", 0) >= MAX_PLANNING_ITERATIONS:
        print("[route_planning_reflect] 최대 반복 도달, 기획 종료")
        logger.info("[route_planning_reflect] max iterations, pass")
        return "pass"        

    planning_router = state["planning_router"]

    print(f"[route_planning_reflect] 다음 경로: {planning_router}")
    logger.info("[route_planning_reflect] route=%s", planning_router)
    return planning_router
