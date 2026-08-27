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
        """畫面上「看得到」的結帳專屬區塊標題。

        一定要驗可見，不能只驗 DOM 裡有沒有。結帳與購物車是同一份 SPA 文件
        （見檔案開頭），這些區塊在還停在購物車步驟時就可能已經掛在 DOM 上了，
        只用 count() 的話，「有沒有真的換到結帳步驟」這件事等於沒驗到。
        """
        return [title for title in self.SECTION_TITLES if self._is_text_visible(title)]

    def _is_text_visible(self, text: str) -> bool:
        """畫面上有沒有任何一個看得見的元素帶著這段文字。

        get_by_text 是子字串比對，同一段文字會連祖先節點一起命中，
        所以是「任何一個可見就算數」而不是只看第一個。
        """
        matches = self.page.get_by_text(text)
        return any(matches.nth(i).is_visible() for i in range(matches.count()))
