import json
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.types import Command

from agents.supervisor import create_supervisor_agent
from data_store import prepare_data


def main():
    load_dotenv(Path(__file__).resolve().parent / ".env")
    prepare_data()
    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    )
    agent = create_supervisor_agent(model)
    context = {"owner_id": "user-001"}
    config = {
        "configurable": {"thread_id": str(uuid4())},
        "recursion_limit": 40,
    }
    print("가상 금융 에이전트 | 사용자: user-001 | 종료: /exit")

    while True:
        user_input = input("\n요청: ").strip()
        if user_input == "/exit":
            break
        if not user_input:
            continue
        result = agent.invoke(
            {"messages": [("user", user_input)]}, config=config, context=context
        )
        while result.get("__interrupt__"):
            pending = result["__interrupt__"][0]
            print(json.dumps(pending.value, ensure_ascii=False, indent=2))
            answer = input("승인 / 거절: ").strip()
            while answer not in ("승인", "거절"):
                answer = input("'승인' 또는 '거절'을 입력하세요: ").strip()
            decision = "approve" if answer == "승인" else "reject"
            result = agent.invoke(
                Command(resume={pending.id: decision}), config=config, context=context
            )
        print("\n답변:", result["messages"][-1].text)


if __name__ == "__main__":
    main()
