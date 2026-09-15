# [TIL] LangGraph 기초 — 상태, 분기, 반복으로 AI 작업 흐름 만들기

> 학습 자료: `11-langgraph-basic.ipynb`  
> 목표: State가 어떻게 바뀌고, 다음 Node가 어떻게 선택되는지 코드로 이해하기.

LangGraph는 **공유 상태(State)를 바탕으로 작업(Node)을 실행하고, 연결(Edge)을 따라 다음 작업으로 이동하는 프레임워크**다. 이 글에서는 기본 챗봇 → 조건 분기 → 반복 → 데이터 누적 → 작성·검토 루프 순서로 살펴본다.

노트북의 중복 풀이를 하나의 흐름으로 합쳤다. 예제는 읽기 쉽도록 변수명을 정리했으며, 종료 조건과 모델 의존성을 보완한 부분은 따로 설명한다. Checkpoint, Interrupt, ToolNode, Send는 원본에서 필요성을 소개하는 수준이므로 여기서 구현하지 않는다.

## 1. 왜 LangGraph를 사용할까?

단순한 AI 작업은 다음 순서로 충분하다.

```text
입력 → 프롬프트 → LLM → 출력 파서 → 결과
```

하지만 검색 결과가 부족하면 질문을 바꾸고 다시 검색해야 할 수도 있다. 원본에서는 Chroma 검색과 LLM을 Python 반복문으로 연결한다.

```python
# 개념을 보여주는 축약 코드. retriever와 llm은 미리 준비해야 한다.
question = "AI 반도체 시장의 전망은?"
max_attempts = 3

for attempt in range(max_attempts):
    docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    check = llm.invoke(
        f"질문: {question}\n검색 결과: {context}\n"
        "답변하기에 충분하면 yes, 부족하면 no만 출력해."
    )
    if check.text.strip().lower() == "yes":
        break
    if attempt + 1 < max_attempts:
        question = llm.invoke(
            f"검색 질문을 같은 의도의 다른 표현 하나로 바꿔줘: {question}"
        ).text
```

모델은 검색 결과의 충분성을 판단하지만 **반복 여부와 종료는 Python 코드가 제어**한다. 분기와 재시도가 많아지면 이 제어 로직도 복잡해진다. LangGraph에서는 이러한 관계를 노드와 엣지로 드러낼 수 있다.

원본의 검색 예제는 `./chroma_db`의 `spri_ai_brief` 컬렉션을 열고 `k=3`으로 검색한다. 문서를 새로 적재하는 코드는 없으므로, 재현하려면 기존 데이터와 해당 컬렉션에 맞는 임베딩 설정이 필요하다. 위 코드는 검색·판정·질문 변경까지만 다루며 최종 답변 생성은 포함하지 않는다. 마지막 시도 후 불필요하게 질문을 다시 만드는 원본 동작은 생략했다.

### Chain, Workflow, Agent의 차이

| 방식 | 흐름을 결정하는 방법 | 예시 |
|---|---|---|
| 단순 Chain | 정해진 순서로 처리 | 번역 → 요약 |
| Workflow | 개발자가 분기와 반복 규칙을 설계 | 검토 실패 시 재작성 |
| Agent | 주어진 목표와 도구 안에서 LLM이 다음 행동을 선택 | 검색할지 계산할지 선택 |

이 구분은 제어 방식의 차이를 설명한다. LangChain에도 분기나 병렬 구성 기능이 있으므로 “Chain은 무조건 직선만 가능하다”는 뜻은 아니다. 또한 LLM이 분류 결과를 만든다고 모두 Agent인 것은 아니다. 이 글의 실습은 개발자가 연결과 종료 규칙을 정한 Workflow에 가깝다.

## 2. 핵심은 State, Node, Edge

| 개념 | 역할 | 코드에서의 형태 |
|---|---|---|
| State | 현재 입력과 중간 결과를 공유 | `TypedDict` 스키마와 실제 딕셔너리 |
| Node | 상태를 읽어 작업하고 변경분을 반환 | Python 함수 |
| Edge | 다음에 실행할 작업을 지정 | 고정 연결 또는 조건부 연결 |
| Reducer | 필드별로 기존 값과 새 값을 합치는 규칙 | `Annotated`에 지정하는 함수 |

```text
현재 State → Node 실행 → 반환한 변경분을 State에 반영 → 다음 Node 선택
```

노드는 보통 전체 상태를 반환할 필요가 없다. `{"answer": "답변"}`만 반환하면 해당 필드가 갱신되고 `question`은 유지된다. Reducer가 없으면 같은 필드의 값은 새 값으로 교체된다. 이 상태 갱신 방식은 [공식 Graph API 문서](https://docs.langchain.com/oss/python/langgraph/graph-api)에 설명되어 있다.

`TypedDict`는 키와 값의 타입을 표현하는 도구다. 타입 선언만으로 기본값이 생기거나 런타임 검증이 자동 수행되지는 않는다. 노드에서 읽을 키는 초기 입력으로 주거나 앞선 노드가 채워야 한다.

## 3. 공통 실행 준비

아래 예제는 **이 준비 코드 실행 후 각 절의 Python 코드를 순서대로 실행**하는 방식이다. 숫자 증가와 Reducer 예제 자체는 모델 호출이 필요 없다.

```bash
pip install langgraph langchain-core langchain-google-genai python-dotenv pydantic
```

`.env`에는 실제 사용 가능한 모델 ID와 API 키를 설정한다.

```dotenv
GOOGLE_API_KEY=본인의_API_키
GOOGLE_MODEL=사용_가능한_Gemini_모델_ID
```

```python
import os
import operator
from typing import Annotated, Literal, NotRequired, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()
llm = ChatGoogleGenerativeAI(model=os.environ["GOOGLE_MODEL"])
```

`NotRequired`를 `typing`에서 가져오는 이 예제는 Python 3.11 이상을 기준으로 한다. 원본 모델 문자열은 `gemini-3.6-flash`, 임베딩 모델은 `gemini-embedding-2`지만, 여기서는 모델 제공 여부를 가정하지 않고 환경변수로 받는다. 실제 모델 실행에는 계정의 접근 권한과 패키지 호환성이 필요하다. API 키가 들어 있는 `.env`는 게시하지 않는다.

## 4. 가장 작은 그래프: 질문 → 답변

```text
START → chatbot → END
```

```python
class ChatState(TypedDict):
    question: str
    answer: NotRequired[str]

def chatbot(state: ChatState):
    response = llm.invoke(state["question"])
    return {"answer": response.text}

chat_builder = StateGraph(ChatState)
chat_builder.add_node("chatbot", chatbot)
chat_builder.add_edge(START, "chatbot")
chat_builder.add_edge("chatbot", END)
chat_graph = chat_builder.compile()

result = chat_graph.invoke({"question": "LangGraph가 뭐야?"})
print(result["answer"])
```

실행 흐름은 다음과 같다.

1. 초기 상태에 `question`을 넣는다.
2. `START`에서 연결한 `chatbot`이 실행된다.
3. `chatbot`이 질문을 읽고 LLM을 호출한다.
4. 반환한 `answer`가 State에 반영된다.
5. `END`에 도달하면 최종 상태를 반환한다.

```python
# 최종 상태의 모양. 답변 내용은 실행마다 달라질 수 있다.
{"question": "LangGraph가 뭐야?", "answer": "LangGraph는 ..."}
```

`add_node("chatbot", chatbot)`의 첫 번째 값은 그래프 안에서 사용할 이름, 두 번째 값은 실행할 함수다. `compile()`은 구성한 그래프를 실행 가능한 객체로 만든다. 컴파일 자체가 LLM을 호출하는 것은 아니다.

## 5. 조건부 Edge: 입력 언어에 따라 답변하기

```text
START → detect_language → ko → answer_ko → END
                        → en → answer_en → END
```

언어 감지 노드는 **상태를 갱신**하고, 라우팅 함수는 **이동할 경로를 반환**한다.

```python
class RouterState(TypedDict):
    question: str
    language: NotRequired[str]
    answer: NotRequired[str]

def detect_language(state: RouterState):
    response = llm.invoke(
        "다음 문장의 언어가 한국어면 ko, 영어면 en만 출력해: "
        + state["question"]
    )
    return {"language": response.text.strip().lower()}

def answer_ko(state: RouterState):
    return {"answer": llm.invoke("한국어로 답변해줘: " + state["question"]).text}

def answer_en(state: RouterState):
    return {"answer": llm.invoke("Answer in English: " + state["question"]).text}

def route_by_language(state: RouterState):
    language = state["language"]
    if language not in ("ko", "en"):
        raise ValueError(f"지원하지 않는 언어 판정: {language!r}")
    return language

router_builder = StateGraph(RouterState)
router_builder.add_node("detect_language", detect_language)
router_builder.add_node("answer_ko", answer_ko)
router_builder.add_node("answer_en", answer_en)
router_builder.add_edge(START, "detect_language")
router_builder.add_conditional_edges(
    "detect_language",
    route_by_language,
    {"ko": "answer_ko", "en": "answer_en"},
)
router_builder.add_edge("answer_ko", END)
router_builder.add_edge("answer_en", END)
router_graph = router_builder.compile()

result = router_graph.invoke({"question": "파이썬의 장점이 뭐야?"})
print(result)
```

`add_conditional_edges(출발 노드, 라우팅 함수, 경로 매핑)`에서 `"ko"`는 라우팅 함수의 반환값이고 `"answer_ko"`는 노드 이름이다. 둘이 같은 문자열일 필요는 없다.

한국어 입력이라면 `detect_language → answer_ko`가 실행되며 `answer_en`은 실행되지 않는다. 원본은 `ko`가 아니면 영어로 보내지만, 위 예제는 예상하지 못한 모델 출력을 확인할 수 있도록 오류를 발생시킨다. 이 실습의 입력 범위는 한국어와 영어다.

## 6. invoke와 stream으로 흐름 확인하기

| 호출 | 확인하는 내용 |
|---|---|
| `invoke(input)` | 실행이 끝난 뒤 최종 State |
| `stream(input, stream_mode="updates")` | 각 노드가 반환한 변경분 |
| `stream(input, stream_mode="values")` | 초기 상태와 각 단계의 전체 State |

```python
for event in router_graph.stream(
    {"question": "파이썬의 장점이 뭐야?"},
    stream_mode="updates",
):
    print(event)
```

```text
출력 형태 예시:
{'detect_language': {'language': 'ko'}}
{'answer_ko': {'answer': '파이썬의 장점은 ...'}}
```

```python
for state in router_graph.stream(
    {"question": "파이썬의 장점이 뭐야?"},
    stream_mode="values",
):
    print(state)
```

```text
출력 형태 예시:
{'question': '파이썬의 장점이 뭐야?'}
{'question': '파이썬의 장점이 뭐야?', 'language': 'ko'}
{'question': '파이썬의 장점이 뭐야?', 'language': 'ko', 'answer': '파이썬의 장점은 ...'}
```

`updates`는 변경된 부분, `values`는 변경분이 반영된 전체 상태를 보여준다. LLM의 토큰 단위 출력을 보려면 `messages` 모드처럼 다른 스트리밍 방식을 사용한다. `graph.stream()`이 항상 토큰을 반환하는 것은 아니다. 자세한 모드 구분은 [공식 Streaming 문서](https://docs.langchain.com/oss/python/langgraph/streaming)를 참고한다.

각 `invoke()`와 `stream()` 호출은 새로운 실행이다. 위 코드를 모두 실행하면 답변 생성도 여러 번 수행된다. `stream()`은 이미 완료된 `invoke()`의 기록을 읽는 함수가 아니다.

## 7. 반복: count가 5가 될 때까지 실행

```python
class CountState(TypedDict):
    count: int

def increment(state: CountState):
    return {"count": state["count"] + 1}

def route_by_count(state: CountState):
    return "end" if state["count"] >= 5 else "continue"

count_builder = StateGraph(CountState)
count_builder.add_node("increment", increment)
count_builder.add_edge(START, "increment")
count_builder.add_conditional_edges(
    "increment", route_by_count,
    {"continue": "increment", "end": END},
)
count_graph = count_builder.compile()

for event in count_graph.stream({"count": 0}, stream_mode="updates"):
    print(event)
```

```text
{'increment': {'count': 1}}
{'increment': {'count': 2}}
{'increment': {'count': 3}}
{'increment': {'count': 4}}
{'increment': {'count': 5}}
```

`increment`가 반환한 값이 반영된 **이후** `route_by_count`가 호출된다. 그래서 `count=5`가 되면 바로 종료한다. 이전 노드로 향하는 엣지가 반복을 만들고 라우팅 함수가 종료 조건을 만든다. 이 구조에서는 시작하자마자 증가 노드를 실행하므로, 처음부터 `count=5`를 넣으면 결과는 6이다.

## 8. Reducer: 덮어쓸 것인가, 누적할 것인가?

```python
class ReducerState(TypedDict):
    name: NotRequired[str]
    messages: Annotated[list, add_messages]
    logs: Annotated[list[str], operator.add]

def step_a(state: ReducerState):
    return {
        "name": "A가 설정",
        "messages": [HumanMessage(content="안녕")],
        "logs": ["A 실행"],
    }

def step_b(state: ReducerState):
    return {
        "name": "B가 덮어씀",
        "messages": [AIMessage(content="반가워!")],
        "logs": ["B 실행"],
    }

def step_c(state: ReducerState):
    return {
        "name": "C가 덮어씀",
        "messages": [HumanMessage(content="잘 가!")],
        "logs": ["C 실행"],
    }

reducer_builder = StateGraph(ReducerState)
for name, node in [("a", step_a), ("b", step_b), ("c", step_c)]:
    reducer_builder.add_node(name, node)
reducer_builder.add_edge(START, "a")
reducer_builder.add_edge("a", "b")
reducer_builder.add_edge("b", "c")
reducer_builder.add_edge("c", END)
reducer_graph = reducer_builder.compile()

result = reducer_graph.invoke({"messages": [], "logs": []})
print(result["name"])
print(result["logs"])
print([(m.type, m.content) for m in result["messages"]])
```

```text
C가 덮어씀
['A 실행', 'B 실행', 'C 실행']
[('human', '안녕'), ('ai', '반가워!'), ('human', '잘 가!')]
```

`Annotated[타입, 메타데이터]`에서 LangGraph가 메타데이터의 함수를 Reducer로 해석한다.

| 필드 | 갱신 방법 | 사용 목적 |
|---|---|---|
| `name` | 새 값으로 교체 | 최신 결과 |
| `logs` | 기존 리스트 + 새 리스트 | 실행 기록 누적 |
| `messages` | 메시지 전용 병합 | 대화 기록 관리 |

`add_messages`는 새 메시지를 추가하고 **같은 ID의 메시지는 교체**할 수 있다. 단순한 리스트 덧셈과 차이가 있다. 자세한 동작은 [공식 메시지 상태 설명](https://docs.langchain.com/oss/python/langgraph/graph-api#working-with-messages-in-graph-state)을 참고한다.

누적 필드에는 새로운 항목만 반환한다. 예를 들어 `logs`에 Reducer가 있을 때 기존 로그까지 복사해서 반환하면 기존 항목이 중복될 수 있다. 또한 메시지를 State에 저장하는 것만으로 모델이 대화를 기억하지는 않는다. 다음 모델 호출에도 그 메시지를 입력해야 한다. 실행 사이의 상태 보존은 Checkpointer 등 별도 구성으로 다룬다.

## 9. 실습 1: 감정에 따라 응답 분기

언어 라우터와 같은 구조다. 감정 분석 결과가 `positive`면 축하·공감 응답을, `negative`면 위로 응답을 생성한다.

```python
class SentimentState(TypedDict):
    text: str
    sentiment: NotRequired[str]
    response: NotRequired[str]

def analyze(state: SentimentState):
    result = llm.invoke(
        "다음 문장의 감정을 positive 또는 negative 하나로만 분류해: "
        + state["text"]
    )
    return {"sentiment": result.text.strip().lower()}

def respond_positive(state: SentimentState):
    return {"response": llm.invoke("기쁨에 공감하며 답해줘: " + state["text"]).text}

def respond_negative(state: SentimentState):
    return {"response": llm.invoke("따뜻하게 위로해줘: " + state["text"]).text}

def route_by_sentiment(state: SentimentState):
    label = state["sentiment"]
    if label not in ("positive", "negative"):
        raise ValueError(f"예상하지 못한 감정 판정: {label!r}")
    return label

sentiment_builder = StateGraph(SentimentState)
sentiment_builder.add_node("analyze", analyze)
sentiment_builder.add_node("respond_positive", respond_positive)
sentiment_builder.add_node("respond_negative", respond_negative)
sentiment_builder.add_edge(START, "analyze")
sentiment_builder.add_conditional_edges(
    "analyze", route_by_sentiment,
    {"positive": "respond_positive", "negative": "respond_negative"},
)
sentiment_builder.add_edge("respond_positive", END)
sentiment_builder.add_edge("respond_negative", END)
sentiment_graph = sentiment_builder.compile()

print(sentiment_graph.invoke({"text": "오늘 승진했어! 너무 기뻐!"})["response"])
```

원본 강사 풀이에서는 분석 노드 안에 `prompt | llm | StrOutputParser()`로 만든 Chain을 사용한다. 즉, **노드 내부의 처리에는 Chain을 쓰고, 노드 사이의 흐름에는 LangGraph를 쓸 수 있다.** 감정을 두 범주로만 나누는 것은 실습용 단순화다.

## 10. 실습 2: 숫자를 추측하고 범위 좁히기

```text
START → guess → check → 정답 또는 횟수 소진 → END
                 └── 오답이며 기회 남음 → guess
```

정답이 37인데 50을 추측했다면 `high=49`로 바꾼다. 다음 추측이 25라면 `low=26`으로 바꾼다. **다음 노드는 갱신된 범위를 읽는다.**

원본의 범위 조정 실습과 최대 5회 제한 풀이를 합친 예제다. 정답 여부를 먼저 확인해 마지막 시도의 정답도 성공으로 처리하고, 범위 밖 출력도 검사한다.

```python
class GuessState(TypedDict):
    target: int
    low: int
    high: int
    attempt: int
    guess: NotRequired[int]
    status: NotRequired[Literal["retry", "success", "exhausted"]]

def guess_number(state: GuessState):
    response = llm.invoke(
        f"{state['low']}부터 {state['high']} 사이의 정수 하나만 출력해."
    )
    value = int(response.text.strip())
    if not state["low"] <= value <= state["high"]:
        raise ValueError("추측값이 현재 범위를 벗어났습니다.")
    return {"guess": value, "attempt": state["attempt"] + 1}

def check_guess(state: GuessState):
    value, target = state["guess"], state["target"]
    if value == target:
        return {"status": "success"}
    if state["attempt"] >= 5:
        return {"status": "exhausted"}
    if value < target:
        return {"low": value + 1, "status": "retry"}
    return {"high": value - 1, "status": "retry"}

def route_guess(state: GuessState):
    return state["status"]

guess_builder = StateGraph(GuessState)
guess_builder.add_node("guess", guess_number)
guess_builder.add_node("check", check_guess)
guess_builder.add_edge(START, "guess")
guess_builder.add_edge("guess", "check")
guess_builder.add_conditional_edges(
    "check", route_guess,
    {"retry": "guess", "success": END, "exhausted": END},
)
guess_graph = guess_builder.compile()

for event in guess_graph.stream(
    {"target": 37, "low": 1, "high": 100, "attempt": 0},
    stream_mode="updates",
):
    print(event)
```

이 코드는 `target`이 초기 범위 안에 있다고 가정한다. 모델이 정수 외의 문장을 출력하면 `int()` 변환 오류가 발생한다. 프롬프트만으로 출력 형식을 보장할 수 없으므로, 실사용에서는 구조화 출력과 오류 처리도 설계해야 한다.

5회 안에 반드시 정답을 맞히는 것은 아니다. 횟수 제한은 성공 보장이 아니라 종료 보장이다. 그래프의 `recursion_limit`도 시도 횟수와 같지 않다. 한 번의 추측에 여러 노드 단계가 있으므로 업무상의 `attempt`를 따로 두는 편이 명확하다.

## 11. 실습 3: 글 작성 → 검토 → 피드백 반영

이번 실습은 지금까지 배운 개념을 함께 사용한다.

```text
START → write → review → pass ─────────────────→ END
          ↑       └── fail → 횟수 남음 ─────────┘ 반복(write)
          └─────────────────────┘
                  fail + 최대 횟수 도달 → END
```

위 흐름을 순서로 읽으면 **작성 → 검토 → 통과하면 종료, 실패하면 최대 3회까지 작성으로 복귀**한다.

### State와 구조화 출력의 역할

| 데이터 | 역할 |
|---|---|
| `topic` | 글의 주제 |
| `draft` | 현재 초안 |
| `feedback` | 다음 작성에 반영할 검토 의견 |
| `result` | 검토 판정 `pass` 또는 `fail` |
| `attempt` | 작성 시도 횟수 |

검토 결과에는 판정과 피드백이 모두 필요하다. 문자열을 직접 쪼개는 대신 `BaseModel`로 응답 구조를 정의한다. Pydantic 모델을 사용하는 구조화 출력은 필드와 값 형식을 검증하는 데 유용하다. 다만 검토 내용의 사실성까지 보장하지는 않는다. 관련 개념은 [공식 Structured output 문서](https://docs.langchain.com/oss/python/langchain/structured-output)를 참고한다.

### 완성 코드

원본의 함수형 풀이와 클래스 풀이를 합쳤다. `sentense`는 의미가 명확한 `draft`로 바꾸고, 작성 모델과 검토 모델을 각각 주입하도록 보완했다.

```python
class WritingState(TypedDict):
    topic: str
    draft: NotRequired[str]
    feedback: NotRequired[str]
    result: NotRequired[Literal["pass", "fail"]]
    attempt: NotRequired[int]

class ReviewResult(BaseModel):
    result: Literal["pass", "fail"]
    feedback: str

class WritingWorkflow:
    def __init__(self, writer, reviewer, max_attempts=3):
        if max_attempts < 1:
            raise ValueError("max_attempts는 1 이상이어야 합니다.")
        self.writer = writer
        self.reviewer = reviewer
        self.max_attempts = max_attempts

    def write(self, state: WritingState):
        attempt = state.get("attempt", 0) + 1
        topic = state["topic"]
        if attempt == 1:
            # 원본처럼 검토·재작성 흐름을 관찰하기 위한 짧은 초안.
            return {"draft": f"{topic}은 아주 좋은 것이야!", "attempt": attempt}

        response = self.writer.invoke(
            f"주제: {topic}\n"
            f"이전 글: {state.get('draft', '')}\n"
            f"피드백: {state.get('feedback', '')}\n"
            "피드백을 반영해서 구체적인 설명이 담긴 짧은 글을 작성해줘."
        )
        return {"draft": response.text, "attempt": attempt}

    def review(self, state: WritingState):
        response = self.reviewer.invoke(
            f"주제: {state['topic']}\n글: {state['draft']}\n"
            "주제를 구체적으로 설명하면 pass, 설명이 부족하면 fail로 판정하고, "
            "feedback에 이유와 개선할 점을 작성해줘."
        )
        return {"result": response.result, "feedback": response.feedback}

    def route(self, state: WritingState):
        if state["result"] == "pass":
            return "success"
        if state["attempt"] >= self.max_attempts:
            return "exhausted"
        return "retry"

    def build(self):
        builder = StateGraph(WritingState)
        builder.add_node("write", self.write)
        builder.add_node("review", self.review)
        builder.add_edge(START, "write")
        builder.add_edge("write", "review")
        builder.add_conditional_edges(
            "review", self.route,
            {"success": END, "exhausted": END, "retry": "write"},
        )
        return builder.compile()

reviewer = llm.with_structured_output(ReviewResult)
writing_graph = WritingWorkflow(writer=llm, reviewer=reviewer).build()

for event in writing_graph.stream(
    {"topic": "AI Agent와 LangGraph"}, stream_mode="updates",
):
    print(event)
```

첫 초안이 짧더라도 실제 LLM이 반드시 `fail`로 판정하는 것은 아니다. 반복 경로를 확실하게 재현하려면 다음 절의 가짜 검토기를 사용한다.

### 상태를 따라가며 읽기

아래는 `fail → pass`인 경우의 설명용 예시다.

| 단계 | 노드가 반환한 변경분 | 다음 행동 |
|---|---|---|
| 첫 작성 | `draft="...아주 좋은 것이야!", attempt=1` | 검토 |
| 첫 검토 | `result="fail", feedback="구체적인 설명이 부족함"` | 다시 작성 |
| 두 번째 작성 | `draft="개선된 글...", attempt=2` | 다시 검토 |
| 두 번째 검토 | `result="pass", feedback="설명이 충분함"` | 종료 |

검토 노드는 `topic`이나 `draft`를 반환하지 않아도 된다. 기존 값이 유지되기 때문이다. 두 번째 작성 노드는 이전 글과 피드백을 읽을 수 있다. 새 초안은 Reducer가 없는 `draft` 필드를 덮어쓴다.

종료 경로와 품질 판정은 구별해야 한다. **최대 횟수에 도달해서 끝난 글은 통과한 글이 아닐 수 있다.** 위 코드는 종료하더라도 실제 `result="fail"`을 유지한다. 원본의 `attempt >= 3`에서 `"pass"`를 반환하는 부분은 종료용 경로 이름으로 쓰였을 뿐, 품질이 통과했다는 뜻이 아니다.

## 12. 가짜 모델로 API 없이 작성 루프 확인하기

원본은 `Graph(llm=fake_llm)`으로 작성 모델을 바꾼다. 그러나 `review()`는 전역 `llm_with_review_result`를 호출하므로 **검토 단계에는 여전히 실제 API 호출이 남는다.**

위 클래스는 검토기도 주입받으므로 두 의존성을 모두 교체할 수 있다. 다음 코드는 공통 import와 `WritingState`, `ReviewResult`, `WritingWorkflow` 정의만 있으면 실행 가능하다. 실제 `llm` 생성 및 앞 절의 실제 모델 실행 코드는 실행하지 않아도 된다.

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel

class FakeReviewer:
    def __init__(self):
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        if self.calls == 1:
            return ReviewResult(result="fail", feedback="두 개념과 관계를 설명해줘.")
        return ReviewResult(result="pass", feedback="개념과 관계가 설명되어 있음.")

fake_writer = FakeListChatModel(responses=[
    "AI Agent는 목표를 수행하기 위해 도구를 선택하고 행동한다. "
    "LangGraph는 상태와 분기, 반복으로 이러한 실행 흐름을 구성한다."
])
fake_graph = WritingWorkflow(fake_writer, FakeReviewer()).build()
final_state = fake_graph.invoke({"topic": "AI Agent와 LangGraph"})

assert final_state["attempt"] == 2
assert final_state["result"] == "pass"
assert "LangGraph" in final_state["draft"]
print(final_state)
```

실행은 `write → review(fail) → write → review(pass) → END` 순서다. 첫 작성은 고정 문자열을 반환하므로 가짜 작성 모델도 두 번째 작성에서 처음 호출된다.

이 확인은 그래프 연결, 피드백 전달, 반복 종료를 검증하는 용도다. 실제 모델의 문장 품질이나 실제 검토의 신뢰성을 검증하는 것은 아니다. `FakeReviewer`는 호출 횟수를 보관하므로 새로운 실행에서도 같은 결과를 원하면 새 인스턴스를 만든다.

## 13. 노드는 언제 나눌까?

| 나누는 기준 | 이 글의 사례 |
|---|---|
| 역할이 다른가? | 글 작성과 글 검토 |
| 중간 상태가 다음 작업에 필요한가? | 감지한 언어를 답변 노드에서 사용 |
| 분기·재시도 지점인가? | 검토 후 작성으로 복귀 |
| 단계별 관찰이 필요한가? | 숫자 추측과 범위 변경 |

항상 같이 실행되는 작은 문자열 처리까지 모두 노드로 나눌 필요는 없다. 예를 들어 `.strip().lower()`는 분석 노드 안에 두면 충분하다.

그래프 구조를 확인하려면 Mermaid 텍스트를 출력할 수 있다.

```python
print(writing_graph.get_graph().draw_mermaid())
```

원본의 `display(Image(...draw_mermaid_png()))`는 노트북에서 이미지로 보는 방법이다. 이미지 렌더링 방식에 따라 네트워크나 추가 환경이 필요할 수 있다. 이 정리본의 텍스트 흐름도는 이미지 첨부 없이도 읽을 수 있게 작성했다.

## 14. 이번 학습에서 기억할 점

- **State는 공유 데이터**, **Node는 작업**, **Edge는 실행 순서**를 담당한다.
- 노드는 필요한 변경분만 반환한다. 필드를 반환하지 않았다고 기존 값이 사라지는 것은 아니다.
- 조건부 Edge의 라우팅 함수는 이 글의 패턴에서 경로만 선택한다. 상태 변경은 노드가 맡는다.
- 반복을 만들 때는 성공 조건과 최대 시도 횟수를 함께 설계한다.
- 최신 결과는 덮어쓰고, 대화나 로그는 목적에 맞는 Reducer로 누적한다.
- `updates`로 노드의 변경분을, `values`로 누적 상태를 관찰한다.
- 작성·검토 Workflow는 이전 초안과 피드백을 State로 전달하면서 개선을 반복한다.
- 가짜 모델 테스트에서는 작성과 검토처럼 모델을 호출하는 모든 의존성을 교체해야 한다.

## 원본과 정리본의 차이

| 원본에서 주의할 부분 | 정리본에 반영한 내용 |
|---|---|
| 여러 셀에서 `State`, `graph`, 함수 이름을 재정의 | 예제별 이름을 구분 |
| 선택적으로 채워지는 키도 모두 필수로 선언 | `NotRequired`로 입력 이후 생성되는 키를 표시 |
| 분류 결과가 예상 밖이어도 반대 경로로 이동 | 지원하는 값인지 검사 |
| 숫자 응답을 `content[0]['text']`로 접근하는 풀이 | 다른 원본 풀이와 같이 `.text` 사용 |
| 숫자 마지막 시도에서 정답이어도 먼저 실패 출력 | 정답을 먼저 검사 |
| 글 재작성 초기 풀이가 피드백을 사용하지 않음 | 이전 글과 피드백을 프롬프트에 포함 |
| 횟수 소진 시 종료 경로로 `pass` 반환 | `success`, `exhausted`, `retry` 구분 |
| 가짜 작성 모델 사용 중 실제 검토 모델 호출 | 작성·검토 의존성 모두 주입 |

이 글은 원본 학습 내용을 정리하고 일부 코드를 보완한 자료다. 실제 LLM 답변 및 API 연동 결과는 실행 환경과 모델에 따라 달라진다.
