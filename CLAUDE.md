# 상세페이지 에이전트 팀 — 프로젝트 가이드

## 시스템 개요
이 프로젝트는 이커머스 상세페이지를 자동으로 생성·분석·개선하는 **멀티 에이전트 시스템**입니다.
Claude Code의 공식 서브에이전트(`.claude/agents/`)와 스킬(`.claude/skills/`)을 사용합니다.

---

## 에이전트 팀 구성

| 에이전트 | 파일 | 역할 | 호출 시점 |
|---------|------|------|---------|
| 정보수집 | `.claude/agents/info-collector.md` | URL/제품명 → 구조화 JSON | 파이프라인 시작 |
| 리서치 | `.claude/agents/researcher.md` | 경쟁사·키워드·리뷰 분석 | 정보수집 완료 후 |
| 카피라이팅 | `.claude/agents/copywriter.md` | A/B/C 카피 변형안 생성 | 리서치 완료 후 |
| 디자인 | `.claude/agents/designer.md` | Pencil MCP 상세페이지 제작 | 카피 완료 후 |
| 분석 | `.claude/agents/analyzer.md` | GA4 분석 + A/B 자동 교체 | 배포 7일 후 |
| 프롬프팅 | `.claude/agents/prompter.md` | 에이전트 품질 평가·개선 | 필요 시 |

---

## 스킬 (슬래시 커맨드)

| 커맨드 | 기능 |
|--------|------|
| `/create-page` | 전체 생성 파이프라인 실행 |
| `/analyze-and-improve` | GA4 분석 + 자동 교체 사이클 |
| `/quality-check` | 전체 에이전트 품질 점검 |

---

## 데이터 흐름

```
사용자 입력 (URL 또는 제품 정보)
    ↓
outputs/structured_data/product_info.json    ← info-collector
    ↓
outputs/structured_data/research_report.json ← researcher
    ↓
outputs/copy/copy_v1.json                    ← copywriter
    ↓
outputs/designs/page_v1.pen                  ← designer
    ↓ (배포 후 7일)
outputs/reports/ab_report.json               ← analyzer
    ↓ (통계적 유의성 확인)
자동 교체 또는 새 가설 → 사이클 재시작
```

---

## 도구 레이어 (tools/)

| 파일 | 역할 |
|------|------|
| `tools/scraper.py` | 웹 스크래핑 (Playwright) |
| `tools/keyword_tool.py` | 네이버 쇼핑 키워드 수집 |
| `tools/gemini_analyzer.py` | Gemini API 호출 (분석, 평가) |
| `tools/ga4_client.py` | GA4 API 데이터 수집 |
| `tools/ab_tester.py` | A/B 테스트 설계·판정 |
| `tools/deployer.py` | 승리 변형안 배포 |
| `tools/save_copy.py` | 카피 결과 저장 |
| `tools/save_design.py` | 디자인 메타데이터 저장 |
| `tools/normalizer.py` | 데이터 정규화 |
| `tools/prompt_tester.py` | 프롬프트 A/B 테스트 |
| `tools/update_agent.py` | 에이전트 프롬프트 업데이트 |

---

## 환경 설정
```bash
cp .env.example .env
# .env에 API 키 입력 후 진행
pip install -r requirements.txt
```

필수 API 키:
- `GEMINI_API_KEY` — Gemini Pro (분석, 콘텐츠 평가)
- `GA4_PROPERTY_ID` — GA4 속성 ID
- `GA4_SERVICE_ACCOUNT_JSON` — GA4 서비스 계정 JSON 경로
- `ANTHROPIC_API_KEY` — Claude (에이전트 실행)

---

## 코딩 규칙

| 상황 | 행동 |
|------|------|
| 에이전트가 Python 도구를 실행할 때 | `tools/` 폴더 내 스크립트만 사용 |
| 새 도구가 필요할 때 | `tools/`에 추가 후 CLAUDE.md 표 업데이트 |
| 에이전트 프롬프트를 수정할 때 | 프롬프팅 에이전트를 통해 테스트 후 적용 |
| 출력 파일 저장 위치 | 반드시 `outputs/` 내 지정 경로에 저장 |
| A/B 테스트 교체 실행 전 | 반드시 사용자 확인 받음 |

---

## 배포 환경
- **자체 서버**: Python FastAPI 서버 + 쿠키 기반 A/B 라우팅
- **크몽**: 완성된 HTML 파일 업로드 + GA4 태깅
- **A/B 방식**: 쿠키 기반 서버사이드 분기 (50:50)
