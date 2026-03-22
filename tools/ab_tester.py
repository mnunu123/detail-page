# A/B 테스트 설계·판정 도구 — 통계적 유의성 검증 후 승리 변형안 판정
import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path


def calculate_sample_size(baseline_cvr: float = 0.03, mde: float = 0.05,
                           power: float = 0.8, alpha: float = 0.05) -> int:
    """최소 필요 샘플 사이즈 계산 (Two-proportion z-test)."""
    z_alpha = 1.96  # alpha=0.05 기준
    z_beta = 0.842  # power=0.80 기준
    p1 = baseline_cvr
    p2 = baseline_cvr * (1 + mde)
    pooled = (p1 + p2) / 2
    n = (z_alpha * math.sqrt(2 * pooled * (1 - pooled)) +
         z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / (p2 - p1) ** 2
    return math.ceil(n)


def z_test_two_proportions(n_a: int, conv_a: int, n_b: int, conv_b: int) -> dict:
    """두 비율 z-검정 수행."""
    if n_a == 0 or n_b == 0:
        return {"p_value": 1.0, "z_stat": 0.0, "error": "샘플 없음"}

    p_a = conv_a / n_a
    p_b = conv_b / n_b
    p_pool = (conv_a + conv_b) / (n_a + n_b)

    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
    if se == 0:
        return {"p_value": 1.0, "z_stat": 0.0}

    z = (p_b - p_a) / se

    # 표준 정규분포 p-value 근사 (양측 검정)
    # 간단한 근사: Abramowitz and Stegun
    def norm_cdf(x):
        t = 1 / (1 + 0.2316419 * abs(x))
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 +
               t * (-1.821255978 + t * 1.330274429))))
        pdf = math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
        cdf = 1 - pdf * poly
        return cdf if x >= 0 else 1 - cdf

    p_value = 2 * (1 - norm_cdf(abs(z)))
    lift = (p_b - p_a) / p_a if p_a > 0 else 0

    return {
        "cvr_a": round(p_a, 4),
        "cvr_b": round(p_b, 4),
        "z_stat": round(z, 3),
        "p_value": round(p_value, 4),
        "confidence": round((1 - p_value) * 100, 1),
        "lift_pct": round(lift * 100, 2),
    }


def setup_test(variant_a: str, variant_b: str, goal: str, output: str):
    """A/B 테스트 설정 파일 생성."""
    min_sample = calculate_sample_size()
    config = {
        "test_id": f"ab_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "created_at": datetime.now().isoformat(),
        "variants": {"A": variant_a, "B": variant_b},
        "goal": goal,
        "traffic_split": {"A": 0.5, "B": 0.5},
        "min_sample_per_variant": min_sample,
        "min_days": 7,
        "significance_threshold": 0.05,
        "min_cvr_lift_pct": 5.0,
        "ga4_event": "detail_page_variant",
        "status": "running",
    }
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    # A/B 분기 JS 스니펫 생성
    js_snippet = f"""
<!-- A/B 테스트 스니펫 (GA4 태깅) — test_id: {config['test_id']} -->
<script>
(function() {{
  var variant = document.cookie.match(/ab_variant=([AB])/);
  if (!variant) {{
    var v = Math.random() < 0.5 ? 'A' : 'B';
    document.cookie = 'ab_variant=' + v + ';path=/;max-age=2592000';
    variant = [null, v];
  }}
  window.AB_VARIANT = variant[1];
  // GA4 이벤트
  if (typeof gtag !== 'undefined') {{
    gtag('event', 'detail_page_variant', {{variant: variant[1]}});
  }}
  // 변형에 따른 페이지 교체
  if (variant[1] === 'B') {{
    window.location.href = window.location.pathname + '?v=B';
  }}
}})();
</script>
"""
    js_path = Path(output).parent / "ab_snippet.js"
    js_path.write_text(js_snippet, encoding="utf-8")
    print(f"테스트 설정 저장: {output}")
    print(f"GA4 태깅 스니펫: {js_path}")
    print(f"최소 샘플: 변형당 {min_sample}명")


def judge_test(report_path: str, threshold: float, output: str):
    """A/B 테스트 판정 — 통계적 유의성 검증."""
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    raw = report.get("raw_data", {})
    a_data = raw.get("A", {})
    b_data = raw.get("B", {})

    # 방문자 수 및 구매 수 추출
    n_a = a_data.get("page_view", {}).get("users", 0)
    n_b = b_data.get("page_view", {}).get("users", 0)
    conv_a = a_data.get("purchase", {}).get("count", 0)
    conv_b = b_data.get("purchase", {}).get("count", 0)

    days = report.get("period", {}).get("days", 0)
    stats = z_test_two_proportions(n_a, conv_a, n_b, conv_b)

    # 판정
    min_sample = 500
    min_days = 7
    min_lift = 5.0

    is_significant = (
        stats.get("p_value", 1.0) < threshold
        and n_a >= min_sample
        and n_b >= min_sample
        and days >= min_days
        and abs(stats.get("lift_pct", 0)) >= min_lift
    )

    if n_a < min_sample or n_b < min_sample or days < min_days:
        verdict = "INSUFFICIENT_DATA"
        next_action = "continue_test"
    elif not is_significant:
        verdict = "NO_WINNER"
        next_action = "restart_with_new_hypothesis"
    elif stats["cvr_b"] > stats["cvr_a"]:
        verdict = "B_WINS"
        next_action = "deploy_winner"
    else:
        verdict = "A_WINS"
        next_action = "deploy_winner"

    result = {
        "report_path": report_path,
        "judged_at": datetime.now().isoformat(),
        "samples": {"A": {"visitors": n_a, "conversions": conv_a},
                    "B": {"visitors": n_b, "conversions": conv_b}},
        "statistics": stats,
        "verdict": verdict,
        "next_action": next_action,
        "conditions_met": {
            "significance": stats.get("p_value", 1.0) < threshold,
            "sample_A": n_a >= min_sample,
            "sample_B": n_b >= min_sample,
            "min_days": days >= min_days,
            "min_lift": abs(stats.get("lift_pct", 0)) >= min_lift,
        },
    }

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*40}")
    print(f"판정 결과: {verdict}")
    print(f"다음 행동: {next_action}")
    print(f"p-value: {stats.get('p_value')}, 신뢰도: {stats.get('confidence')}%")
    print(f"CVR 향상: {stats.get('lift_pct')}%")
    print(f"{'='*40}")
    print(f"저장: {output}")


def main():
    parser = argparse.ArgumentParser(description="A/B 테스트 도구")
    parser.add_argument("--mode", required=True, choices=["setup", "judge"])
    parser.add_argument("--variant-a")
    parser.add_argument("--variant-b")
    parser.add_argument("--goal", default="purchase")
    parser.add_argument("--report")
    parser.add_argument("--threshold", type=float, default=0.05)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.mode == "setup":
        setup_test(args.variant_a, args.variant_b, args.goal, args.output)
    elif args.mode == "judge":
        judge_test(args.report, args.threshold, args.output)


if __name__ == "__main__":
    main()
