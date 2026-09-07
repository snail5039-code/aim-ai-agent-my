"""config의 retrieval.methods를 실제 retriever 객체로 만든다.

지원 검색법: similarity / mmr / bm25 / hybrid

similarity와 mmr은 둘 다 dense 벡터 검색이다. 차이는 표현이 아니라 선택 전략으로,
LangChain의 search_type 값(similarity / mmr)을 그대로 이름으로 쓴다.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever


@lru_cache(maxsize=1)
def _kiwi():
    """Kiwi 초기화는 무거우므로 한 번만 한다."""
    from kiwipiepy import Kiwi

    return Kiwi()


def kiwi_tokenize(text: str) -> list[str]:
    """한국어 형태소 토크나이저 (09-rag-search-advanced.ipynb와 동일).

    명사/동사/수식언/접사와 외국어(SL)·숫자(SN)만 남긴다.
    조사·어미를 버려야 BM25가 의미어 위주로 매칭한다.
    """
    return [
        token.form.lower()
        for token in _kiwi().tokenize(text)
        if token.tag.startswith(("N", "V", "M", "X")) or token.tag in {"SL", "SN"}
    ]


def _build_similarity(vectorstore, top_k: int, method: dict):
    # search_type 생략 = LangChain 기본값 "similarity" (순수 코사인 유사도 상위 k개).
    return vectorstore.as_retriever(search_kwargs={"k": top_k})


def _build_mmr(vectorstore, top_k: int, method: dict):
    """다양성을 섞어 뽑는다 (fetch_k개 후보에서 서로 안 닮은 top_k개 선택).

    주의: langchain_chroma는 MMR이 고른 "순서"를 버리고 유사도 순서로 재정렬해서
    돌려준다 (vectorstores.py의 `[r for i, r in enumerate(candidates) if i in
    mmr_selected]`). 그래서 이 검색법의 순위 기반 지표(reciprocal_rank, *_hit_1)는
    MMR의 순위가 아니라 유사도 순위를 잰다 - 1위는 항상 similarity와 같아진다.
    비교에 쓸 수 있는 건 "무엇이 뽑혔는가"에만 의존하는 page_hit_k와
    page_precision_k뿐이다. top_k를 바꾸면 잘라낸 결과와 직접 뽑은 결과가
    달라지는 것도 같은 이유다.
    """
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": top_k,
            "fetch_k": method.get("fetch_k", 20),
            "lambda_mult": method.get("lambda_mult", 0.5),
        },
    )


def _build_bm25(chunks: list, top_k: int, method: dict):
    tokenizer = method.get("tokenizer", "kiwi")
    if tokenizer == "kiwi":
        preprocess = kiwi_tokenize
    elif tokenizer == "whitespace":
        preprocess = str.split
    else:
        raise ValueError(f"지원하지 않는 bm25 tokenizer: {tokenizer}")

    return BM25Retriever.from_documents(chunks, preprocess_func=preprocess, k=top_k)


def build_retrievers(config: dict, vectorstore, chunks: list) -> dict:
    """검색법 이름 -> retriever 딕셔너리.

    BM25는 임베딩이 필요 없으므로 매번 메모리에서 구성한다.
    hybrid는 similarity + bm25를 EnsembleRetriever(RRF)로 합친다.
    """
    top_k = config["retrieval"]["top_k"]
    retrievers = {}

    for method in config["retrieval"]["methods"]:
        name = method["name"]

        if name == "similarity":
            retrievers[name] = _build_similarity(vectorstore, top_k, method)
        elif name == "mmr":
            retrievers[name] = _build_mmr(vectorstore, top_k, method)
        elif name == "bm25":
            retrievers[name] = _build_bm25(chunks, top_k, method)
        elif name == "hybrid":
            weights = method.get("weights", [0.5, 0.5])
            retrievers[name] = EnsembleRetriever(
                retrievers=[
                    _build_similarity(vectorstore, top_k, method),
                    _build_bm25(chunks, top_k, method),
                ],
                weights=weights,
                # 같은 청크가 양쪽에서 나와도 한 번만 세도록 하는 키.
                id_key="chunk_id",
            )
        else:
            raise ValueError(f"알 수 없는 검색법: {name}")

    return retrievers
