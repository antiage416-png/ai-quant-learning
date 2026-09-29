from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    try:
        page = browser.new_page()

        page.goto(
            "https://quotes.toscrape.com/js/",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        # 첫 번째 명언 본문을 찾을 조건을 만듭니다.
        first_quote = page.locator("div.quote span.text").first

        # 그 요소가 화면에 표시 가능한 상태가 될 때까지 기다립니다.
        # 10000밀리초는 최대 10초입니다.
        first_quote.wait_for(state="visible", timeout=10000)

        # 기다림이 끝난 뒤 본문을 읽습니다.
        print("현재 주소:", page.url)
        print("첫 명언:", first_quote.inner_text())


        # 이동 전 첫 명언을 문자열로 보관합니다.
        before_text = first_quote.inner_text()

        # Next 링크에 적힌 목적지 주소를 가져옵니다.
        next_link = page.locator("li.next a")
        href = next_link.get_attribute("href")

        if href is None:
            raise ValueError("Next 링크에 href가 없습니다.")

        # 상대주소를 전체 주소로 바꿉니다.
        next_url = urljoin(page.url, href)

        # 브라우저에서 Next 링크를 클릭합니다.
        next_link.click()

        # 목적지 주소로 이동했는지 확인합니다.
        page.wait_for_url(next_url, timeout=30000)

        # 새 페이지의 첫 명언이 보일 때까지 기다립니다.
        next_quote = page.locator("div.quote span.text").first
        next_quote.wait_for(state="visible", timeout=10000)

        after_text = next_quote.inner_text()

        print("이동 후 주소:", page.url)
        print("이동 후 첫 명언:", after_text)
        print("첫 명언이 달라졌는가:", before_text != after_text)

    finally:
        browser.close()