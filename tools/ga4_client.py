# GA4 API 클라이언트 — A/B 테스트 데이터 수집 및 리포트 생성
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Filter,
        FilterExpression,
        Metric,
        RunReportRequest,
    )
    from google.oauth2 import service_account
except ImportError:
    print("필수 패키지 없음: pip install google-analytics-data google-auth")
    sys.exit(1)


def get_client() -> BetaAnalyticsDataClient:
    """GA4 클라이언트 초기화."""
    sa_path = os.getenv("GA4_SERVICE_ACCOUNT_JSON")
    if not sa_path or not Path(sa_path).exists():
        print("오류: GA4_SERVICE_ACCOUNT_JSON 환경변수 또는 파일 없음")
        sys.exit(1)
    credentials = service_account.Credentials.from_service_account_file(
        sa_path,
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
    return BetaAnalyticsDataClient(credentials=credentials)


def fetch_ab_report(property_id: str, test_id: str, days: int = 14) -> dict:
    """A/B 테스트 변형별 전환 데이터 수집."""
    client = get_client()
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[
            Dimension(name="customEvent:detail_page_variant"),
            Dimension(name="eventName"),
        ],
        metrics=[
            Metric(name="eventCount"),
            Metric(name="totalUsers"),
            Metric(name="purchaseRevenue"),
        ],
    )
    response = client.run_report(request)

    results = {"A": {}, "B": {}}
    for row in response.rows:
        variant = row.dimension_values[0].value  # A 또는 B
        event = row.dimension_values[1].value
        count = int(row.metric_values[0].value)
        users = int(row.metric_values[1].value)
        revenue = float(row.metric_values[2].value)

        if variant in results:
            results[variant][event] = {"count": count, "users": users, "revenue": revenue}

    return {
        "test_id": test_id,
        "property_id": property_id,
        "period": {"start": start_date, "end": end_date, "days": days},
        "raw_data": results,
        "fetched_at": datetime.now().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="GA4 리포트 수집")
    parser.add_argument("--mode", required=True, choices=["report"])
    parser.add_argument("--property-id", default=os.getenv("GA4_PROPERTY_ID"))
    parser.add_argument("--test-id", required=True)
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if not args.property_id:
        print("오류: --property-id 또는 GA4_PROPERTY_ID 필요")
        sys.exit(1)

    result = fetch_ab_report(args.property_id, args.test_id, args.days)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"GA4 리포트 저장 완료: {args.output}")


if __name__ == "__main__":
    main()
