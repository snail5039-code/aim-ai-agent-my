from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallRequest, wrap_tool_call
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import interrupt
from pydantic import BaseModel, ConfigDict, Field

from data_store import read_data, save_data


class CardLookupArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    card_id: str | None = Field(default=None, min_length=1)


class CardChangeArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    card_id: str = Field(min_length=1)


TOOL_SCHEMAS = {
    "lookup_cards": CardLookupArgs,
    "report_card_lost": CardChangeArgs,
    "cancel_card_loss": CardChangeArgs,
}


def find_card(data, card_id, owner_id):
    card = next(
        (c for c in data["cards"]
         if c["card_id"] == card_id and c["owner_id"] == owner_id),
        None,
    )
    if card is None:
        raise ValueError("본인 소유의 카드 ID인지 확인해 주세요.")
    return card


def check_card_change(data, name, card_id, owner_id):
    card = find_card(data, card_id, owner_id)
    if name == "report_card_lost" and card["status"] not in ("active", "locked"):
        raise ValueError("사용 가능하거나 일시 잠금된 카드만 분실신고할 수 있습니다.")
    if name == "cancel_card_loss" and card["status"] != "lost":
        raise ValueError("분실신고된 카드만 분실신고를 취소할 수 있습니다.")
    return card


@tool
def lookup_cards(runtime: ToolRuntime[dict], card_id: str | None = None) -> list[dict]:
    """본인 카드의 ID, 이름, 종류, 상태를 조회한다.

    Args:
        runtime: 실행 시 주입되는 정보. context의 owner_id로 사용자를 확인한다.
        card_id: 조회할 본인 카드 ID. 생략하면 본인 전체 카드를 조회한다.
    """
    data = read_data()
    return [
        {"card_id": c["card_id"], "name": c["name"],
         "card_type": c["card_type"], "status": c["status"]}
        for c in data["cards"]
        if c["owner_id"] == runtime.context["owner_id"]
        and (card_id is None or c["card_id"] == card_id)
    ]


@tool
def report_card_lost(card_id: str, runtime: ToolRuntime[dict]) -> dict:
    """본인 카드를 분실 정지(lost)한다. middleware 승인 후 실행한다.

    Args:
        card_id: 분실신고할 본인 카드 ID. active 또는 locked 상태여야 한다.
        runtime: 실행 시 주입되는 정보. context의 owner_id로 사용자를 확인한다.
    """
    data = read_data()
    card = check_card_change(data, "report_card_lost", card_id, runtime.context["owner_id"])
    card["status"] = "lost"
    save_data(data)
    return {"status": "completed", "card_id": card_id, "card_status": "lost"}


@tool
def cancel_card_loss(card_id: str, runtime: ToolRuntime[dict]) -> dict:
    """본인 카드의 분실신고를 취소하여 사용 가능(active) 상태로 바꾼다. 승인 후 실행한다.

    Args:
        card_id: 분실신고를 취소할 본인 카드 ID. lost 상태여야 한다.
        runtime: 실행 시 주입되는 정보. context의 owner_id로 사용자를 확인한다.
    """
    data = read_data()
    card = check_card_change(data, "cancel_card_loss", card_id, runtime.context["owner_id"])
    card["status"] = "active"
    save_data(data)
    return {"status": "completed", "card_id": card_id, "card_status": "active"}


@wrap_tool_call
def validate_tool_call(request: ToolCallRequest, handler):
    try:
        message = next(m for m in reversed(request.state["messages"]) if isinstance(m, AIMessage))
        if len(message.tool_calls) != 1:
            raise ValueError("어떤 도구도 실행되지 않았습니다. 도구를 하나씩 호출하세요.")
        name = request.tool_call["name"]
        args = TOOL_SCHEMAS[name].model_validate(request.tool_call["args"])
        data = read_data()
        owner_id = request.runtime.context["owner_id"]
        if name == "lookup_cards":
            if args.card_id is not None:
                find_card(data, args.card_id, owner_id)
        else:
            check_card_change(data, name, args.card_id, owner_id)
        return handler(request)
    except (ValueError, OSError) as error:
        return ToolMessage(
            content=f"처리 실패: {error}", status="error",
            tool_call_id=request.tool_call["id"], name=request.tool_call["name"],
        )


@wrap_tool_call
def approve_tool_call(request: ToolCallRequest, handler):
    name = request.tool_call["name"]
    if name == "lookup_cards":
        return handler(request)

    args = request.tool_call["args"]
    owner_id = request.runtime.context["owner_id"]
    card = find_card(read_data(), args["card_id"], owner_id)
    next_status = "lost" if name == "report_card_lost" else "active"
    decision = interrupt({
        "question": "다음 카드 상태 변경을 승인하시겠습니까?",
        "action": "분실신고" if name == "report_card_lost" else "분실신고 취소",
        "card": f"{card['name']} ({card['card_id']})",
        "current_status": card["status"],
        "next_status": next_status,
    })
    if decision != "approve":
        return ToolMessage(
            content="사용자가 카드 상태 변경을 거절하여 취소했습니다.",
            tool_call_id=request.tool_call["id"], name=name,
        )
    return handler(request)


def create_card_agent(model):
    return create_agent(
        model=model,
        context_schema=dict,
        tools=[lookup_cards, report_card_lost, cancel_card_loss],
        middleware=[validate_tool_call, approve_tool_call],
        system_prompt="""너는 카드 담당자다. 카드 조회, 분실신고, 분실신고 취소만 한다.
도구는 한 번에 하나만 호출하고 결과를 확인한 후 다음 도구를 호출한다.
카드 ID를 추측하지 말고 조회로 확인한다. 대상이 불명확하면 질문한다.
active는 사용 가능, locked는 일시 잠금, lost는 분실 정지다.
분실신고 취소는 lost 카드를 active로 바꾸는 작업이다.
하나의 사용자 요청을 처리하는 동안 완료되거나 거절된 작업을 반복하지 않는다.
사용자가 새로 요청하면 별도 요청으로 처리하고, 변경 작업은 다시 승인받는다.
업무 조건·권한 오류가 발생하면 실패 이유를 안내하고 종료한다.
실행 결과 또는 사용자에게 필요한 추가 질문을 한국어로 반환한다.
성공 여부와 카드 상태는 반드시 도구 결과만 근거로 안내한다.
""",
        name="card_agent",
    )
