"""購物車頁（cart.momoshop.com.tw）。

進入方式是點 header 的購物車，不是直接開網址——使用者不會自己打網址。

畫面結構：
    button.v-delete-all-products    「全部刪除」（標題列右側）
    button.v-product-delete-button  「移除」（每一列商品各一顆）
    span.product-number             商品編號
    #btnDetailCheckout              「結帳(N)」

「購物車裡有幾件商品」直接數「移除」鈕的數量：每一列商品必定有一顆。
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.checkout_page import CheckoutPage
from pages.helpers import click_until

# 判定「購物車是空的」要等多久。空車時這段時間一定會等好等滿，設太長會拖慢
# 每一次的後置清空；購物車列表是一支 API 回來就渲染，10 秒綽綽有餘。
EMPTY_CART_TIMEOUT_MS = 10_000


class CartPage:
    PRODUCT_ROW_DELETE = "button.v-product-delete-button"   # 每列商品的「移除」
    PRODUCT_NUMBER = "span.product-number"
    DELETE_ALL_BUTTON = "button.v-delete-all-products"
    CHECKOUT_BUTTON = "#btnDetailCheckout"

    def __init__(self, page: Page):
        self.page = page

    def wait_until_has_items(self):
        """等購物車的商品列渲染出來。

        購物車頁的內容是進頁之後才用 JS 拉回來的，導頁一結束就讀會讀到空的。
        """
        self.page.locator(self.PRODUCT_ROW_DELETE).first.wait_for(state="visible")
        return self

    def has_items(self, timeout_ms: int = EMPTY_CART_TIMEOUT_MS) -> bool:
        """購物車裡有沒有商品。

        給清單一段時間渲染，等不到就當作是空的——清空購物車時用得到，
        不然空車會卡在等待上。
        """
        try:
            self.page.locator(self.PRODUCT_ROW_DELETE).first.wait_for(
                state="visible", timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            return False

    def product_numbers(self) -> list:
        return [t.strip() for t in self.page.locator(self.PRODUCT_NUMBER).all_inner_texts()]

    def checkout(self):
        """按「結帳」進入填寫購買資料的步驟。

        用結帳頁的元素當作「這一步真的換過去了」的訊號，所以這裡會參照
        CheckoutPage 的選擇器——購物車的結帳鈕本來就是通往結帳頁的入口。
        """
        self._click_and_confirm(self.CHECKOUT_BUTTON, CheckoutPage.BACK_TO_CART,
                                state="visible")

    def delete_all(self):
        """按「全部刪除」，等到商品列全部消失。"""
        self._click_and_confirm(self.DELETE_ALL_BUTTON, self.PRODUCT_ROW_DELETE,
                                state="detached")

    def _click_and_confirm(self, trigger: str, expected: str, state: str):
        """點擊，並在跳出來的瀏覽器確認視窗按「確定」。

        購物車的「全部刪除」和「結帳」按下去會跳原生的 confirm 視窗
        （例如「確定刪除"momo訂單"全部 3 個商品？」）。那不是頁面上的元素，
        而 Playwright 預設會自動「取消」所有原生對話框——所以不掛這個 handler
        的話，點下去等於按了取消，畫面上什麼都不會發生也不會報錯。

        handler 只在這一次操作期間掛著，做完就移除，避免誤按到其他地方的視窗。
        """
        def accept(dialog):
            dialog.accept()

        self.page.on("dialog", accept)
        try:
            click_until(self.page, trigger, expected, state=state)
        finally:
            self.page.remove_listener("dialog", accept)
