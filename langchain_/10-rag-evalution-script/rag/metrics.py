"""검색 평가 지표.

필드명과 요약 스키마는 10-rag-evaluation-practice.ipynb 셀 14/16/19를 그대로 따른다.
(file_hit_1, page_hit_1, page_hit_3, page_hit_5, reciprocal_rank, latency_ms, count)

recall@k는 계산하지 않는다. 이 골든셋은 정답 근거가 (파일, 페이지) 단 하나뿐이라
정답 집합 크기가 1이고, 그러면 recall@k가 page_hit_k와 같은 값이 되기 때문이다.
대신 page_precision_k를 추가했다 - 청크가 작아질수록 같은 페이지의 청크가
상위를 채우는 현상을 잡아내므로 청킹 실험 해석에 쓰인다.
"""

from __future__ import annotations

import time


def _file_match(doc, case: dict) -> bool:
    return doc.metadata.get("source") == case["target_file_name"]


def _page_match(doc, case: dict) -> bool:
    return _file_match(doc, case) and doc.metadata.get("page_no") == case["target_page_no"]


def file_hit_at_k(docs: list, case: dict, k: int) -> int:
    """상위 k개 안에 정답 파일이 있으면 1."""
    return int(any(_file_match(doc, case) for doc in docs[:k]))


def page_hit_at_k(docs: list, case: dict, k: int) -> int:
    """상위 k개 안에 정답 파일 + 정답 페이지가 있으면 1."""
    return int(any(_page_match(doc, case) for doc in docs[:k]))


def page_precision_at_k(docs: list, case: dict, k: int) -> float:
    """상위 k개 중 정답 페이지에서 온 청크의 비율."""
    selected = docs[:k]
    if not selected:
        return 0.0
    return sum(_page_match(doc, case) for doc in selected) / len(selected)


def reciprocal_rank(docs: list, case: dict) -> float:
    """정답 페이지가 처음 등장한 순위의 역수. 없으면 0.0."""
    for rank, doc in enumerate(docs, start=1):
        if _page_match(doc, case):
            return 1 / rank
    return 0.0


def evaluate_retriever(
    name: str,
    retriever,
    cases: list[dict],
    k_list: list[int],
    top_k: int,
) -> tuple[list[dict], list[list]]:
    """문항별 검색 + 지표 계산.

    Returns:
        (rows, retrieved_docs) - rows는 JSON 저장용, retrieved_docs는
        생성/RAGAS 단계에서 컨텍스트로 쓸 Document 리스트(직렬화 불가)다.
    """
    rows = []
    retrieved_docs = []

    for case in cases:
        started = time.perf_counter()
        docs = retriever.invoke(case["question"])
        latency_ms = (time.perf_counter() - started) * 1000

        # hybrid(EnsembleRetriever)는 융합 결과가 top_k보다 길 수 있어
        # 검색법 간 비교가 공정하도록 여기서 잘라낸다.
        docs = docs[:top_k]
        retrieved_docs.append(docs)

        row = {
            "name": name,
            "question": case["question"],
            "target_file_name": case["target_file_name"],
            "target_page_no": case["target_page_no"],
        }
        for k in k_list:
            row[f"file_hit_{k}"] = file_hit_at_k(docs, case, k)
        for k in k_list:
            row[f"page_hit_{k}"] = page_hit_at_k(docs, case, k)
        for k in k_list:
            row[f"page_precision_{k}"] = page_precision_at_k(docs, case, k)

        row["reciprocal_rank"] = reciprocal_rank(docs, case)
        row["latency_ms"] = latency_ms
        row["retrieved"] = [
            {
                "rank": rank,
                "source": doc.metadata.get("source"),
                "page_no": doc.metadata.get("page_no"),
            }
            for rank, doc in enumerate(docs, start=1)
        ]
        rows.append(row)

    return rows, retrieved_docs


def metric_keys(k_list: list[int]) -> list[str]:
    """요약에 평균으로 들어갈 지표 필드 순서."""
    keys = [f"file_hit_{k}" for k in k_list]
    keys += [f"page_hit_{k}" for k in k_list]
    keys += [f"page_precision_{k}" for k in k_list]
    keys += ["reciprocal_rank", "latency_ms"]
    return keys


def average(rows: list[dict], key: str) -> float:
    return sum(row[key] for row in rows) / len(rows) if rows else 0.0


def summarize(name: str, rows: list[dict], k_list: list[int]) -> dict:
    """검색법 하나에 대한 요약 행 (노트북 셀 19 스키마)."""
    summary = {"name": name, "count": len(rows)}
    for key in metric_keys(k_list):
        summary[key] = round(average(rows, key), 4)
    return summary


def find_failures(rows: list[dict], k_list: list[int]) -> tuple[list[dict], int]:
    """정답 페이지를 상위 k개 안에서 못 찾은 문항.

    기준 노트북은 page_hit_5 == 0을 썼다. 여기서는 k_list의 최댓값을 쓰므로
    기본 설정([1, 3, 5])에서는 노트북과 같은 기준이 된다.

    Returns:
        (실패 행 목록, 사용한 k)
    """
    k = max(k_list)
    key = f"page_hit_{k}"
    if not rows or key not in rows[0]:
        return [], k
    return [row for row in rows if row[key] == 0], k
