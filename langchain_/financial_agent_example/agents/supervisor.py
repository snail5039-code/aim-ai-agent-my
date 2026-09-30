from datetime import datetime
from zoneinfo import ZoneInfo

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallRequest, wrap_tool_call
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from agents.card import create_card_agent
from agents.transfer import create_transfer_agent


@wrap_tool_call
def single_tool_call(request: ToolCallRequest, handler):
    message = next(m for m in reversed(request.state["messages"]) if isinstance(m, AIMessage))
    if len(message.tool_calls) != 1:
        return ToolMessage(
            content="어떤 에이전트도 실행되지 않았습니다. 도구를 하나씩 호출하세요.",
            status="error",
            tool_call_id=request.tool_call["id"], name=request.tool_call["name"],
        )
    return handler(request)


def create_supervisor_agent(model):
    transfer_agent = create_transfer_agent(model)
    card_agent = create_card_agent(model)

    @tool
    def run_transfer_agent(query: str, runtime: ToolRuntime[dict]) -> str:
        """본인 계좌 조회, 본인·타인 계좌로 이체, 본인 거래내역 조회를 이체 담당자에게 요청한다.

        Args:
            query: 처리할 요청. 이전 대화에서 확인한 계좌, 금액, 기간 등 필요한 맥락을 포함한다.
            runtime: 실행 시 주입되는 정보. 사용자 context를 하위 에이전트에 전달한다.
        """
        today = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
        result = transfer_agent.invoke(
            {"messages": [("user", f"기준일: {today}\n요청: {query}")]},
            context=runtime.context,
        )
        return result["messages"][-1].text

    @tool
    def run_card_agent(query: str, runtime: ToolRuntime[dict]) -> str:
        """카드 조회, 카드 분실신고, 카드 분실신고 취소를 카드 담당자에게 요청한다.

        Args:
            query: 처리할 요청. 이전 대화에서 확인한 카드와 수행할 작업 등 필요한 맥락을 포함한다.
            runtime: 실행 시 주입되는 정보. 사용자 context를 하위 에이전트에 전달한다.
        """
        result = card_agent.invoke(
            {"messages": [("user", query)]},
            context=runtime.context,
        )
        return result["messages"][-1].text

    return create_agent(
        model=model,
        context_schema=dict,
        tools=[run_transfer_agent, run_card_agent],
        middleware=[single_tool_call],
        checkpointer=InMemorySaver(),
        system_prompt="""너는 가상 금융 업무 Supervisor다. 사용자 요청에 맞는 에이전트를 호출한다.
도구는 한 번에 하나만 호출하고 결과를 확인한 후 다음 도구를 호출한다.
하위 담당자에게 이전 대화의 대상, 금액, 기간 등 필요한 맥락을 충분히 전달한다.
사용자의 의도를 임의로 바꾸지 말고 정보가 부족하면 추가 질문을 전달한다.
하나의 사용자 요청을 처리하는 동안 완료되거나 거절된 작업을 반복하지 않는다.
사용자가 새로 요청하면 별도 요청으로 처리하고, 변경 작업은 다시 승인받는다.
실패 원인을 안내하고 성공했다고 말하지 않는다. 업무 결과만 근거로 한국어로 간결하게 응답한다.
업무 승인은 실행 중 표시되는 승인 입력으로만 받는다.
대상과 금액이 명확한 이체 요청은 담당 Agent에 전달하여 Tool의 승인 절차까지 진행한다.
일반 대화로 승인을 다시 묻거나 사용자의 말만으로 승인되었다고 판단하지 않는다.
""",
        name="supervisor",
    )
