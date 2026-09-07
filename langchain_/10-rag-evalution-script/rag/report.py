"""콘솔 표 출력과 결과 JSON 저장."""

from __future__ import annotations

import json
from pathlib import Path


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _cell(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def show_table(rows: list[dict], columns: list[str], title: str = "") -> None:
    """딕셔너리 리스트를 고정폭 표로 출력한다."""
    if not rows:
        print("(출력할 행이 없습니다)")
        return

    if title:
        print(f"\n{title}")

    widths = {}
    for column in columns:
        cells = [_cell(row.get(column)) for row in rows]
        widths[column] = max(len(column), *(len(c) for c in cells))

    header = " | ".join(column.rjust(widths[column]) for column in columns)
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            " | ".join(
                _cell(row.get(column)).rjust(widths[column]) for column in columns
            )
        )


def summary_columns(k_list: list[int], extra: list[str]) -> list[str]:
    """요약 표에 보여줄 열 순서."""
    columns = ["name", "count"]
    columns += [f"file_hit_{k}" for k in k_list]
    columns += [f"page_hit_{k}" for k in k_list]
    columns += [f"page_precision_{k}" for k in k_list]
    columns += ["reciprocal_rank", "latency_ms"]
    columns += extra
    return columns


def show_failures(failures: list[dict], k: int = 5, limit: int = 5) -> None:
    """실패 문항과 그때 실제로 뭐가 검색됐는지 보여준다."""
    if not failures:
        print()
        print(f"실패 문항 없음 (모든 문항에서 정답 페이지를 상위 {k}개 안에 찾았습니다)")
        return

    shown = min(limit, len(failures))
    print()
    print(f"실패 문항 {len(failures)}건 (page_hit_{k} == 0) - 앞 {shown}건:")
    for row in failures[:limit]:
        print()
        print(f"  [{row['name']}] {row['question'][:70]}...")
        print(f"    정답: {row['target_file_name']} p.{row['target_page_no']}")
        for item in row["retrieved"][:3]:
            print(f"    {item['rank']}위: {item['source']} p.{item['page_no']}")


def collect_summaries(result_dir: Path) -> tuple[list[dict], list[int]]:
    """output/ 밑에 저장된 summary.json들을 모은다 (--compare용).

    Returns:
        (검색법 요약 행 전체, k_list) - k_list는 표 열 순서를 만드는 데 쓴다.
    """
    collected = []
    k_list = [1, 3, 5]

    for summary_path in sorted(result_dir.glob("*/summary.json")):
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        collected.extend(payload.get("retrievers", []))
        if payload.get("k_list"):
            k_list = payload["k_list"]

    # 청크 크기 -> 검색법 순으로 정렬해야 비교표가 읽힌다.
    collected.sort(key=lambda row: (row.get("chunk_size", 0), row.get("name", "")))
    return collected, k_list
