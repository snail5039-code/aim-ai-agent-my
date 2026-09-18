import warnings
import time
import logging
from agents.supervisor.graph import supervisor_graph
from langchain_core.messages import HumanMessage
from rich.console import Console

try:
    import cowsay
except ImportError:
    cowsay = None

logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)
logging.getLogger("langchain_google_genai").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

config = {"configurable": {"thread_id": "report-session-1"}}
console = Console()

def stream_text(text:str, delay: float = 0.001):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()

def main():
    if cowsay:
        cowsay.tux("멀티 에이전트 보고서 시스템")
    else:
        print("멀티 에이전트 보고서 시스템")

    print()
    print("==== 종료하려면 exit 또는 종료를 입력하세요 ====")


    while True:
        user_input = input("요청을 입력하세요 : ")

        if user_input in ["exit", "종료"]:
            print("\n======= 시스템을 종료합니다. =======")
            print("다음에 또 봐요~~!!!")
            break

        with console.status("[bold green]에이전트들이 작업 중입니다...[/bold green]", spinner="dots"):
            result = supervisor_graph.invoke(
                {
                    "query" : user_input,
                    "messages" : [HumanMessage(content=user_input)]
                 },
                config=config,
            )

        print("\n=== 최종 응답 ===")
        stream_text(result["final_result"])
        print()
        print()

if __name__ == "__main__":
    main()