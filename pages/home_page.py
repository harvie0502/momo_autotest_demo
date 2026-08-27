"""momo 首頁的搜尋框。"""

from playwright.sync_api import Page

from pages.urls import HOME_URL, SEARCH_URL_PATTERN


class HomePage:
    SEARCH_INPUT = '[data-testid="header-search-input"]'
    SEARCH_BUTTON = '[data-testid="header-search-button"]'
    # 關鍵字建議清單。momo 沒給這一塊 testid，class 是編譯產生的，
    # 但 mu-z-dropdown 是語意化的層級名稱，比整串 class 穩。
    SUGGESTION_PANEL = "div[class*='mu-z-dropdown']"
    SUGGESTION_ITEM = "div[class*='mu-z-dropdown'] button"

    def __init__(self, page: Page):
        self.page = page

    def open(self):
        self.page.goto(HOME_URL, wait_until="domcontentloaded")
        self.page.locator(self.SEARCH_INPUT).wait_for(state="visible")
        return self

    def type_keyword(self, keyword: str):
        """逐字輸入關鍵字。

        用 press_sequentially 而不是 fill：fill 是一次性寫值，momo 的建議清單是
        監聽逐字輸入才會去打 API 的，用 fill 不會觸發。逐字輸入才是真實使用者行為。
        """
        search_input = self.page.locator(self.SEARCH_INPUT)
        search_input.click()
        search_input.press_sequentially(keyword, delay=120)
        return self

    def get_suggestions(self) -> list:
        """回傳關鍵字建議清單上的文字。

        每一筆建議底下還有「約 N 件商品」，只取第一行的關鍵字本體。
        """
        self.page.locator(self.SUGGESTION_PANEL).wait_for(state="visible")
        items = self.page.locator(self.SUGGESTION_ITEM)
        items.first.wait_for(state="visible")
        return [t.strip().splitlines()[0].strip() for t in items.all_inner_texts() if t.strip()]

    def submit_search(self):
        """送出搜尋。

        實測 momo 首頁按 Enter 不會送出搜尋，一定要點搜尋鈕。
        """
        self.page.locator(self.SEARCH_BUTTON).click()
        self.page.wait_for_url(SEARCH_URL_PATTERN, wait_until="domcontentloaded")
