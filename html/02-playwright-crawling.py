from playwright.sync_api import sync_playwright


URL = "https://www.motir.go.kr/kor/article/ATCL7d1e8393f?pageIndex=4"
TITLE_SELECTOR = ".ta-l"


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        try:
            page = browser.new_page()
            response = page.goto(URL, wait_until="domcontentloaded")
            if response is None or not response.ok:
                status = response.status if response else "응답 없음"
                raise RuntimeError(f"페이지 요청 실패: {status}")

            # title_locator = page.content()
            title_locator = page.locator("body")
            text = title_locator.inner_text()
            # 이거는 바디를 꺼낼때 이너 텍스트를 쓴다
            # title_locator = page.locator(TITLE_SELECTOR)
            # title_locator.first.wait_for(state="visible", timeout=15000)
            page.wait_for_timeout(3000)  # 화면 확인을 위한 3초 대기

            # for title in title_locator.all():
            #     text = title.text_content()
            #     if text and text.strip():
                    # print(text.strip())
            # print(title_locator)
            print(text)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
