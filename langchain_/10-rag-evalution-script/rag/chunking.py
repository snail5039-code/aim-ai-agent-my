"""페이지 Document를 청크로 분할하고 chunk_id를 부여한다."""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_pages(pages: list, chunking: dict) -> list:
    """config의 chunking 설정으로 분할한다.

    split_documents는 문서(=페이지)별로 나누므로 청크가 페이지 경계를 넘지 않는다.
    덕분에 page_no 메타데이터가 그대로 보존되어 페이지 단위 채점이 가능하다.
    """
    kwargs = {
        "chunk_size": chunking["chunk_size"],
        "chunk_overlap": chunking["chunk_overlap"],
    }
    # separators를 지정하지 않으면 RecursiveCharacterTextSplitter 기본값을 쓴다.
    if chunking.get("separators"):
        kwargs["separators"] = chunking["separators"]

    splitter = RecursiveCharacterTextSplitter(**kwargs)
    chunks = splitter.split_documents(pages)

    # EnsembleRetriever가 dense/bm25 결과를 합칠 때 중복 제거 키로 쓴다.
    for index, chunk in enumerate(chunks):
        source = chunk.metadata.get("source", "?")
        page_no = chunk.metadata.get("page_no", "?")
        chunk.metadata["chunk_id"] = f"{source}:p{page_no}:c{index}"

    return chunks


def chunk_stats(pages: list, chunks: list) -> dict:
    """청킹 조건 간 비교에 쓰는 통계."""
    total_chars = sum(len(chunk.page_content) for chunk in chunks)
    return {
        "num_pages": len(pages),
        "num_chunks": len(chunks),
        "avg_chunk_chars": round(total_chars / len(chunks), 1) if chunks else 0.0,
    }
