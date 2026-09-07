"""검색 지표 단위 테스트.

지표가 틀리면 실험 결론이 전부 무의미해지므로 여기가 1순위다.
API도 문서도 필요 없다 - 가짜 Document 몇 개로 끝난다.

    python tests/test_metrics.py     # pytest 없이
    pytest tests/                    # pytest 있으면
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.metrics import (  # noqa: E402
    file_hit_at_k,
    find_failures,
    page_hit_at_k,
    page_precision_at_k,
    reciprocal_rank,
    summarize,
)


class FakeDoc:
    """metadata만 쓰는 지표 함수에는 이걸로 충분하다."""

    def __init__(self, source: str, page_no: int):
        self.metadata = {"source": source, "page_no": page_no}
        self.page_content = ""


CASE = {"target_file_name": "a.pdf", "target_page_no": 15}

# 정답(a.pdf p.15)이 1, 2, 5위에 있고 3위는 같은 파일 다른 페이지, 4위는 다른 파일.
DOCS = [
    FakeDoc("a.pdf", 15),
    FakeDoc("a.pdf", 15),
    FakeDoc("a.pdf", 10),
    FakeDoc("b.pdf", 1),
    FakeDoc("a.pdf", 15),
]


def test_file_hit_ignores_page():
    # 3위는 페이지가 틀려도 파일은 맞다.
    assert file_hit_at_k([DOCS[2]], CASE, 1) == 1
    # 다른 파일만 있으면 0.
    assert file_hit_at_k([DOCS[3]], CASE, 1) == 0


def test_page_hit_needs_both():
    assert page_hit_at_k(DOCS, CASE, 1) == 1
    assert page_hit_at_k(DOCS[2:], CASE, 1) == 0  # 3위(p.10)만 보면 실패
    assert page_hit_at_k(DOCS[2:], CASE, 3) == 1  # 5위까지 보면 성공


def test_page_precision_counts_not_exists():
    # 상위 5개 중 정답 페이지는 3개(1, 2, 5위).
    assert page_precision_at_k(DOCS, CASE, 5) == 3 / 5
    assert page_precision_at_k(DOCS, CASE, 3) == 2 / 3
    assert page_precision_at_k(DOCS, CASE, 1) == 1.0
    assert page_precision_at_k([], CASE, 5) == 0.0


def test_precision_at_1_equals_hit_at_1():
    """k=1에서는 두 지표가 수학적으로 같다 - 표의 두 열이 늘 같은 이유."""
    for docs in ([DOCS[0]], [DOCS[2]], [DOCS[3]], DOCS):
        assert page_precision_at_k(docs, CASE, 1) == page_hit_at_k(docs, CASE, 1)


def test_reciprocal_rank_uses_first_occurrence():
    assert reciprocal_rank(DOCS, CASE) == 1.0  # 1위
    assert reciprocal_rank(DOCS[1:], CASE) == 1.0  # 잘라도 1위
    assert reciprocal_rank(DOCS[2:], CASE) == 1 / 3  # p.10, b.pdf, p.15 -> 3위
    assert reciprocal_rank([FakeDoc("b.pdf", 1)], CASE) == 0.0  # 못 찾으면 0


def test_reciprocal_rank_ignores_later_duplicates():
    """정답이 2위와 4위에 나와도 RR은 2위 기준."""
    docs = [FakeDoc("a.pdf", 8), FakeDoc("a.pdf", 15), FakeDoc("a.pdf", 8), FakeDoc("a.pdf", 15)]
    assert reciprocal_rank(docs, CASE) == 0.5


def test_summarize_averages_and_rounds():
    rows = [
        {"page_hit_1": 1, "page_precision_1": 1.0, "reciprocal_rank": 1.0, "latency_ms": 10.0,
         "file_hit_1": 1},
        {"page_hit_1": 0, "page_precision_1": 0.0, "reciprocal_rank": 0.5, "latency_ms": 20.0,
         "file_hit_1": 1},
    ]
    summary = summarize("similarity", rows, [1])
    assert summary["name"] == "similarity"
    assert summary["count"] == 2
    assert summary["page_hit_1"] == 0.5
    assert summary["reciprocal_rank"] == 0.75
    assert summary["latency_ms"] == 15.0


def test_find_failures_uses_max_k():
    rows = [
        {"page_hit_1": 1, "page_hit_3": 1, "q": "찾음"},
        {"page_hit_1": 0, "page_hit_3": 0, "q": "못찾음"},
    ]
    failures, k = find_failures(rows, [1, 3])
    assert k == 3
    assert [row["q"] for row in failures] == ["못찾음"]
    assert find_failures([], [1, 3]) == ([], 3)


if __name__ == "__main__":
    tests = [v for name, v in sorted(globals().items()) if name.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
        except AssertionError as error:
            failed += 1
            print(f"  FAIL  {test.__name__}: {error}")
    print(f"\n{len(tests) - failed}/{len(tests)} 통과")
    raise SystemExit(1 if failed else 0)
