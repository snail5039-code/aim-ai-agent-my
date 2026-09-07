"""RAGAS 생성 평가 (faithfulness, answer_relevancy).

10-rag-evaluation.ipynb 셀 34의 Gemini + instructor 조합을 재사용한다.
abatch_score는 동시 실행 수를 제어할 수 없어 35문항을 한꺼번에 던지면
Gemini 무료 티어에서 429가 난다. 그래서 ascore를 세마포어로 감싸 직접 돌린다.
"""

from __future__ import annotations

import asyncio


def _build_evaluator(config: dict):
    """RAGAS용 평가자 LLM과 임베딩을 만든다."""
    import instructor
    from google import genai
    from ragas.embeddings.base import embedding_factory
    from ragas.llms import InstructorLLM

    google_client = genai.Client()
    instructor_client = instructor.from_genai(google_client, use_async=True)

    evaluator_llm = InstructorLLM(
        client=instructor_client,
        model=config["generation"]["model"],
        provider="google",
    )
    evaluator_embeddings = embedding_factory(
        "google", model=config["embedding"]["model"], client=google_client
    )

    # 배치로 임베딩하면 단건과 차원이 달라지는 경우가 있어 하나씩 처리한다.
    async def embed_texts_individually(texts, **kwargs):
        return [await evaluator_embeddings.aembed_text(text, **kwargs) for text in texts]

    evaluator_embeddings.aembed_texts = embed_texts_individually

    return evaluator_llm, evaluator_embeddings


def _build_metrics(metric_names: list[str], evaluator_llm, evaluator_embeddings) -> dict:
    from ragas.metrics.collections import AnswerRelevancy, Faithfulness

    metrics = {}
    if "faithfulness" in metric_names:
        metrics["faithfulness"] = Faithfulness(llm=evaluator_llm)
    if "answer_relevancy" in metric_names:
        metrics["answer_relevancy"] = AnswerRelevancy(
            llm=evaluator_llm, embeddings=evaluator_embeddings
        )
    return metrics


def _metric_inputs(metric_name: str, record: dict) -> dict:
    """메트릭마다 요구하는 인자가 다르다."""
    if metric_name == "faithfulness":
        return {
            "user_input": record["question"],
            "response": record["response"],
            "retrieved_contexts": record["retrieved_contexts"],
        }
    if metric_name == "answer_relevancy":
        return {
            "user_input": record["question"],
            "response": record["response"],
        }
    raise ValueError(f"알 수 없는 RAGAS 메트릭: {metric_name}")


async def _score_all(metrics: dict, records: list[dict], max_concurrency: int) -> list[dict]:
    semaphore = asyncio.Semaphore(max_concurrency)
    done = 0
    total = len(records) * len(metrics)

    async def score_one(index: int, metric_name: str, metric, record: dict):
        nonlocal done
        async with semaphore:
            # 생성이 실패해 빈 답변이면 채점 자체가 의미 없다.
            if not record["response"].strip():
                value = None
            else:
                try:
                    result = await metric.ascore(**_metric_inputs(metric_name, record))
                    value = result.value
                except Exception as error:
                    print(f"    [{metric_name}] {index + 1}번 문항 채점 실패: {error}")
                    value = None
            done += 1
            if done % 10 == 0 or done == total:
                print(f"    RAGAS 채점 {done}/{total}")
            return index, metric_name, value

    tasks = [
        score_one(index, metric_name, metric, record)
        for index, record in enumerate(records)
        for metric_name, metric in metrics.items()
    ]
    results = await asyncio.gather(*tasks)

    rows = [
        {"question": record["question"], "response": record["response"]}
        for record in records
    ]
    for name in metrics:
        for row in rows:
            row[name] = None
    for index, metric_name, value in results:
        rows[index][metric_name] = value

    return rows


def run_ragas(records: list[dict], config: dict) -> list[dict]:
    """문항별 RAGAS 점수 리스트를 돌려준다."""
    ragas_config = config["evaluation"]["ragas"]
    metric_names = ragas_config["metrics"]

    evaluator_llm, evaluator_embeddings = _build_evaluator(config)
    metrics = _build_metrics(metric_names, evaluator_llm, evaluator_embeddings)
    if not metrics:
        return []

    return asyncio.run(
        _score_all(metrics, records, ragas_config.get("max_concurrency", 4))
    )


def summarize_ragas(rows: list[dict], metric_names: list[str]) -> dict:
    """None(채점 실패)은 평균에서 제외하고, 몇 개가 유효했는지도 같이 남긴다."""
    summary = {}
    for name in metric_names:
        values = [row[name] for row in rows if row.get(name) is not None]
        summary[name] = round(sum(values) / len(values), 4) if values else None
        summary[f"{name}_scored"] = len(values)
    return summary
