import operator
from model import llm
from agents.review.prompts import review_generate_prompt, review_initial_prompt, review_evaluate_prompt, review_optimize_prompt
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from logger import logger

class CriterionResult(BaseModel):
    score: int = Field(description="1~10 점수", ge=1, le=10)
    reason: str = Field(description="점수 근거 (1문장)")


class EvaluationResult(BaseModel):
    accuracy: CriterionResult = Field(description="사실과 근거가 정확한지 평가")
    completeness: CriterionResult = Field(description="요청한 내용과 필요한 항목이 빠짐없이 들어갔는지 평가")
    realism: CriterionResult = Field(description="제안과 계획이 현실적으로 실행 가능한지 평가")
    structure: CriterionResult = Field(description="보고서 구조와 흐름이 읽기 좋은지 평가")
    summary: str = Field(description="전체 평가 요약 (1~2문장)")

class ReviewState(TypedDict):
    query: str
    review_result: str
    evaluation: dict  
    iteration: int
    history: Annotated[list, operator.add] 

MAX_ITERATIONS = 4
PASS_THRESHOLD = 8
EVALUATION_CRITERIA = ("accuracy", "completeness", "realism", "structure")
evaluator = llm.with_structured_output(EvaluationResult)


def review_generate_node(state: ReviewState):
    """초기 보고서를 준비하거나, 이전 개선 지시를 반영해 보고서를 다시 작성한다."""
    query = state["query"]
    history = state.get("history", [])

    if history:
        last = history[-1]
        prompt = (
            review_generate_prompt.format(
                query = query,
                review_result = state["review_result"],
                improvement = last["improvement"]
            )
        )
    else:
        prompt = review_initial_prompt.format(query = query)

    response = llm.invoke(prompt)
    print("\n[review_generate_node] 보고서 생성/수정 완료")
    logger.info("[review_generate_node] 보고서 생성/수정 완료")
    return {"review_result": response.text}


def review_evaluate_node(state: ReviewState):
    """보고서를 기준표에 따라 평가하고 점수와 피드백을 구조화해서 반환한다."""
    review_result = state["review_result"]
    system = SystemMessage(content= review_evaluate_prompt)
    result = evaluator.invoke([
        system,
        HumanMessage(content=f"<review_result>\n{review_result}\n</review_result>"),
    ])

    evaluation = result.model_dump()
    evaluation["overall_pass"] = all(
        evaluation[name]["score"] >= PASS_THRESHOLD
        for name in EVALUATION_CRITERIA
    )
    print("[review_evaluate_node] 보고서 평가 완료")
    logger.info(
        "[review_evaluate_node] iteration=%s overall_pass=%s",
        state.get("iteration", 0) + 1,
        evaluation["overall_pass"],
    )
    return {
        "evaluation": evaluation,
        "iteration": state.get("iteration", 0) + 1,
    }


def review_optimize_node(state: ReviewState):
    """미달 항목의 평가 근거를 바탕으로 다음 생성에 사용할 수정 지시를 만든다."""
    evaluation = state["evaluation"]
    query = state["query"]
    failed = [
        (name, evaluation[name])
        for name in EVALUATION_CRITERIA
        if evaluation[name]["score"] < PASS_THRESHOLD
    ]
    failed_items = [
        f"- {name} ({criterion['score']}점): {criterion['reason']}"
        for name, criterion in failed
    ]

    response = llm.invoke(
        review_optimize_prompt.format(
            query = state["query"],
            review_result = state["review_result"],
            failed_items = "\n".join(failed_items)
        )
    )
    print("[review_optimize_node] 개선 지시 생성 완료")
    logger.info("[review_optimize_node] failed_items=%s", len(failed_items))
    return {
        "history": [{
            "query": query,
            "evaluation": evaluation,
            "improvement": response.text,
        }],
    }


def should_continue_review(state: ReviewState):
    """평가 결과와 반복 횟수를 보고 개선을 계속할지 종료할지 결정한다."""
    if state["evaluation"]["overall_pass"]:
        print("[should_continue_review] 기준 통과, 검토 종료")
        logger.info("[should_continue_review] end: overall_pass")
        return "end"
    if state["iteration"] >= MAX_ITERATIONS:
        print("[should_continue_review] 최대 반복 도달, 검토 종료")
        logger.info("[should_continue_review] end: max_iterations")
        return "end"  # 상한 도달 시에도 종료
    print("[should_continue_review] 기준 미달, 개선 계속")
    logger.info("[should_continue_review] continue")
    return "fail"
