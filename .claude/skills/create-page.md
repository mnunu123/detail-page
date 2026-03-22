---
name: create-page
description: 제품 URL이나 정보를 입력하면 정보수집→리서치→카피라이팅→디자인 전체 파이프라인을 순서대로 실행하여 완성된 상세페이지를 만든다
---

상세페이지 전체 생성 파이프라인을 시작합니다.

## 실행 순서

다음 에이전트들을 순서대로 실행하세요:

1. **정보수집** (@info-collector)
   - 사용자가 입력한 URL 또는 제품 정보 수집
   - `outputs/structured_data/product_info.json` 생성 확인

2. **리서치** (@researcher)
   - `product_info.json` 기반으로 경쟁사·키워드·리뷰 분석
   - `outputs/structured_data/research_report.json` 생성 확인

3. **카피라이팅** (@copywriter)
   - 두 결과물 기반으로 A/B/C 3가지 카피 변형안 생성
   - `outputs/copy/copy_v1.json` 생성 확인

4. **디자인** (@designer)
   - 카피 결과 + 브랜드 정보로 Pencil MCP 상세페이지 디자인
   - `outputs/designs/` 결과물 확인

각 단계 완료 후 다음 단계로 진행하고, 완료 시 "상세페이지 생성 완료" 요약을 제공하세요.

## 사용자 입력 처리
- URL이 주어진 경우: 정보수집 에이전트에 URL 전달
- 텍스트로 주어진 경우: `outputs/structured_data/product_info.json`에 직접 작성 후 리서치 단계 시작
