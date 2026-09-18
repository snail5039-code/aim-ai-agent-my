review_generate_prompt = """
다음 보고서를 검토 가능한 형태로 정리해. 보고서만 출력해
작업: {query}\n\n
이전 결과:\n{review_result}\n\n
개선 지시:\n{improvement}\n\n
위 지시를 반영해서 보고서를 다시 작성해. 보고서만 출력해.
"""

review_initial_prompt = """
다음 보고서를 검토 가능한 형태로 정리해. 보고서만 출력해.
작업: {query}
"""
review_evaluate_prompt = """
너는 보고서 평가자다. 각 항목을 1~10점으로 평가하고 근거를 한 문장으로 작성하라.

평가 기준:
- accuracy: 사실과 근거가 정확하면 8점 이상
- completeness: 요청한 내용과 필요한 항목이 빠짐없이 들어갔으면 8점 이상
- realism: 제안과 계획이 현실적으로 실행 가능하면 8점 이상
- structure: 보고서 구조와 흐름이 읽기 좋으면 8점 이상

기준을 충족하지 못한 항목에는 7점 이하를 부여하라.
"""

review_optimize_prompt = """
너는 보고서 개선 편집자다. 평가 기준에 미달한 항목만 분석해
다음 생성 단계가 바로 적용할 수 있는 구체적인 수정 지시를 작성하라.
보고서를 직접 다시 쓰지 말고, 유지할 내용과 바꿀 내용을 명확히 구분하라.
평가에 없는 새로운 사실은 추가하지 마라.

작업 : {query}
현재 결과 : {review_result}
미달 항목 : {failed_items}
"""