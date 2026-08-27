"""商品頁。

從搜尋結果點進來，網址會從 /goods/GoodsDetail.jsp?i_code=NNN 正規化成
/product/NNN，所以商品編號可以直接從網址取得，用來確認點到的是同一件商品。

購買相關的按鈕都有 aria-label，是這頁最穩定的定位方式：
    button[aria-label="直接購買"]     立即購買
    button[aria-label="放入購物車"]   加入購物車
    button[aria-label="售完補貨中"]   缺貨（此時前兩顆不存在）
"""

import re

from playwright.sync_api import (
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from pages.helpers import choose_first_spec
from pages.urls import CART_URL_PATTERN

PRODUCT_CODE_IN_URL = re.compile(r"/product/(\d+)")
BUY_TIMEOUT_MS = 20_000


class ProductPage:
    BUY_NOW_BUTTON = "button[aria-label='直接購買']"
    ADD_TO_CART_BUTTON = "button[aria-label='放入購物車']"
    SOLD_OUT_BUTTON = "button[aria-label='售完補貨中']"
    MESSAGE_DIALOG = "div.whitespace-pre-line"   # momo 擋下操作時跳的提示視窗內文
    # 規格有兩種 UI。組合商品用下拉選單，本商品的沒有 name 屬性
    # （數量是 goodsQuantity、頁面下方推薦商品是 goodsSpec，都要避開）；
    # 一般規格商品用按鈕方塊，momo 有給 data-testid。
    SPEC_DROPDOWN = "select:not([name])"
    SPEC_BUTTON = "button[data-testid^='spec-button-']"

    def __init__(self, page: Page):
        self.page = page

    def wait_until_loaded(self):
        """等購買區塊出現（不論可買還是缺貨）才算商品頁載入完成。"""
        self.page.locator(
            f"{self.BUY_NOW_BUTTON}, {self.ADD_TO_CART_BUTTON}, {self.SOLD_OUT_BUTTON}"
        ).first.wait_for(state="visible")
        return self

    def product_code(self) -> str:
        found = PRODUCT_CODE_IN_URL.search(self.page.url)
        if not found:
            raise AssertionError(f"目前網址不是商品頁，取不到商品編號：{self.page.url}")
        return found.group(1)

    def is_in_stock(self) -> bool:
        return self.page.locator(self.SOLD_OUT_BUTTON).count() == 0

    def buy_now(self):
        """點「直接購買」。

        momo 的「直接購買」不是直接跳結帳，而是把商品加進購物車後帶你到購物車頁，
        要再按一次「結帳」才會進到填寫購買資料的步驟。
        """
        choose_first_spec(self.page.locator(self.SPEC_DROPDOWN),
                          self.page.locator(self.SPEC_BUTTON))
        self.page.locator(self.BUY_NOW_BUTTON).click()
        try:
            self.page.wait_for_url(
                CART_URL_PATTERN, wait_until="domcontentloaded", timeout=BUY_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            # 沒進購物車時 momo 會跳一個小視窗說明原因，把它讀出來，
            # 免得只看到一個看不懂的等待逾時。
            raise AssertionError(
                f"按了「直接購買」卻沒有進到購物車。"
                f"momo 的提示：{self._dialog_message() or '（沒有提示）'}\n"
                "常見原因：這件商品有多種規格 / 組合要先選，或是還沒開賣的限時搶購。"
            )

    def _dialog_message(self) -> str:
        """讀 momo 擋下操作時跳的提示；讀不到就回空字串。

        跟 LoginPage._error_message() 同樣的道理：這個方法只在 buy_now() 已經
        失敗之後被呼叫，任務是「讓錯誤訊息更好懂」。頁面如果已經導走或關掉，
        這串會自己拋錯，把上面那句寫得清清楚楚的 AssertionError 換成一個
        看不懂的 TargetClosedError——用診斷程式碼蓋掉診斷結果。所以一律吞掉。
        """
        try:
            dialog = self.page.locator(self.MESSAGE_DIALOG)
            return dialog.first.inner_text().strip() if dialog.count() else ""
        except PlaywrightError:
            return ""
