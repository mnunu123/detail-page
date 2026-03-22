---
name: quality-check
description: 모든 에이전트의 최근 출력물 품질을 한 번에 채점하고 개선이 필요한 에이전트를 파악한다
---

전체 에이전트 품질 점검을 실행합니다.

## 실행 순서

@prompter 에이전트를 호출하여 다음을 수행합니다:

1. `outputs/` 내 최근 결과물 수집
   - `outputs/structured_data/product_info.json`
   - `outputs/structured_data/research_report.json`
   - `outputs/copy/copy_v1.json`
   - `outputs/reports/ab_report.json`

2. 각 에이전트 출력물 채점 (10점 만점)

3. 7점 미만 에이전트 목록 + 문제점 분석

4. 개선 프롬프트 초안 작성 (사용자 검토 후 적용)

## 결과 형식
```
📊 에이전트 품질 리포트
------------------------
✅ 정보수집:  8.5/10
✅ 리서치:    8.0/10
⚠️ 카피라이팅: 6.5/10 → 개선 필요
✅ 디자인:    9.0/10
✅ 분석:      7.5/10
------------------------
💡 개선 권장: 카피라이팅 에이전트
   문제: 헤드라인 임팩트 부족, 숫자 근거 미흡
   개선안: prompts/v2/copywriter.md 생성 완료
```
