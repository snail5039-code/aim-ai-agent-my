from vector_store import open_vector_store

TEXTS = [
    "Docker 이미지는 컨테이너를 실행하는 데 필요한 파일과 설정을 담는다.",
    "Docker Compose는 여러 컨테이너의 실행 설정을 하나의 파일로 관리한다.",
    "이름 있는 볼륨에 데이터를 저장하면 컨테이너를 삭제하고 다시 만들어도 유지된다.",
    "FastAPI는 Python으로 API 서버를 만드는 프레임워크이며, 요청 데이터 검증과 자동 API 문서를 제공한다.",
    "LangGraph는 상태를 주고받는 여러 처리 단계를 그래프로 연결하고, 조건에 따라 분기하거나 반복하도록 구성한다.",
    "React는 컴포넌트를 조합해 사용자 화면을 만들고, 상태가 바뀌면 화면을 갱신한다.",
]


def ingest():
    with open_vector_store(initialize=True) as vector_store:
        vector_store.add_texts(
            TEXTS, ids=["image", "compose", "volume", "fastapi", "langgraph", "react"]
        )
    print(f"텍스트 {len(TEXTS)}개를 임베딩해 저장했습니다.")


if __name__ == "__main__":
    ingest()
