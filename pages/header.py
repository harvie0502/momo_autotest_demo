"""momo 主站的 header（首頁與搜尋結果頁共用）。

購物車入口是 a#TopCart，文字帶著目前的件數，例如「購物車( 1 )」。
首頁和搜尋結果頁的空白排版略有差異（「購物車 (0)」/「購物車( 0 )」），
所以用正規表達式取數字，不要比對整串文字。

注意兩件事：
1. 這個數字是「件數」（同一件商品買 4 個會顯示 4），不是購物車裡的品項列數。
2. 首頁剛載入時是伺服器給的預設值 0，約 0.5 秒後才被 API 更新成真實數字。
   所以測試一律比較「加入前後的差值」，不去斷言某個絕對值。
"""

import re

from playwright.sync_api import Page, expect

from pages.urls import CART_URL_PATTERN

class Header:
    CART_ENTRY = "#TopCart"

    def __init__(self, page: Page):
        self.page = page

    def cart_count(self) -> int:
        """header 上顯示的購物車件數。"""
        text = self.page.locator(self.CART_ENTRY).inner_text()
        found = re.search(r"\d+", text)
        return int(found.group()) if found else 0

    def wait_for_cart_count(self, expected: int):
        """等 header 的購物車件數變成預期值。

        加入購物車是非同步的，這個數字就是使用者眼中「加成功了」的訊號，
        等它更新再往下走，比等一個固定秒數可靠。
        """
        expect(self.page.locator(self.CART_ENTRY)).to_have_text(
            re.compile(rf"購物車\s*\(\s*{expected}\s*\)")
        )

    def open_cart(self):
        """點 header 的購物車，進到購物車頁。

        #TopCart 本身就是個連結，點下去一定會導頁（購物車空的也一樣），
        所以只要等網址落在購物車頁就好。
        """
        self.page.locator(self.CART_ENTRY).click()
        self.page.wait_for_url(CART_URL_PATTERN, wait_until="domcontentloaded")
