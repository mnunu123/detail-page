# 상세페이지 에이전트 팀 (detail-page v1)

이커머스 상세페이지를 **생성 → 배포 → GA4 데이터로 A/B 분석 → 승리안 자동 교체**까지
순환시키는 멀티 에이전트 시스템입니다. Claude Code의 서브에이전트(`.claude/agents/`)와
슬래시 커맨드 스킬(`.claude/skills/`)로 구성됩니다.

> 같은 "상세페이지 자동 생성" 계열로 [`landing-page-generator`](https://github.com/mnunu123/landing-page-generator)(5-에이전트, Gemini 이미지 생성 중심 v2)가 있습니다.
> 이 저장소(v1)는 **생성 이후 단계 — 실제 배포 후 GA4 데이터를 근거로 자동 개선하는 루프**에 초점이 맞춰진 초기 버전입니다.

## 에이전트 팀 구성

| 에이전트 | 역할 | 호출 시점 |
| --- | --- | --- |
| `info-collector` | URL/제품명 → 구조화 JSON | 파이프라인 시작 |
| `researcher` | 경쟁사·키워드·리뷰 분석 | 정보수집 완료 후 |
| `copywriter` | A/B/C 카피 변형안 생성 | 리서치 완료 후 |
| `designer` | Pencil MCP로 상세페이지 제작 | 카피 완료 후 |
| `analyzer` | GA4 분석 + A/B 자동 교체 판정 | 배포 7일 후 |
| `prompter` | 에이전트 프롬프트 품질 평가·개선 | 필요 시 |

## 슬래시 커맨드

| 커맨드 | 기능 |
| --- | --- |
| `/create-page` | 전체 생성 파이프라인 실행 |
| `/analyze-and-improve` | GA4 분석 + 자동 교체 사이클 |
| `/quality-check` | 전체 에이전트 품질 점검 |

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

상태 전이는 `state/schema.py`의 `PipelineStatus`(idle → info_collecting → researching →
copywriting → designing → deployed → analyzing → improving → completed/failed)로 관리됩니다.

## 배포 방식

- **자체 서버**: Python FastAPI + 쿠키 기반 A/B 라우팅(50:50)
- **크몽**: 완성된 HTML 업로드 + GA4 태깅

## 현재 구현 상태

`tools/`에는 아래 4개가 구현되어 있습니다.

| 파일 | 역할 |
| --- | --- |
| `tools/scraper.py` | 웹 스크래핑 (Playwright) |
| `tools/gemini_analyzer.py` | Gemini API 호출 (분석, 콘텐츠 평가) |
| `tools/ga4_client.py` | GA4 API 데이터 수집 |
| `tools/ab_tester.py` | A/B 테스트 설계·판정 |

`CLAUDE.md`에 설계된 나머지 도구(`keyword_tool.py`, `deployer.py`, `save_copy.py`,
`save_design.py`, `normalizer.py`, `prompt_tester.py`, `update_agent.py`)와 `outputs/` 산출물은
아직 이 저장소에 커밋되지 않은 **다음 단계**입니다.

## 환경 설정

```bash
cp .env.example .env
# .env에 아래 키 입력
pip install -r requirements.txt
```

필수 API 키: `GEMINI_API_KEY`, `GA4_PROPERTY_ID`, `GA4_SERVICE_ACCOUNT_JSON`, `ANTHROPIC_API_KEY`

## 코딩 규칙 (CLAUDE.md 발췌)

- 에이전트가 Python 도구를 실행할 때는 `tools/` 폴더 내 스크립트만 사용
- 새 도구가 필요하면 `tools/`에 추가 후 `CLAUDE.md` 표를 업데이트
- 에이전트 프롬프트 수정 시 `prompter` 에이전트로 테스트 후 적용
- 출력 파일은 반드시 `outputs/` 내 지정 경로에 저장
- A/B 테스트 교체 실행 전 반드시 사용자 확인
