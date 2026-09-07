"""RAG 실험 실행기.

config 파일 하나 = 실험 하나. 청킹 조건 하나 위에서 여러 검색법을 비교한다.

    python main.py --config chunk_300
    python main.py --config chunk_300 chunk_500 chunk_700 chunk_1000
    python main.py --config chunk_300 --retrieval-only --limit 3
    python main.py --compare
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

from rag import report
from rag.chunking import chunk_stats, split_pages
from rag.config import (
    DEFAULT_RESULT_DIR,
    SCRIPT_DIR,
    apply_overrides,
    dump_config,
    load_config,
    ragas_target_methods,
    resolve_path,
    validate_config,
)
from rag.data import load_golden_set, load_pages
from rag.generation import build_llm, generate_answers
from rag.index import get_vectorstore
from rag.metrics import evaluate_retriever, find_failures, summarize
from rag.ragas_eval import run_ragas, summarize_ragas
from rag.retrievers import build_retrievers

RAGAS_METRIC_NAMES = ("faithfulness", "answer_relevancy")


def quiet_library_noise() -> None:
    """실행 결과와 상관없는 라이브러리 경고를 진행 출력에서 걷어낸다.

    - gemini-3.x는 sampling 파라미터를 고정값으로 쓰기 때문에 temperature를 무시한다는
      UserWarning이 LLM 호출마다 뜬다. config의 temperature는 다른 모델에서 여전히
      의미가 있으므로 설정은 두고 경고만 끈다.
    - google-genai는 generate_content를 직접 부르면 AFC 권고 로그를 남긴다.
      LangChain이 대신 호출하는 구조라 우리가 바꿀 수 있는 부분이 아니다.
    """
    warnings.filterwarnings(
        "ignore",
        message=r"Model .* uses fixed sampling defaults",
        category=UserWarning,
    )
    logging.getLogger("google_genai.models").setLevel(logging.ERROR)


def setup_environment() -> None:
    quiet_library_noise()

    # 한글 출력이 깨지지 않도록.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # .env는 langchain_/.env를 쓴다 (GEMINI_API_KEY가 여기 있다).
    load_dotenv(SCRIPT_DIR.parent / ".env", override=True)

    # langchain-google-genai와 google-genai 모두 GOOGLE_API_KEY를 먼저 보고
    # 없으면 GEMINI_API_KEY로 넘어간다. 둘 다 설정하면 "Both ... are set" 경고가
    # 뜨므로 굳이 맞춰 넣지 않고, 하나라도 있는지만 확인한다.
    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        print(
            "[경고] GEMINI_API_KEY(또는 GOOGLE_API_KEY)가 없습니다. "
            f"{SCRIPT_DIR.parent / '.env'}를 확인하세요."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RAG 실험 실행기 - config로 청킹/검색법/평가 조건을 바꿔가며 비교한다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--config",
        nargs="+",
        metavar="NAME",
        help="실행할 config. chunk_300 / chunk_300.json / input/chunk_300.json 모두 가능. "
        "여러 개를 주면 순차 실행 후 비교표를 출력한다.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="이미 저장된 output/*/summary.json을 모아 비교표만 출력한다.",
    )

    override = parser.add_argument_group("config 오버라이드")
    override.add_argument("--document-path", help="검색 대상 문서 디렉토리 (data.document_dir)")
    override.add_argument("--result-dir", help="결과 저장 디렉토리 (기본: ./output)")
    override.add_argument("--experiment-name", help="실험 이름 (기본: config 파일명)")
    override.add_argument("--top-k", type=int, help="검색 결과 개수 (retrieval.top_k)")

    run = parser.add_argument_group("실행 옵션")
    run.add_argument(
        "--retrieval-only",
        action="store_true",
        help="답변 생성과 RAGAS를 건너뛰고 검색 평가만 한다 (LLM 호출 없음).",
    )
    run.add_argument("--limit", type=int, help="골든셋 앞 N문항만 사용 (스모크 테스트용)")
    run.add_argument(
        "--rebuild-index", action="store_true", help="인덱스 캐시를 무시하고 다시 만든다."
    )

    args = parser.parse_args()
    if not args.config and not args.compare:
        parser.error("--config 또는 --compare 중 하나는 필요합니다.")
    if args.experiment_name and args.config and len(args.config) > 1:
        parser.error("--experiment-name은 config를 하나만 지정했을 때만 쓸 수 있습니다.")
    return args


def run_experiment(config: dict, args: argparse.Namespace, result_dir: Path) -> dict:
    name = config["experiment_name"]
    if args.limit:
        # 일부 문항만 돌린 결과가 전체 실행 결과를 덮어쓰지 않도록 따로 저장한다.
        name = f"{name}_limit{args.limit}"
    k_list = config["evaluation"]["retrieval"]["k_list"]
    top_k = config["retrieval"]["top_k"]

    print(f"\n{'=' * 70}")
    print(f"실험: {name}")
    if config.get("description"):
        print(f"      {config['description']}")
    method_names = [method["name"] for method in config["retrieval"]["methods"]]
    chunking = config["chunking"]
    print(
        f"      청크 {chunking['chunk_size']}/{chunking['chunk_overlap']}"
        f", top_k={top_k}, 검색법={method_names}"
    )
    print("=" * 70)

    # 1. 문서 로드
    pages = load_pages(config["data"]["document_dir"], config["data"]["document_glob"])
    cases = load_golden_set(config["data"]["golden_set_path"], args.limit)
    print(f"  로드한 페이지: {len(pages)}개 / 평가 문항: {len(cases)}개")

    # 2. 청킹
    chunks = split_pages(pages, chunking)
    corpus = chunk_stats(pages, chunks)
    print(f"  생성한 청크: {corpus['num_chunks']}개 (평균 {corpus['avg_chunk_chars']}자)")

    # 3. 인덱싱 (청킹/임베딩이 같으면 재사용)
    vectorstore, index_info = get_vectorstore(chunks, config)

    # 4. 검색기 구성
    retrievers = build_retrievers(config, vectorstore, chunks)

    # 5. 검색 평가
    all_rows = []
    docs_by_method = {}
    summaries = []

    for method_name, retriever in retrievers.items():
        print(f"  검색 평가: {method_name}")
        rows, retrieved_docs = evaluate_retriever(
            method_name, retriever, cases, k_list, top_k
        )
        all_rows.extend(rows)
        docs_by_method[method_name] = retrieved_docs

        summary = {
            "experiment": name,
            "chunk_size": chunking["chunk_size"],
            "chunk_overlap": chunking["chunk_overlap"],
        }
        summary.update(summarize(method_name, rows, k_list))
        summaries.append(summary)

    # 6~7. 답변 생성 + RAGAS
    generation_records = {}
    ragas_rows = {}

    if config["generation"]["enabled"] and config["evaluation"]["ragas"]["enabled"]:
        targets = ragas_target_methods(config)
        sample_size = config["evaluation"]["ragas"]["sample_size"]
        ragas_cases = cases[:sample_size] if sample_size else cases
        llm = build_llm(config["generation"])

        for method_name in targets:
            print(f"  답변 생성: {method_name} ({len(ragas_cases)}문항)")
            records = generate_answers(
                llm,
                ragas_cases,
                docs_by_method[method_name][: len(ragas_cases)],
                max_concurrency=config["generation"].get("max_concurrency", 4),
            )
            generation_records[method_name] = records

            print(f"  RAGAS 채점: {method_name}")
            scores = run_ragas(records, config)
            ragas_rows[method_name] = scores

            ragas_summary = summarize_ragas(
                scores, config["evaluation"]["ragas"]["metrics"]
            )
            for summary in summaries:
                if summary["name"] == method_name:
                    summary.update(ragas_summary)

    # 8. 저장 + 출력
    experiment_dir = result_dir / name
    payload = {
        "experiment_name": name,
        "description": config.get("description", ""),
        "chunking": chunking,
        "embedding": config["embedding"],
        "retrieval": config["retrieval"],
        "k_list": k_list,
        "corpus": corpus,
        "index": index_info,
        "num_cases": len(cases),
        "retrievers": summaries,
    }

    report.save_json(experiment_dir / "config.used.json", dump_config(config))
    report.save_json(experiment_dir / "summary.json", payload)
    report.save_json(experiment_dir / "retrieval_detail.json", all_rows)

    failures, failure_k = find_failures(all_rows, k_list)
    report.save_json(experiment_dir / "failures.json", failures)

    if generation_records:
        report.save_json(experiment_dir / "generation.json", generation_records)
    if ragas_rows:
        report.save_json(experiment_dir / "ragas_detail.json", ragas_rows)

    report.show_table(
        summaries,
        report.summary_columns(k_list, present_ragas_metrics(summaries)),
        title=f"[{name}] 검색법별 요약",
    )
    report.show_failures(failures, failure_k)
    print(f"\n  결과 저장: {experiment_dir}")

    return payload


def present_ragas_metrics(rows: list[dict]) -> list[str]:
    """실제로 채점된 RAGAS 메트릭만 표 열로 넣는다."""
    return [name for name in RAGAS_METRIC_NAMES if any(name in row for row in rows)]


def main() -> int:
    setup_environment()
    args = parse_args()

    result_dir = resolve_path(args.result_dir) if args.result_dir else DEFAULT_RESULT_DIR

    if args.compare and not args.config:
        rows, k_list = report.collect_summaries(result_dir)
        if not rows:
            print(f"비교할 결과가 없습니다: {result_dir}")
            return 1
        columns = ["experiment", "chunk_size"] + report.summary_columns(
            k_list, present_ragas_metrics(rows)
        )
        report.show_table(rows, columns, title="저장된 실험 비교")
        return 0

    # config 오타나 잘못된 값은 사용자 실수이므로 스택 트레이스 대신 한 줄로 알린다.
    configs = []
    for name in args.config:
        try:
            config = apply_overrides(load_config(name), args)
            validate_config(config)
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
            print(f"\n[오류] config '{name}': {error}")
            return 1
        configs.append(config)

    payloads = [run_experiment(config, args, result_dir) for config in configs]

    if len(payloads) > 1:
        rows = [row for payload in payloads for row in payload["retrievers"]]
        columns = ["experiment", "chunk_size"] + report.summary_columns(
            payloads[0]["k_list"], present_ragas_metrics(rows)
        )
        report.show_table(rows, columns, title="전체 비교")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
