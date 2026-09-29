from playwright.sync_api import sync_playwright

# Playwright를 시작하고, 작업이 끝나면 정리합니다.
with sync_playwright() as p:
    # 화면에 창을 띄우지 않는 방식으로 Chromium을 실행합니다.
    browser = p.chromium.launch(headless=True)

    try:
        # 브라우저에 새 페이지를 만듭니다.
        page = browser.new_page()

        # JavaScript 연습 페이지로 이동합니다.
        # timeout 단위는 밀리초이므로 30000은 30초입니다.
        page.goto(
            "https://quotes.toscrape.com/js/",
            timeout=30000,
        )

        # 브라우저가 읽은 문서 제목을 출력합니다.
        print("페이지 제목:", page.title())

    finally:
        # 중간에 오류가 나더라도 브라우저를 닫습니다.
        browser.close()