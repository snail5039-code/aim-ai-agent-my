"""실험 config 로드, 기본값 병합, CLI 오버라이드, 경로/해시 유틸."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

# rag/config.py -> rag/ -> 10-rag-evalution-script/
SCRIPT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = SCRIPT_DIR / "input"
DEFAULT_RESULT_DIR = SCRIPT_DIR / "output"

# config에 적지 않은 항목은 이 값이 쓰인다.
DEFAULT_CONFIG = {
    "experiment_name": None,
    "description": "",
    "data": {
        "document_dir": "../data/public",
        "document_glob": "*.pdf",
        "golden_set_path": "../data/public/public_paragraph_golden_set.json",
    },
    "chunking": {
        "chunk_size": 700,
        "chunk_overlap": 100,
        "separators": None,
    },
    "embedding": {
        "provider": "google",
        "model": "gemini-embedding-001",
    },
    "index": {
        "persist_dir": "./.index_cache",
        "rebuild": False,
    },
    "retrieval": {
        "top_k": 5,
        "methods": [{"name": "similarity"}],
    },
    "generation": {
        "enabled": True,
        "model": "gemini-3.6-flash",
        "temperature": 0.0,
        "max_concurrency": 4,     # 답변 생성 동시 실행 수 (429 방지)
    },
    "evaluation": {
        "retrieval": {
            "enabled": True,
            "k_list": [1, 3, 5],
        },
        "ragas": {
            "enabled": True,
            "metrics": ["faithfulness", "answer_relevancy"],
            "methods": None,          # None이면 retrieval.methods 전체
            "sample_size": None,      # None이면 전체 문항
            "max_concurrency": 4,
        },
    },
}

VALID_METHODS = {"similarity", "mmr", "bm25", "hybrid"}
VALID_RAGAS_METRICS = {"faithfulness", "answer_relevancy"}


def _deep_merge(base: dict, override: dict) -> dict:
    """base를 복사한 뒤 override를 재귀적으로 덮어쓴다. 리스트는 통째로 교체한다."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def resolve_config_path(name: str) -> Path:
    """`chunk_300`, `chunk_300.json`, `input/chunk_300.json`을 모두 받는다."""
    candidates = []
    given = Path(name)
    if given.suffix == ".json":
        candidates += [given, SCRIPT_DIR / given, CONFIG_DIR / given.name]
    else:
        candidates += [
            CONFIG_DIR / f"{name}.json",
            SCRIPT_DIR / f"{name}.json",
            Path(f"{name}.json"),
        ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    tried = "\n  ".join(str(c) for c in candidates)
    raise FileNotFoundError(f"config를 찾지 못했습니다: {name}\n찾아본 경로:\n  {tried}")


def resolve_path(value: str | Path) -> Path:
    """config에 적힌 상대경로는 스크립트 디렉토리 기준으로 해석한다(cwd 무관)."""
    path = Path(value)
    return path if path.is_absolute() else (SCRIPT_DIR / path).resolve()


def load_config(name: str) -> dict:
    config_path = resolve_config_path(name)
    user_config = json.loads(config_path.read_text(encoding="utf-8"))
    config = _deep_merge(DEFAULT_CONFIG, user_config)

    # experiment_name을 안 적었으면 파일명을 쓴다.
    if not config.get("experiment_name"):
        config["experiment_name"] = config_path.stem

    config["_config_path"] = str(config_path)
    return config


def apply_overrides(config: dict, args) -> dict:
    """CLI 플래그로 config 값을 덮어쓴다."""
    config = copy.deepcopy(config)

    if getattr(args, "document_path", None):
        config["data"]["document_dir"] = args.document_path
    if getattr(args, "experiment_name", None):
        config["experiment_name"] = args.experiment_name
    if getattr(args, "rebuild_index", False):
        config["index"]["rebuild"] = True
    if getattr(args, "retrieval_only", False):
        config["generation"]["enabled"] = False
        config["evaluation"]["ragas"]["enabled"] = False
    if getattr(args, "top_k", None):
        config["retrieval"]["top_k"] = args.top_k

    return config


def validate_config(config: dict) -> None:
    methods = config["retrieval"]["methods"]
    if not methods:
        raise ValueError("retrieval.methods가 비어 있습니다.")

    names = []
    for method in methods:
        name = method.get("name")
        if name not in VALID_METHODS:
            raise ValueError(
                f"알 수 없는 검색법 '{name}'. 가능한 값: {sorted(VALID_METHODS)}"
            )
        if name in names:
            raise ValueError(f"검색법 '{name}'이 중복 지정되었습니다.")
        names.append(name)

    for metric in config["evaluation"]["ragas"]["metrics"]:
        if metric not in VALID_RAGAS_METRICS:
            raise ValueError(
                f"알 수 없는 RAGAS 메트릭 '{metric}'. 가능한 값: {sorted(VALID_RAGAS_METRICS)}"
            )

    ragas_methods = config["evaluation"]["ragas"]["methods"]
    if ragas_methods:
        unknown = set(ragas_methods) - set(names)
        if unknown:
            raise ValueError(
                f"evaluation.ragas.methods에 retrieval.methods에 없는 검색법이 있습니다: {sorted(unknown)}"
            )

    chunking = config["chunking"]
    if chunking["chunk_overlap"] >= chunking["chunk_size"]:
        raise ValueError("chunk_overlap은 chunk_size보다 작아야 합니다.")

    # top_k보다 큰 k는 검색 결과가 그만큼 없어서 top_k일 때와 같은 값이 나온다.
    # 착각을 부르는 열이므로 아예 빼고 경고한다.
    top_k = config["retrieval"]["top_k"]
    k_list = sorted(set(config["evaluation"]["retrieval"]["k_list"]))
    usable = [k for k in k_list if k <= top_k]
    if not usable:
        raise ValueError(f"k_list {k_list}에 top_k({top_k}) 이하인 값이 없습니다.")
    if usable != k_list:
        dropped = [k for k in k_list if k > top_k]
        print(f"  [경고] top_k={top_k}보다 큰 k {dropped}는 계산에서 제외합니다.")
    config["evaluation"]["retrieval"]["k_list"] = usable


def index_signature(config: dict) -> str:
    """청킹/임베딩/문서가 같으면 같은 값이 나오는 인덱스 캐시 키."""
    payload = {
        "document_dir": str(resolve_path(config["data"]["document_dir"])),
        "document_glob": config["data"]["document_glob"],
        "chunking": config["chunking"],
        "embedding": config["embedding"],
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def ragas_target_methods(config: dict) -> list[str]:
    """RAGAS를 돌릴 검색법 목록. 미지정이면 전체."""
    configured = config["evaluation"]["ragas"]["methods"]
    all_names = [m["name"] for m in config["retrieval"]["methods"]]
    if not configured:
        return all_names
    return [name for name in all_names if name in configured]


def dump_config(config: dict) -> dict:
    """저장용 — 내부 키(_로 시작)는 뺀다."""
    return {k: v for k, v in config.items() if not k.startswith("_")}
