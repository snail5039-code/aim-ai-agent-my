# RAG 실험 스크립트

공공문서 RAG 파이프라인을 **config 파일로 조건을 바꿔가며** 실행하고 결과를 비교하는 CLI 도구.
`10-rag-evaluation-practice.ipynb`의 평가 로직을 그대로 옮기되, 청킹·검색법·평가 조건을 코드에서 분리했다.

- 검색 대상: `../data/public/*.pdf` (11개, 236페이지)
- 평가 데이터: `../data/public/public_paragraph_golden_set.json` (35문항, 정답 = 파일명 + 페이지번호)
- **config 하나 = 청킹 조건 하나.** 그 안에서 여러 검색법(similarity/mmr/bm25/hybrid)을 한 번에 비교한다.

---

## 실행 환경

**인터프리터: 시스템 Python 3.13.15** — `C:\Users\snail\AppData\Local\Programs\Python\Python313\python.exe`

langchain 계열·chromadb·ragas·kiwipiepy가 전부 여기에 설치돼 있고, `python`이 이걸 가리킨다.

```powershell
PS> (Get-Command python).Source
C:\Users\snail\AppData\Local\Programs\Python\Python313\python.exe
PS> python -V
Python 3.13.15
```

원래는 pyenv shim(3.13.13)이 `python`을 가로챘고 거기엔 langchain이 없어서
`ModuleNotFoundError: No module named 'langchain_chroma'`가 났다.
사용자 PATH에서 **pyenv 항목을 Python313 뒤로 옮겨서** 해결했다
(pyenv-win에는 `pyenv global system` 같은 게 없다 — 설치된 버전이나 `--unset`만 받는다).

현재 사용자 PATH 순서:

```
1. ...\Programs\Python\Python313\Scripts\
2. ...\Programs\Python\Python313\        <- python이 여기서 잡힌다
3. ...\.pyenv\pyenv-win\bin
4. ...\.pyenv\pyenv-win\shims
```

`pyenv` 명령 자체는 그대로 동작한다. 다만 pyenv로 설치한 파이썬이 `python`으로 잡히지는 않는다.
되돌리려면 PATH에서 pyenv 두 항목을 다시 맨 앞으로 올리면 된다.

`run.ps1`도 있다. PATH와 무관하게 항상 올바른 인터프리터로 실행하므로,
환경이 다시 꼬이거나 다른 PC에서 돌릴 때 쓰면 된다.

```powershell
.\run.ps1 --config chunk_700 --retrieval-only --limit 3
```

API 키는 `langchain_/.env`의 `GEMINI_API_KEY`를 읽는다 (스크립트가 알아서 로드한다).

---

## 빠른 시작

이 폴더로 이동한 뒤 실행한다.

```powershell
cd "C:\Users\snail\OneDrive\바탕 화면\aim-ai-agent-my\langchain_\10-rag-evalution-script"

# 옵션 전체 보기
python main.py --help

# 검색 평가만, 앞 3문항으로 빠르게 확인 (LLM 호출 없음)
python main.py --config chunk_300 --retrieval-only --limit 3

# 검색 평가 전체 (35문항 x 4개 검색법, LLM 호출 없음)
python main.py --config chunk_700 --retrieval-only

# 검색 + 답변 생성 + RAGAS 전체 (LLM 호출 많음, 몇 분 걸림)
python main.py --config chunk_700

# 청크 크기 4종을 순차 실행하고 16행 비교표 출력
python main.py --config chunk_300 chunk_500 chunk_700 chunk_1000 --retrieval-only

# 이미 저장된 결과만 모아서 비교표 출력
python main.py --compare
```

처음 돌리는 청크 조건은 임베딩을 하느라 10~30초 걸린다.
같은 조건을 다시 돌리면 인덱스를 재사용하므로 바로 시작한다.

### CLI 옵션

| 옵션 | 설명 |
|---|---|
| `--config NAME [NAME ...]` | 실행할 config. `chunk_300` / `chunk_300.json` / `input/chunk_300.json` 모두 됨 |
| `--compare` | `output/*/summary.json`을 모아 비교표만 출력 |
| `--retrieval-only` | 답변 생성·RAGAS를 건너뛴다 (LLM 호출 0회, 빠르고 무료) |
| `--limit N` | 골든셋 앞 N문항만. 결과는 `output/<이름>_limitN/`에 따로 저장되어 전체 실행 결과를 덮어쓰지 않는다 |
| `--rebuild-index` | 인덱스 캐시를 무시하고 다시 임베딩 |
| `--top-k N` | 검색 결과 개수 |
| `--document-path` / `--result-dir` / `--experiment-name` | config 값 오버라이드 |

---

## config 스키마

`input/chunk_700.json` 기준. 적지 않은 항목은 `rag/config.py`의 `DEFAULT_CONFIG` 값이 쓰인다.

```json
{
  "experiment_name": "chunk_700",
  "description": "청크 700/100에서 4개 검색 전략 비교",

  "data": {
    "document_dir": "../data/public",
    "document_glob": "*.pdf",
    "golden_set_path": "../data/public/public_paragraph_golden_set.json"
  },

  "chunking": {
    "chunk_size": 700,
    "chunk_overlap": 100,
    "separators": null
  },

  "embedding": { "provider": "google", "model": "gemini-embedding-001" },

  "index": { "persist_dir": "./.index_cache", "rebuild": false },

  "retrieval": {
    "top_k": 5,
    "methods": [
      { "name": "similarity" },
      { "name": "mmr", "fetch_k": 20, "lambda_mult": 0.5 },
      { "name": "bm25", "tokenizer": "kiwi" },
      { "name": "hybrid", "weights": [0.5, 0.5] }
    ]
  },

  "generation": { "enabled": true, "model": "gemini-3.6-flash", "temperature": 0.0 },

  "evaluation": {
    "retrieval": { "enabled": true, "k_list": [1, 3, 5] },
    "ragas": {
      "enabled": true,
      "metrics": ["faithfulness", "answer_relevancy"],
      "methods": ["similarity", "hybrid"],
      "sample_size": null,
      "max_concurrency": 4
    }
  }
}
```

몇 가지 규칙:

- `data.*`의 상대경로는 **이 스크립트 폴더 기준**으로 해석한다. 어느 디렉토리에서 실행하든 같게 동작한다.
- `retrieval.methods`는 배열이다. 임베딩은 청킹 조건에만 의존하므로 config당 한 번만 하고, 그 인덱스 위에서 검색법을 차례로 평가한다. 그래서 검색법을 늘려도 임베딩 비용은 그대로다.
- `evaluation.ragas.methods`로 RAGAS 채점 대상을 좁힐 수 있다. RAGAS는 문항당 LLM을 여러 번 부르므로 검색법 4개 전부에 돌리면 비싸다. 생략하면 전체가 대상이 된다.
- `evaluation.ragas.sample_size`로 RAGAS만 앞 N문항으로 줄일 수 있다 (검색 평가는 전체 유지).
- `k_list`에 `top_k`보다 큰 값이 있으면 경고와 함께 제외한다. 검색 결과가 top_k개뿐이라 그보다 큰 k는 top_k일 때와 같은 값이 나와서 착각을 부르기 때문이다.

기본 제공 config 4종 (청크 크기만 다르고 나머지는 동일 — 청크 크기를 통제 변수로 남긴 것):

| config | chunk_size | chunk_overlap | 청크 수 |
|---|---|---|---|
| `chunk_300.json` | 300 | 50 | 851 |
| `chunk_500.json` | 500 | 70 | 530 |
| `chunk_700.json` | 700 | 100 | 402 (기준 노트북과 동일) |
| `chunk_1000.json` | 1000 | 150 | 309 |

---

## 출력

`output/<experiment_name>/`에 저장된다.

| 파일 | 내용 |
|---|---|
| `config.used.json` | CLI 오버라이드까지 반영된 실제 적용 config |
| `summary.json` | 검색법별 요약 + 코퍼스/인덱스 통계 (`--compare`가 읽는 파일) |
| `retrieval_detail.json` | 문항 × 검색법 전체. 각 행에 검색 결과 순위·파일·페이지가 들어있어 실패 원인을 볼 수 있다 |
| `failures.json` | 정답 페이지를 상위 k개 안에서 못 찾은 문항 |
| `generation.json` | 생성한 답변과 그때 쓴 컨텍스트 (RAGAS 실행 시에만) |
| `ragas_detail.json` | 문항별 RAGAS 점수 (RAGAS 실행 시에만) |

---

## 지표

기준 노트북(`10-rag-evaluation-practice.ipynb`)의 필드명을 그대로 쓴다.

| 필드 | 정의 |
|---|---|
| `file_hit_{k}` | 상위 k개 안에 정답 **파일**이 있으면 1 |
| `page_hit_{k}` | 상위 k개 안에 정답 **파일 + 페이지**가 있으면 1 |
| `reciprocal_rank` | 정답 페이지가 처음 등장한 순위의 역수. 평균이 MRR |
| `latency_ms` | 질의당 검색 시간 |
| `page_precision_{k}` | 상위 k개 중 정답 페이지에서 온 청크 비율 (노트북에 없던 추가 지표) |

**recall@k는 없다.** 이 골든셋은 정답 근거가 `(파일, 페이지)` 단 하나뿐이라 정답 집합 크기가 1이고,
그러면 `recall@k`가 `page_hit_k`와 항상 같은 값이 된다. 같은 숫자를 두 열로 보여줄 이유가 없다.

대신 넣은 `page_precision_k`는 청크 크기 실험에서 실제로 일한다.
청크를 잘게 쪼갤수록 같은 페이지의 청크들이 상위를 함께 채우는데, 그 정도를 이 값이 잡아낸다
(similarity 기준 `page_precision_3`: 청크 300에서 0.610 → 1000에서 0.362).

---

## 기준 노트북과의 대조

`chunk_700`은 기준 노트북과 같은 조건(700/100)이다. 전처리 결과가 정확히 일치한다: **PDF 11개 / 236페이지 / 402청크.**

임베딩은 노트북의 OpenAI `text-embedding-3-small`에서 Gemini `gemini-embedding-001`로 바꿨다
(이 PC의 `.env`에 `OPENAI_API_KEY`가 없다). 그래서 수치는 다르지만 경향은 같고, 한국어에서는 Gemini 쪽이 더 좋다.

| | file_hit_1 | page_hit_1 | page_hit_3 | page_hit_5 | MRR |
|---|---|---|---|---|---|
| 노트북 Similarity (OpenAI) | 0.886 | 0.629 | 0.714 | 0.800 | 0.685 |
| 노트북 MMR (OpenAI) | 0.886 | 0.629 | 0.743 | 0.743 | 0.681 |
| **similarity** (Gemini) | 0.971 | 0.829 | 0.943 | 0.943 | 0.886 |
| **mmr** (Gemini) | 0.971 | 0.829 | 0.886 | 0.886 | 0.857 |
| **bm25** (Kiwi) | 0.971 | 0.886 | 0.914 | 0.943 | 0.907 |
| **hybrid** | 0.971 | 0.857 | 0.943 | 0.943 | 0.895 |

노트북에서 MMR이 Similarity보다 `page_hit_5`가 낮았던 것과 같은 방향이 재현된다.
BM25는 임베딩을 안 쓰므로 검색이 100배 이상 빠르다 (약 3ms vs 약 390ms).

---

## 인덱스 캐시

컬렉션명은 `exp_{sha1(문서경로 + glob + 청킹 + 임베딩모델)[:12]}`이다.
같은 청킹 조건이면 검색법만 바꿔 다시 돌려도 **재임베딩하지 않는다.**
저장 위치는 `./.index_cache`로, 다른 노트북들이 쓰는 `langchain_/chroma_db`와 분리돼 있다.

캐시가 있어도 저장된 청크 수가 지금 만든 청크 수와 다르면 신뢰하지 않고 다시 만든다.
강제로 다시 만들려면 `--rebuild-index` 또는 config의 `index.rebuild: true`.

---

## 트러블슈팅

**`ModuleNotFoundError: No module named 'langchain_chroma'`**
`python`이 Python313이 아닌 다른 인터프리터(대개 pyenv shim)를 탄 것이다.
`(Get-Command python).Source`로 확인하고, PATH가 다시 꼬였으면 `.\run.ps1`로 실행하면 된다.
위의 "실행 환경" 참고.

**`임베딩 쿼터 초과입니다 (모델: ...)`**
그 모델의 무료 티어 한도가 남지 않은 것이다. config의 `embedding.model`을 바꾸면 된다.
쓸 수 있는 임베딩 모델 확인:

```powershell
python -c "from rag.index import list_embedding_models; print(list_embedding_models())"
```

실제로 `gemini-embedding-2`는 쿼터가 소진돼 있었고 `gemini-embedding-001`로 바꿔서 돌렸다.
429는 지수 백오프로 8회까지 재시도하므로, 일시적인 속도 제한이면 알아서 넘어간다.
반대로 한도가 진짜 없으면 재시도를 다 쓰느라 몇 분 걸린 뒤에 실패한다.

**RAGAS가 느리다**
문항당 LLM을 여러 번 부른다. `evaluation.ragas.methods`로 검색법을 줄이거나,
`sample_size`로 문항을 줄이거나, `--retrieval-only`로 아예 건너뛰면 된다.
검색 지표(hit@k, MRR)만 볼 거라면 `--retrieval-only`가 LLM 호출 0회라 가장 빠르다.
