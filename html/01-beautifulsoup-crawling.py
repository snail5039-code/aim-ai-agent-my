import csv
import json
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


URL = "https://news.google.com/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFp4WkRNU0FtdHZLQUFQAQ?hl=ko&gl=KR&ceid=KR%3Ako"
ARTICLE_SELECTOR = "a.gPFEn"


def main():
    # HTML 요청과 파싱
    response = requests.get(URL, timeout=15)
    response.raise_for_status()
    print("상태 코드:", response.status_code)

    soup = BeautifulSoup(response.text, "html.parser")
    print(soup.title)

    # CSS 선택자로 기사 찾기
    articles = soup.select(ARTICLE_SELECTOR)
    print("기사 수:", len(articles))
    if not articles:
        raise ValueError("기사를 찾지 못했습니다. 응답 HTML과 선택자를 확인하세요.")

    # 제목과 절대 주소를 딕셔너리로 정리하기
    base_url = urljoin(response.url, "/")
    news_rows = []

    for article in articles:
        title = article.get_text(strip=True)
        href = article.get("href")
        if not title or not href:
            continue

        absolute_url = urljoin(base_url, href)
        news_rows.append({"title": title, "url": absolute_url})

        print(f"제목: {title}")
        print(f"링크: {absolute_url}")
        print("-" * 50)

    print("수집 개수:", len(news_rows))

    # 현재 작업 폴더에 CSV와 JSON 저장하기
    output_dir = Path.cwd() / "crawling_output"
    output_dir.mkdir(exist_ok=True)
    csv_path = output_dir / "google_news.csv"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["title", "url"])
        writer.writeheader()
        writer.writerows(news_rows)

    json_path = output_dir / "google_news.json"
    json_path.write_text(
        json.dumps(news_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(csv_path.resolve())
    print(json_path.resolve())


if __name__ == "__main__":
    main()
