from datetime import date, datetime
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallRequest, wrap_tool_call
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import interrupt
from pydantic import BaseModel, ConfigDict, Field

from data_store import read_data, save_data


class AccountArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    account_id: str | None = Field(default=None, min_length=1)


class TransferArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    from_account_id: str = Field(min_length=1)
    to_account_id: str = Field(min_length=1)
    amount: int = Field(gt=0)


class TransactionArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    account_id: str | None = Field(default=None, min_length=1)
    start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    min_amount: int | None = Field(default=None, ge=0)
    max_amount: int | None = Field(default=None, ge=0)
    transaction_type: Literal["deposit", "withdrawal", "payment"] | None = None


TOOL_SCHEMAS = {
    "lookup_accounts": AccountArgs,
    "transfer_money": TransferArgs,
    "lookup_transactions": TransactionArgs,
}


def find_account(data, account_id, owner_id):
    account = next(
        (a for a in data["accounts"]
         if a["account_id"] == account_id and a["owner_id"] == owner_id),
        None,
    )
    if account is None:
        raise ValueError("본인 소유의 계좌 ID인지 확인해 주세요.")
    return account


def find_recipient_account(data, account_id):
    account = next((a for a in data["accounts"] if a["account_id"] == account_id), None)
    if account is None:
        raise ValueError("입금 계좌가 존재하지 않습니다. 계좌 ID를 확인해 주세요.")
    return account


def check_transfer(data, args, owner_id):
    source = find_account(data, args.from_account_id, owner_id)
    target = find_recipient_account(data, args.to_account_id)
    if source["account_id"] == target["account_id"]:
        raise ValueError("출금 계좌와 입금 계좌는 달라야 합니다.")
    if source["balance"] < args.amount:
        raise ValueError("출금 계좌의 잔액이 부족합니다.")
    return source, target


@tool
def lookup_accounts(runtime: ToolRuntime[dict], account_id: str | None = None) -> list[dict]:
    """본인 계좌의 ID, 별명, 잔액을 조회한다.

    Args:
        runtime: 실행 시 주입되는 정보. context의 owner_id로 사용자를 확인한다.
        account_id: 조회할 본인 계좌 ID. 생략하면 본인 전체 계좌를 조회한다.
    """
    data = read_data()
    owner_id = runtime.context["owner_id"]
    return [
        a for a in data["accounts"]
        if a["owner_id"] == owner_id
        and (account_id is None or a["account_id"] == account_id)
    ]


@tool
def transfer_money(
    from_account_id: str, to_account_id: str, amount: int, runtime: ToolRuntime[dict]
) -> dict:
    """본인 계좌에서 본인 또는 타인 계좌로 양의 정수 amount원을 이체한다. 승인 후 실행한다.

    타인에게 송금할 때는 사용자가 제공한 입금 계좌 ID를 사용한다.

    Args:
        from_account_id: 출금할 본인 계좌 ID.
        to_account_id: 입금할 본인 또는 타인의 계좌 ID.
        amount: 이체할 금액. 원 단위의 0보다 큰 정수.
        runtime: 실행 시 주입되는 정보. context의 owner_id로 사용자를 확인한다.
    """
    data = read_data()
    owner_id = runtime.context["owner_id"]
    args = TransferArgs(
        from_account_id=from_account_id, to_account_id=to_account_id, amount=amount
    )
    source, target = check_transfer(data, args, owner_id)
    source["balance"] -= amount
    target["balance"] += amount
    occurred_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    for account, transaction_type in [
        (source, "withdrawal"), (target, "deposit")
    ]:
        data["transactions"].append({
            "transaction_id": str(uuid4()),
            "owner_id": account["owner_id"],
            "account_id": account["account_id"],
            "type": transaction_type,
            "amount": amount,
            "occurred_at": occurred_at,
            "card_id": None,
            "merchant": None,
        })
    save_data(data)
    return {
        "status": "completed", "amount": amount,
        "from_account": source, "to_account_id": target["account_id"],
    }


@tool
def lookup_transactions(
    runtime: ToolRuntime[dict],
    account_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    min_amount: int | None = None,
    max_amount: int | None = None,
    transaction_type: Literal["deposit", "withdrawal", "payment"] | None = None,
) -> list[dict]:
    """본인 거래를 최신순으로 조회한다.

    생략한 필터는 적용하지 않으며, 지정한 조건은 모두 만족해야 한다.

    Args:
        runtime: 실행 시 주입되는 정보. context의 owner_id로 사용자를 확인한다.
        account_id: 조회할 본인 계좌 ID. 생략하면 본인 전체 계좌를 조회한다.
        start_date: 조회 시작일. YYYY-MM-DD 형식이며 해당 날짜를 포함한다.
        end_date: 조회 종료일. YYYY-MM-DD 형식이며 해당 날짜를 포함한다.
        min_amount: 최소 거래 금액. 0 이상 정수이며, 50000이면 5만 원 이상을 조회한다.
        max_amount: 최대 거래 금액. 0 이상 정수이며, 100000이면 10만 원 이하를 조회한다.
        transaction_type: deposit은 입금, withdrawal은 모든 출금, payment는 카드 결제.
            생략하면 모든 거래 유형을 조회한다.
    """
    data = read_data()
    owner_id = runtime.context["owner_id"]
    cards = {c["card_id"]: c["name"] for c in data["cards"] if c["owner_id"] == owner_id}
    results = []
    for transaction in data["transactions"]:
        if transaction["owner_id"] != owner_id:
            continue
        if account_id is not None and transaction["account_id"] != account_id:
            continue
        occurred_date = transaction["occurred_at"][:10]
        if start_date is not None and occurred_date < start_date:
            continue
        if end_date is not None and occurred_date > end_date:
            continue
        if min_amount is not None and transaction["amount"] < min_amount:
            continue
        if max_amount is not None and transaction["amount"] > max_amount:
            continue
        if transaction_type == "payment":
            if transaction["type"] != "withdrawal" or transaction["card_id"] is None:
                continue
        elif transaction_type is not None and transaction["type"] != transaction_type:
            continue
        results.append({**transaction, "card_name": cards.get(transaction["card_id"])})
    return sorted(results, key=lambda t: t["occurred_at"], reverse=True)


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
        if name == "transfer_money":
            check_transfer(data, args, owner_id)
        else:
            if args.account_id is not None:
                find_account(data, args.account_id, owner_id)
            if name == "lookup_transactions":
                if args.start_date is not None:
                    date.fromisoformat(args.start_date)
                if args.end_date is not None:
                    date.fromisoformat(args.end_date)
                if args.start_date and args.end_date and args.start_date > args.end_date:
                    raise ValueError("시작일은 종료일보다 늦을 수 없습니다.")
                if args.min_amount is not None and args.max_amount is not None:
                    if args.min_amount > args.max_amount:
                        raise ValueError("최소 금액은 최대 금액보다 클 수 없습니다.")
        return handler(request)
    except (ValueError, OSError) as error:
        return ToolMessage(
            content=f"처리 실패: {error}", status="error",
            tool_call_id=request.tool_call["id"], name=request.tool_call["name"],
        )


@wrap_tool_call
def approve_tool_call(request: ToolCallRequest, handler):
    if request.tool_call["name"] != "transfer_money":
        return handler(request)

    args = request.tool_call["args"]
    owner_id = request.runtime.context["owner_id"]
    data = read_data()
    source = find_account(data, args["from_account_id"], owner_id)
    decision = interrupt({
        "tool_name": request.tool_call["name"],
        "question": "다음 이체를 승인하시겠습니까?",
        "from_account": f"{source['nickname']} ({source['account_id']})",
        "to_account": args["to_account_id"],
        "amount": args["amount"],
    })
    if decision != "approve":
        return ToolMessage(
            content="사용자가 이체를 거절하여 취소했습니다.",
            tool_call_id=request.tool_call["id"], name=request.tool_call["name"],
        )
    return handler(request)


def create_transfer_agent(model):
    return create_agent(
        model=model,
        context_schema=dict,
        tools=[lookup_accounts, transfer_money, lookup_transactions],
        middleware=[validate_tool_call, approve_tool_call],
        system_prompt="""너는 계좌·이체 담당자다. 본인 계좌 조회, 본인 또는 타인 계좌로의 즉시이체, 본인 거래내역 조회를 한다.
도구는 한 번에 하나만 호출하고 결과를 확인한 후 다음 도구를 호출한다.
본인 계좌 ID는 조회로 확인한다. 타인의 입금 계좌 ID는 사용자가 제공한 값을 사용하고, 없으면 질문한다.
계좌 ID를 추측하지 않는다. 타인 계좌의 잔액이나 거래내역은 조회하지 않는다. 대상이나 금액이 불명확하면 질문한다.
사용자가 지정한 금액·기간을 임의로 바꾸지 않는다. 잔액 부족이나 권한 오류는 안내하고 종료한다.
이체 대상과 금액이 명확하면 계좌를 확인한 뒤 transfer_money를 호출한다.
승인은 이 Tool의 실행 전 interrupt에서 받는다. 별도의 승인 질문을 최종 답변으로 출력하고 끝내지 않는다.
Tool 호출은 승인 요청을 시작하는 것이며, 실제 이체는 승인 후에만 실행된다.
하나의 사용자 요청을 처리하는 동안 완료되거나 거절된 작업을 반복하지 않는다.
사용자가 새로 요청하면 별도 요청으로 처리하고, 변경 작업은 다시 승인받는다.
성공 여부와 조회 결과는 도구 결과만 근거로 안내한다.
입금은 deposit, 출금은 withdrawal, 카드 결제는 payment로 조회한다.
상대 날짜는 전달받은 기준일로 계산하고 YYYY-MM-DD로 전달한다. 이번 주는 월~일이다.
실행 결과 또는 사용자에게 필요한 추가 질문을 한국어로 반환한다.
""",
        name="transfer_agent",
    )
