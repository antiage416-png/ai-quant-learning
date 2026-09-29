from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    try:
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(
            "https://quotes.toscrape.com/scroll",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        # 첫 명언이 표시될 때까지 기다립니다.
        quotes = page.locator("div.quote")
        quotes.first.wait_for(state="visible", timeout=10000)

        max_scrolls = 50
        print("시작 명언 수:", quotes.count())

        for attempt in range(1, max_scrolls + 1):
            before_count = quotes.count()

            # 페이지 맨 아래로 이동해 추가 로딩을 유도합니다.
            page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )

            try:
                # 이전보다 명언 개수가 늘어나는지 기다립니다.
                page.wait_for_function(
                    "previous => document.querySelectorAll('div.quote').length > previous",
                    arg=before_count,
                    timeout=10000,
                )

            except PlaywrightTimeoutError:
                print(
                    f"{attempt}번째 스크롤: "
                    "10초 안에 개수 증가를 확인하지 못해 종료합니다."
                )
                break

            after_count = quotes.count()
            print(
                f"{attempt}번째 스크롤: "
                f"{before_count}개 → {after_count}개"
            )

        else:
            # break 없이 정해진 반복을 모두 마쳤을 때 실행됩니다.
            print(f"최대 스크롤 {max_scrolls}회에 도달해 종료합니다.")

        print("종료 시 명언 수:", quotes.count())
    finally:
        browser.close()