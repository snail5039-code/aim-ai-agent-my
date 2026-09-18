planning_create_plan_prompt = """
다음 요청에 대한 분석 보고서를 작성하려고 한다. 
필요한 분석 작업을 3~5개로 나눠줘.\n\n요청: <query>{query}</query>
"""

planning_worker_prompt = """
전체 요청을 고려하여 담당 항목을 구체적으로 분석해줘.\n\n
전체 요청: <query>{query}</query>\n
담당 항목: <title>{title}</title>\n
분석 내용: <description>{description}</description>
"""

planning_merge_prompt = """
다음 요청과 분석 결과를 바탕으로 하나의 보고서를 작성해줘.\n\n
요청: <query>{query}</query>\n\n{all_results}
개선 피드백:{planning_feedback}
작성 규칙:
- 개선 피드백이 비어 있으면 분석 결과를 바탕으로 초안 보고서를 작성해라.
- 개선 피드백이 있으면 그 피드백을 참고해서 보고서를 다시 작성해라.
- 분석 결과에 없는 내용을 사실처럼 추가하지 말고, 필요한 경우 가정이라고 표시해라.
"""

planning_reflect_prompt = """
너는 기획 보고서 검토자다.
사용자 요청, 작업 목록, worker 작성 결과, 최종 보고서를 보고 기획 결과가 충분한지 판단해라.

검토 기준:
- 사용자 요청의 조건과 목적이 반영되었는가?
- worker 작성 결과가 최종 보고서에 빠짐없이 반영되었는가?
- 실행 계획이 구체적이고 현실적인가?
- 보고서 구조가 자연스럽고 중복이 적은가?

다음 경로는 아래 중 하나로 판단해라.

- pass: 최종 보고서가 충분하므로 종료해도 된다.
- revise: 최종 보고서에 누락, 중복, 추상적인 표현, 현실성 부족이 있어 다시 병합/수정해야 한다.

planning_feedback에는 왜 그 경로를 선택했는지와 다음 병합 단계에서 무엇을 보완해야 하는지 구체적으로 작성해라.
"""