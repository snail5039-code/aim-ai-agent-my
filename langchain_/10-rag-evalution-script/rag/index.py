"""임베딩 생성과 Chroma 인덱스 캐시.

인덱스는 (문서 + 청킹 + 임베딩 모델) 해시를 컬렉션명으로 써서 재사용한다.
검색법만 바꾼 실험은 재임베딩 없이 같은 인덱스를 그대로 쓴다.
"""

from __future__ import annotations

import time

import chromadb
from langchain_chroma import Chroma

from .config import index_signature, resolve_path


def _retry_client():
    """Gemini 429(쿼터 초과)를 지수 백오프로 흡수하는 클라이언트.

    35문항 x 여러 검색법을 연속으로 돌리면 무료 티어에서 쉽게 걸린다.
    """
    from google import genai
    from google.genai.types import HttpOptions, HttpRetryOptions

    return genai.Client(
        http_options=HttpOptions(
            retry_options=HttpRetryOptions(
                attempts=8,
                initial_delay=2.0,
                max_delay=60.0,
                exp_base=2,
                jitter=1.0,
            )
        )
    )


def list_embedding_models() -> list[str]:
    """이 API 키로 쓸 수 있는 임베딩 모델 목록. 쿼터 초과 시 대안을 찾는 용도."""
    from google import genai

    return [
        model.name.replace("models/", "")
        for model in genai.Client().models.list()
        if "embedContent" in (getattr(model, "supported_actions", None) or [])
    ]


def build_embeddings(embedding_config: dict):
    provider = embedding_config["provider"]
    model = embedding_config["model"]

    if provider == "google":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        embeddings = GoogleGenerativeAIEmbeddings(model=model)
        try:
            embeddings.client = _retry_client()
        except Exception as error:  # 재시도 주입이 실패해도 임베딩 자체는 동작한다.
            print(f"  [경고] 재시도 클라이언트 주입 실패 (429에 취약해집니다): {error}")
        return embeddings

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=model)

    raise ValueError(f"지원하지 않는 embedding.provider: {provider}")


def get_vectorstore(chunks: list, config: dict) -> tuple[Chroma, dict]:
    """캐시된 컬렉션이 있으면 로드하고, 없으면 임베딩해서 만든다.

    Returns:
        (vectorstore, {"collection_name", "index_build_sec", "index_reused"})
    """
    signature = index_signature(config)
    collection_name = f"exp_{signature}"
    persist_dir = resolve_path(config["index"]["persist_dir"])
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(persist_dir))
    existing = {c.name for c in client.list_collections()}

    embeddings = build_embeddings(config["embedding"])
    rebuild = config["index"]["rebuild"]

    if collection_name in existing and not rebuild:
        stored = client.get_collection(collection_name).count()
        if stored == len(chunks):
            print(f"  인덱스 재사용: {collection_name} ({stored}개 청크)")
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                client=client,
            )
            return vectorstore, {
                "collection_name": collection_name,
                "index_build_sec": 0.0,
                "index_reused": True,
            }
        # 청크 수가 다르면 같은 해시라도 신뢰할 수 없으므로 다시 만든다.
        print(f"  인덱스 청크 수 불일치 ({stored} != {len(chunks)}) - 다시 만듭니다")

    if collection_name in existing:
        client.delete_collection(collection_name)

    print(f"  인덱스 생성: {collection_name} ({len(chunks)}개 청크 임베딩 중...)")
    started = time.perf_counter()
    try:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=collection_name,
            client=client,
        )
    except Exception as error:
        # 임베딩 도중 끊기면 반쯤 채워진 컬렉션이 캐시에 남는다. 치우고 나간다.
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

        if "RESOURCE_EXHAUSTED" in str(error) or "429" in str(error):
            raise RuntimeError(
                "\n".join(
                    [
                        f"임베딩 쿼터 초과입니다 (모델: {config['embedding']['model']}).",
                        "재시도를 다 쓰고도 실패했다면 그 모델의 무료 티어 한도가 남지 않은 것입니다.",
                        "config의 embedding.model을 다른 모델로 바꿔보세요.",
                        "사용 가능한 임베딩 모델은 list_embedding_models()로 확인할 수 있습니다:",
                        "  python -c \"from rag.index import list_embedding_models; print(list_embedding_models())\"",
                    ]
                )
            ) from error
        raise
    build_sec = round(time.perf_counter() - started, 2)
    print(f"  인덱스 생성 완료: {build_sec}초")

    return vectorstore, {
        "collection_name": collection_name,
        "index_build_sec": build_sec,
        "index_reused": False,
    }
