"""PDF 로드와 골든셋 로드.

메타데이터 정규화는 10-rag-evaluation-practice.ipynb 셀 7과 동일하게 맞춘다.
- source: 전체 경로가 아니라 파일명만 (골든셋의 target_file_name과 직접 비교)
- page_no: PyPDFLoader의 0-base page를 사람이 보는 1-base로

PDF 파싱은 이 스크립트에서 제일 느린 단계(236페이지에 12초)라서 결과를 캐시한다.
페이지는 청킹 조건과 무관하므로 chunk_300/500/700/1000을 연달아 돌려도 한 번만 읽는다.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from .config import SCRIPT_DIR, resolve_path

DEFAULT_PAGE_CACHE_DIR = SCRIPT_DIR / ".page_cache"


def pages_signature(pdf_paths: list[Path], document_glob: str) -> str:
    """PDF 목록이 같으면 같은 값이 나오는 페이지 캐시 키.

    index_signature와 같은 방식이다. 파일이 바뀌면 mtime이나 크기가 달라지므로
    캐시가 자동으로 무효화된다.
    """
    payload = {
        "glob": document_glob,
        "files": [
            [path.name, path.stat().st_mtime_ns, path.stat().st_size]
            for path in pdf_paths
        ],
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def _parse_pdfs(pdf_paths: list[Path]) -> list:
    page_documents = []
    for pdf_path in pdf_paths:
        pages = PyPDFLoader(pdf_path).load()
        for page in pages:
            page.metadata["source"] = Path(page.metadata["source"]).name
            page.metadata["page_no"] = page.metadata["page"] + 1
        page_documents.extend(pages)
    return page_documents


def load_pages(
    document_dir: str,
    document_glob: str = "*.pdf",
    cache_dir: str | Path | None = None,
) -> list:
    """문서 디렉토리의 PDF를 페이지 단위 Document로 읽는다 (캐시 사용)."""
    directory = resolve_path(document_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"문서 디렉토리가 없습니다: {directory}")

    pdf_paths = sorted(directory.glob(document_glob))
    if not pdf_paths:
        raise FileNotFoundError(f"문서를 찾지 못했습니다: {directory / document_glob}")

    cache_root = resolve_path(cache_dir) if cache_dir else DEFAULT_PAGE_CACHE_DIR
    signature = pages_signature(pdf_paths, document_glob)
    cache_path = cache_root / f"pages_{signature}.json"

    if cache_path.is_file():
        try:
            records = json.loads(cache_path.read_text(encoding="utf-8"))
            print(f"  페이지 캐시 재사용: {cache_path.name} ({len(records)}페이지)")
            return [
                Document(
                    page_content=record["page_content"], metadata=record["metadata"]
                )
                for record in records
            ]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            # 캐시가 깨졌으면 조용히 버리고 다시 읽는다.
            print(f"  [경고] 페이지 캐시를 읽지 못해 다시 파싱합니다: {error}")

    started = time.perf_counter()
    page_documents = _parse_pdfs(pdf_paths)
    parse_sec = round(time.perf_counter() - started, 1)

    cache_root.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            [
                {"page_content": page.page_content, "metadata": page.metadata}
                for page in page_documents
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(
        f"  페이지 캐시 생성: {cache_path.name} "
        f"({len(page_documents)}페이지, 파싱 {parse_sec}초)"
    )

    return page_documents


def load_golden_set(golden_set_path: str, limit: int | None = None) -> list[dict]:
    """골든셋 JSON을 읽는다. limit을 주면 앞에서 그만큼만 (스모크 테스트용)."""
    path = resolve_path(golden_set_path)
    if not path.is_file():
        raise FileNotFoundError(f"골든셋이 없습니다: {path}")

    cases = json.loads(path.read_text(encoding="utf-8"))

    required = {"question", "target_file_name", "target_page_no"}
    missing = required - set(cases[0])
    if missing:
        raise ValueError(f"골든셋에 필수 필드가 없습니다: {sorted(missing)}")

    return cases[:limit] if limit else cases
