# 웹 스크래핑 도구 — Playwright 기반 제품 정보 수집
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    from bs4 import BeautifulSoup
except ImportError:
    print("필수 패키지 없음: pip install playwright beautifulsoup4 && playwright install chromium")
    sys.exit(1)


def scrape_product_page(url: str) -> dict:
    """제품 상세페이지에서 정보를 수집한다."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ))
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            html = page.content()
        finally:
            browser.close()

    soup = BeautifulSoup(html, "html.parser")

    # 텍스트 전체 추출 (에이전트가 분석)
    text_content = soup.get_text(separator="\n", strip=True)

    # 이미지 URL 수집
    images = [
        img.get("src") or img.get("data-src", "")
        for img in soup.find_all("img")
        if img.get("src") or img.get("data-src")
    ]

    # 메타 정보
    title = soup.title.string if soup.title else ""
    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        description = meta_desc.get("content", "")

    return {
        "url": url,
        "title": title,
        "meta_description": description,
        "text_content": text_content[:10000],  # 10,000자 제한
        "images": images[:20],
        "collected_at": datetime.now().isoformat(),
    }


def scrape_competitors(product_name: str) -> list[dict]:
    """경쟁사 상품 검색 및 기본 정보 수집 (네이버 쇼핑)."""
    search_url = f"https://search.shopping.naver.com/search/all?query={product_name}"
    try:
        result = scrape_product_page(search_url)
        return [{"source": "naver_shopping", "query": product_name, "raw": result}]
    except Exception as e:
        return [{"error": str(e), "query": product_name}]


def main():
    parser = argparse.ArgumentParser(description="제품 정보 스크래퍼")
    parser.add_argument("--url", help="스크래핑할 URL")
    parser.add_argument("--mode", default="product", choices=["product", "competitor"])
    parser.add_argument("--product", help="경쟁사 검색용 제품명")
    parser.add_argument("--output", required=True, help="결과 저장 경로")
    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    if args.mode == "product" and args.url:
        result = scrape_product_page(args.url)
    elif args.mode == "competitor" and args.product:
        result = scrape_competitors(args.product)
    else:
        print("오류: --url 또는 --product 필요")
        sys.exit(1)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {args.output}")


if __name__ == "__main__":
    main()
