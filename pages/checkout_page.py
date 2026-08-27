"""結帳頁（填寫購買資料）。

momo 的結帳跟購物車是同一個網址，按下「結帳」只是在同一個 SPA 裡換步驟，
所以不能用網址判斷有沒有到結帳頁，要看畫面上出現了哪些只有結帳才有的東西。

頁面由上而下：訂購人資料 → 收件人資料 → 發票資料 → 付款方式 → 確認結帳

測試只確認「有到結帳頁、而且結帳鈕在」，不會真的送出訂單，
所以這個 Page Object 刻意不提供任何點擊 #orderSave 的方法。
"""

from playwright.sync_api import Page

class CheckoutPage:
    SUBMIT_ORDER = "#orderSave"      # 確認結帳（頁面最下方，測試只檢查存在，不點）
    BACK_TO_CART = "#goWebDetails"   # 返回查看商品明細（頁面最上方）
    SECTION_TITLES = ("訂購人資料", "收件人資料", "發票資料")

    def __init__(self, page: Page):
        self.page = page

    def wait_until_loaded(self):
        """等「確認結帳」按鈕出現，代表結帳頁整頁都渲染完了。"""
        self.page.locator(self.SUBMIT_ORDER).wait_for(state="visible")
        return self

    def scroll_to_submit_button(self):
        """捲到頁面最下方的「確認結帳」。

        結帳頁很長，進來時停在最上面的訂購人資料，使用者要往下滑才看得到結帳鈕。
        """
        self.page.locator(self.SUBMIT_ORDER).scroll_into_view_if_needed()
        return self

    def has_submit_button(self) -> bool:
        return self.page.locator(self.SUBMIT_ORDER).is_visible()

    def visible_sections(self) -> list:
        """畫面上出現了哪些結帳專屬的區塊標題。"""
        return [t for t in self.SECTION_TITLES if self.page.get_by_text(t).count() > 0]
