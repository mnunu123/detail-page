# Gemini Pro API 호출 도구 — 분석, 평가, 콘텐츠 생성 작업 담당
import argparse
import json
import os
import sys
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    print("필수 패키지 없음: pip install google-generativeai")
    sys.exit(1)


def get_model():
    """Gemini Pro 모델 초기화."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("오류: GEMINI_API_KEY 환경변수 없음")
        sys.exit(1)
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-pro-exp")


def analyze_reviews(product_info: dict) -> dict:
    """제품 리뷰 인사이트 분석."""
    model = get_model()
    reviews = product_info.get("raw_reviews", [])
    prompt = f"""
다음 제품 리뷰들을 분석하여 JSON 형식으로 답하세요.

제품명: {product_info.get('product_name', '')}
리뷰: {json.dumps(reviews, ensure_ascii=False)[:3000]}

출력 형식:
{{
  "positive_drivers": ["구매 결정 이유 Top5"],
  "objections": ["불안 요소 Top3"],
  "purchase_triggers": ["구매 트리거 Top5"],
  "sentiment_summary": "전반적 감성 요약"
}}
JSON만 출력하세요.
"""
    response = model.generate_content(prompt)
    text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def evaluate_agent_output(agent: str, output_data: dict, criteria: dict) -> dict:
    """에이전트 출력물 품질 채점 (프롬프팅 에이전트용)."""
    model = get_model()
    prompt = f"""
당신은 AI 에이전트 출력 품질 평가 전문가입니다.

평가 대상 에이전트: {agent}
평가 기준:
{json.dumps(criteria, ensure_ascii=False, indent=2)}

에이전트 출력물:
{json.dumps(output_data, ensure_ascii=False, indent=2)[:4000]}

각 항목을 10점 만점으로 채점하고 JSON으로만 답하세요:
{{
  "scores": {{"항목명": 점수}},
  "total": 평균점수,
  "strengths": ["잘된 점"],
  "weaknesses": ["개선 필요 점"],
  "improvement_suggestions": ["구체적 개선 방향"]
}}
"""
    response = model.generate_content(prompt)
    text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text, "error": "파싱 실패"}


def main():
    parser = argparse.ArgumentParser(description="Gemini 분석 도구")
    parser.add_argument("--mode", required=True, choices=["review_analysis", "evaluate"])
    parser.add_argument("--input", help="입력 JSON 파일 경로")
    parser.add_argument("--agent", help="평가 대상 에이전트명 (evaluate 모드)")
    parser.add_argument("--output-file", help="평가할 결과물 파일 (evaluate 모드)")
    parser.add_argument("--criteria", help="평가 기준 JSON 파일 (evaluate 모드)")
    parser.add_argument("--score-output", help="채점 결과 저장 경로")
    parser.add_argument("--output", help="결과 저장 경로")
    args = parser.parse_args()

    if args.mode == "review_analysis":
        with open(args.input, encoding="utf-8") as f:
            product_info = json.load(f)
        result = analyze_reviews(product_info)
        out_path = args.output or "outputs/structured_data/review_insights.json"

    elif args.mode == "evaluate":
        with open(args.output_file, encoding="utf-8") as f:
            output_data = json.load(f)
        criteria = {}
        if args.criteria and Path(args.criteria).exists():
            with open(args.criteria, encoding="utf-8") as f:
                criteria = json.load(f)
        result = evaluate_agent_output(args.agent, output_data, criteria)
        out_path = args.score_output or "outputs/reports/quality_scores.json"

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"완료: {out_path}")


if __name__ == "__main__":
    main()
